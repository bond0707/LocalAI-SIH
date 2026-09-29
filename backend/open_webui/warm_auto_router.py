"""
OpenWebUI Warm-First Model Router Pipe
Sovereign On-Premise Agentic AI Workbench (SIH PS 26117 - MRPL)

Routes user prompts to specialized local Ollama models (General, Coding, Reasoning)
using single-tier intent classification with VRAM-affinity ("warm-first") model selection.

Prevents GPU memory thrashing: if a domain-eligible model is already loaded in VRAM
(per GET /api/ps), it is selected immediately; otherwise the first preferred candidate
is used (cold start).
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import os
import re
from typing import AsyncGenerator, Awaitable, Callable, Optional

import httpx
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain Category Constants
# ---------------------------------------------------------------------------
CATEGORY_REASONING = "Reasoning"
CATEGORY_CODING = "Coding"
CATEGORY_GENERAL = "General"

# ---------------------------------------------------------------------------
# Intent Classification Regex Patterns
# ---------------------------------------------------------------------------

# Coding signals
_CODE_FENCE = re.compile(r"```")

_LANG_NAMES = re.compile(
    r"\b(python|typescript|javascript|js|ts|golang|go|rust|c\+\+|cpp|csharp|c#|sql|"
    r"dockerfile|docker|html|css|bash|sh|powershell|ps1|java|scala|kotlin|ruby|php|"
    r"yaml|yml|json|terraform|hcl|graphql)\b",
    re.IGNORECASE,
)

_CODE_SYNTAX = re.compile(
    r"(?:^|\s)("
    r"def\s+\w+|"
    r"function\s+\w+|"
    r"class\s+\w+|"
    r"import\s+\w+|"
    r"from\s+\w+\s+import|"
    r"const\s+\w+|"
    r"let\s+\w+|"
    r"var\s+\w+|"
    r"#include\s*<|"
    r"SELECT\s+.+\s+FROM|"
    r"INSERT\s+INTO|"
    r"UPDATE\s+\w+\s+SET|"
    r"git\s+(?:commit|push|pull|clone|checkout|status|merge|branch|rebase|stash)|"
    r"npm\s+(?:install|run|build|test)|"
    r"pip\s+(?:install|uninstall|freeze)"
    r")",
    re.IGNORECASE,
)

_ERROR_DIAG = re.compile(
    r"\b("
    r"debug|debugger|breakpoint|"
    r"stack\s*trace|traceback|"
    r"syntax\s*error|typeerror|valueerror|nameerror|indexerror|keyerror|attributeerror|"
    r"runtime\s*error|exception|"
    r"segmentation\s*fault|sigsegv|"
    r"npm\s+err|pip\s+error|"
    r"bug\s+fix|patch\s+fix|"
    r"linting|eslint|pylint"
    r")\b",
    re.IGNORECASE,
)

# Reasoning signals
_REASONING_KW = re.compile(
    r"\b("
    r"prove|proves|proving|proof|"
    r"theorem|lemma|corollary|"
    r"derive|derivation|deriving|"
    r"solve|step\s*by\s*step|puzzle|riddle|"
    r"reasoning|reason|logic|logical|"
    r"find\s+x|math|mathematics|arithmetic|"
    r"algebra|algebraic|"
    r"calculus|differential|integral|derivative|"
    r"probability|statistics|statistical|"
    r"matrix|matrices|eigenvalue|eigenvector|"
    r"trigonometry|geometry|"
    r"equation|inequality"
    r")\b",
    re.IGNORECASE,
)

_ARITHMETIC = re.compile(
    r"(?:^|\s|\()(\d+(?:\.\d+)?\s*[\+\-\*\/\^%]\s*\d+(?:\.\d+)?)(?:\s|\)|$)"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_prompt_text(messages: list[dict]) -> str:
    """Extract text from last user message (supports str and multimodal list)."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "\n".join(
                    part.get("text", "")
                    for part in content
                    if isinstance(part, dict) and part.get("type") == "text"
                )
    return ""


def _sanitize_messages(messages: list[dict]) -> list[dict]:
    """
    Sanitize OpenWebUI conversation history for Ollama /api/chat.
    Strips internal OpenWebUI metadata (function_call, statusHistory, UI state)
    that causes Ollama's parser to throw HTTP 400 errors.
    """
    clean = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "user")
        if role not in ("system", "user", "assistant"):
            role = "user"

        content = msg.get("content", "")
        if isinstance(content, list):
            text_parts = [
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            content = "\n".join(filter(None, text_parts))
        elif not isinstance(content, str):
            content = str(content or "")

        # Skip messages that have no text and are only internal tool call artifacts
        if not content.strip() and not msg.get("images"):
            continue

        clean_msg = {"role": role, "content": content}
        if "images" in msg and isinstance(msg["images"], list):
            clean_msg["images"] = msg["images"]

        clean.append(clean_msg)

    return clean


def _normalize_model_id(raw: str) -> tuple[str, str]:
    """
    Normalize an Ollama model identifier to (base_name, tag).

    Handles:
      - "deepseek-r1:8b"                                 -> ("deepseek-r1", "8b")
      - "registry.ollama.ai/library/deepseek-r1:8b"      -> ("deepseek-r1", "8b")
      - "qwen3.5"                                         -> ("qwen3.5", "latest")
    """
    cleaned = raw.strip().lower().split("/")[-1]
    if ":" in cleaned:
        base, tag = cleaned.split(":", 1)
        return base, tag
    return cleaned, "latest"


def _is_warm_match(candidate: str, warm_models: list[str]) -> bool:
    """
    Check if candidate matches any model currently loaded in Ollama VRAM.

    Matching rules:
      1. Exact string match (normalized, case-insensitive)
      2. Normalized base-name + tag match:
         - If candidate specifies a tag (e.g. 'qwen3.5:9b'), the warm model must
           match BOTH base and tag.
         - NEVER match different parameter sizes (e.g. 'qwen3.5:9b' != 'qwen3.5:4b' != 'qwen3.5:0.8b').
         - If candidate omitted tag (e.g. 'deepseek-r1'), matches if warm model is ':latest' or untagged.
    """
    c_normalized = candidate.strip().lower().split("/")[-1]
    c_base, c_tag = _normalize_model_id(candidate)
    c_has_tag = ":" in candidate.strip().split("/")[-1]

    for warm in warm_models:
        w_normalized = warm.strip().lower().split("/")[-1]

        # Rule 1: exact normalized
        if c_normalized == w_normalized:
            return True

        # Rule 2: base + tag match
        w_base, w_tag = _normalize_model_id(warm)
        w_has_tag = ":" in warm.strip().split("/")[-1]

        if c_base != w_base:
            continue

        if c_has_tag:
            if c_tag == w_tag:
                return True
        else:
            if not w_has_tag or w_tag == "latest":
                return True

    return False


# ---------------------------------------------------------------------------
# Pipe Class
# ---------------------------------------------------------------------------

class Pipe:
    """
    OpenWebUI Pipe Function: Warm-First Model Auto-Router.

    Lifecycle:
      - classify_intent()            : keyword/regex domain classification
      - get_warm_models()            : poll Ollama GET /api/ps (2s timeout)
      - select_model_from_candidates(): warm-first candidate resolution
      - pipe()                       : emit status events, stream from /api/chat
    """

    class Valves(BaseModel):
        OLLAMA_BASE_URL: str = Field(
            default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            description=(
                "Base URL for local Ollama daemon. "
                "Use 'http://host.docker.internal:11434' when running inside Docker."
            ),
        )
        GENERAL_MODELS: str = Field(
            default="smollm2:1.7b, qwen3.5:0.8b",
            description="Ordered comma-separated candidates for general conversation",
        )
        CODER_MODELS: str = Field(
            default="qwen3.5:9b, qwen3.5:4b",
            description="Ordered comma-separated candidates for coding/scripting tasks",
        )
        REASONING_MODELS: str = Field(
            default="deepseek-r1:8b, qwen3.5:9b",
            description="Ordered comma-separated candidates for reasoning/math proofs",
        )
        TIMEOUT_SECONDS: float = Field(
            default=180.0,
            description="Inference streaming timeout (seconds)",
        )
        PS_TIMEOUT_SECONDS: float = Field(
            default=2.0,
            description="Timeout for GET /api/ps VRAM query (seconds). Keep low.",
        )

    def __init__(self):
        self.type = "pipe"
        self.id = "warm_auto_router"
        self.name = "Auto"
        self.valves = self.Valves()

    # ------------------------------------------------------------------
    # 1. Intent Classification
    # ------------------------------------------------------------------

    def classify_intent(self, prompt: str) -> str:
        """
        Classify prompt into one of three domains.

        Precedence (first match wins):
          1. Coding   - code fences, language names, syntax tokens, error diagnostics
          2. Reasoning - math/logic keywords, raw arithmetic expressions
          3. General  - fallback
        """
        if not prompt or not prompt.strip():
            return CATEGORY_GENERAL

        if (
            _CODE_FENCE.search(prompt)
            or _ERROR_DIAG.search(prompt)
            or _CODE_SYNTAX.search(prompt)
            or _LANG_NAMES.search(prompt)
        ):
            return CATEGORY_CODING

        if _REASONING_KW.search(prompt) or _ARITHMETIC.search(prompt):
            return CATEGORY_REASONING

        return CATEGORY_GENERAL

    # ------------------------------------------------------------------
    # 2. VRAM State Query
    # ------------------------------------------------------------------

    async def get_warm_models(self) -> list[str]:
        """
        Query Ollama GET /api/ps to retrieve models currently in GPU/RAM.

        Returns list of model name strings.
        Returns [] on any network failure or timeout (graceful degradation).
        """
        url = f"{self.valves.OLLAMA_BASE_URL.rstrip('/')}/api/ps"
        try:
            async with httpx.AsyncClient(timeout=self.valves.PS_TIMEOUT_SECONDS) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                return [
                    m.get("name") or m.get("model", "")
                    for m in data.get("models", [])
                    if isinstance(m, dict) and (m.get("name") or m.get("model"))
                ]
        except Exception as exc:
            log.warning(f"[WarmAutoRouter] /api/ps query failed (cold-start fallback): {exc}")
            return []

    # ------------------------------------------------------------------
    # 3. Warm-First Model Selection
    # ------------------------------------------------------------------

    def select_model_from_candidates(
        self,
        category: str,
        warm_models: list[str],
    ) -> tuple[str, bool]:
        """
        Resolve optimal model for domain against live VRAM state.

        Returns (selected_model_name, is_warm).
        is_warm=True  -> model already in VRAM, no cold-start penalty.
        is_warm=False -> cold start, first preferred candidate selected.
        """
        candidate_valve = {
            CATEGORY_REASONING: self.valves.REASONING_MODELS,
            CATEGORY_CODING: self.valves.CODER_MODELS,
            CATEGORY_GENERAL: self.valves.GENERAL_MODELS,
        }.get(category, self.valves.GENERAL_MODELS)

        candidates = [c.strip() for c in candidate_valve.split(",") if c.strip()]
        if not candidates:
            log.warning(f"[WarmAutoRouter] No candidates for '{category}'. Using smollm2:1.7b.")
            return ("smollm2:1.7b", False)

        for cand in candidates:
            if _is_warm_match(cand, warm_models):
                log.info(f"[WarmAutoRouter] WARM hit: '{cand}' for domain '{category}'")
                return (cand, True)

        log.info(f"[WarmAutoRouter] COLD start: '{candidates[0]}' for domain '{category}'")
        return (candidates[0], False)

    async def select_model(self, category: str) -> tuple[str, bool]:
        """Fetch live VRAM state then run warm-first selection."""
        warm_models = await self.get_warm_models()
        return self.select_model_from_candidates(category, warm_models)

    # ------------------------------------------------------------------
    # 4. OpenWebUI Pipe Entry Point
    # ------------------------------------------------------------------

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        OpenWebUI Pipe handler.

        Flow:
          1. Extract last user message.
          2. Classify intent -> category.
          3. Query /api/ps; select warm model or cold fallback.
          4. Emit pre-inference status: "Class: <Cat> -> <Model> [Warm/Cold]" (done=False).
          5. POST /api/chat, stream via httpx.
          6. On first content chunk emit: "Generating with <Model>" (done=True).
          7. Yield each content token string.
          8. Handle ConnectError, TimeoutException, HTTP errors, malformed JSON.
        """
        prompt = _extract_prompt_text(body.get("messages", []))
        category = self.classify_intent(prompt)
        selected_model, is_warm = await self.select_model(category)
        warm_label = "Warm" if is_warm else "Cold"

        log.info(
            f"[WarmAutoRouter] '{category}' -> '{selected_model}' [{warm_label}] "
            f"(user={(__user__ or {}).get('name', 'anon')})"
        )

        async def _emit(description: str, done: bool) -> None:
            if __event_emitter__:
                try:
                    await __event_emitter__(
                        {"type": "status", "data": {"description": description, "done": done}}
                    )
                except Exception as e:
                    log.warning(f"[WarmAutoRouter] Event emitter error: {e}")

        await _emit(f"Class: {category} -> {selected_model} [{warm_label}]", done=False)

        chat_url = f"{self.valves.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
        payload: dict = {
            "model": selected_model,
            "messages": _sanitize_messages(body.get("messages", [])),
            "stream": True,
        }
        if "options" in body and isinstance(body["options"], dict):
            safe_options = {
                k: v for k, v in body["options"].items()
                if isinstance(v, (int, float, str, bool, list)) and k != "format"
            }
            if safe_options:
                payload["options"] = safe_options

        first_chunk_done = False

        try:
            async with httpx.AsyncClient(timeout=self.valves.TIMEOUT_SECONDS) as client:
                async with client.stream("POST", chat_url, json=payload) as resp:

                    if resp.status_code != 200:
                        raw = await resp.aread()
                        err_msg = f"Ollama HTTP {resp.status_code}: {raw.decode(errors='ignore')}"
                        log.error(f"[WarmAutoRouter] {err_msg}")
                        await _emit(f"Failed with {selected_model}", done=True)
                        yield f"[Router Error] {err_msg}"
                        return

                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            log.warning(f"[WarmAutoRouter] Malformed JSON chunk skipped: {line[:120]}")
                            continue

                        content = chunk.get("message", {}).get("content", "")

                        if content:
                            if not first_chunk_done:
                                await _emit(f"Generating with {selected_model}", done=True)
                                first_chunk_done = True
                            yield content

                        if chunk.get("done", False):
                            break

        except httpx.ConnectError as exc:
            msg = f"Cannot connect to Ollama at '{self.valves.OLLAMA_BASE_URL}': {exc}"
            log.error(f"[WarmAutoRouter] {msg}")
            await _emit("Ollama connection failed", done=True)
            yield f"\n[Router Error] {msg}"

        except httpx.TimeoutException as exc:
            msg = f"Inference timed out after {self.valves.TIMEOUT_SECONDS}s: {exc}"
            log.error(f"[WarmAutoRouter] {msg}")
            await _emit("Generation timed out", done=True)
            yield f"\n[Router Error] {msg}"

        except Exception as exc:
            log.exception(f"[WarmAutoRouter] Unexpected streaming error: {exc}")
            await _emit(f"Unexpected error: {exc}", done=True)
            yield f"\n[Router Error] {exc}"
