"""
Auto-Router: Prompt-Length-Based Model Selection Engine
Sovereign On-Premise Agentic AI Workbench (SIH PS 26117 - MRPL)

Routes user prompts to the most suitable local model based on prompt length:
  - Short   (≤100 chars)   -> smollm2:1.7b     (quick general replies)
  - Medium  (≤500 chars)   -> qwen3.5:9b        (coding / calculations)
  - Long    (≤1500 chars)  -> qwen3.5:9b        (vision / detailed tasks)
  - XLong   (>1500 chars)  -> deepseek-r1:8b    (deep reasoning / analysis)
"""

from __future__ import annotations

import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import aiohttp
from pydantic import BaseModel, Field

os.environ.setdefault("OPENAI_API_KEY", "sovereign-airgap-local-key")

log = logging.getLogger(__name__)

# Default model definitions aligned with SIH PS 26117 requirements
DEFAULT_CODING_MODEL = "qwen3.5:9b"
DEFAULT_VISION_MODEL = "qwen3.5:9b"
DEFAULT_REASONING_MODEL = "deepseek-r1:8b"
DEFAULT_GENERAL_MODEL = "smollm2:1.7b"
DEFAULT_ROUTER_MODEL_ID = "routellm-auto-router"

# Task category constants
CATEGORY_CODING = "CODING_CALCULATION"
CATEGORY_VISION = "VISION_PID_DRAWING"
CATEGORY_REASONING = "REASONING_APPROVAL_NOTE"
CATEGORY_GENERAL = "GENERAL_INQUIRY"

# ----- Length thresholds (characters) -----
LENGTH_SHORT = 100    # ≤100 chars  -> GENERAL
LENGTH_MEDIUM = 500   # ≤500 chars  -> CODING
LENGTH_LONG = 1500    # ≤1500 chars -> VISION
#                      >1500 chars  -> REASONING


def classify_by_length(prompt: str) -> Tuple[str, float, str]:
    """
    Classify a prompt into one of the 4 model categories based purely on
    the character length of the prompt text.

    Returns: (category, score, human_readable_reason)
    """
    length = len((prompt or "").strip())

    if length <= LENGTH_SHORT:
        score = round(length / LENGTH_SHORT * 0.25, 3)  # 0.00 - 0.25
        return (
            CATEGORY_GENERAL,
            score,
            f"Short prompt ({length} chars <= {LENGTH_SHORT}) -> General model",
        )

    if length <= LENGTH_MEDIUM:
        score = round(0.25 + (length - LENGTH_SHORT) / (LENGTH_MEDIUM - LENGTH_SHORT) * 0.25, 3)  # 0.25 - 0.50
        return (
            CATEGORY_CODING,
            score,
            f"Medium prompt ({length} chars <= {LENGTH_MEDIUM}) -> Coding model",
        )

    if length <= LENGTH_LONG:
        score = round(0.50 + (length - LENGTH_MEDIUM) / (LENGTH_LONG - LENGTH_MEDIUM) * 0.25, 3)  # 0.50 - 0.75
        return (
            CATEGORY_VISION,
            score,
            f"Long prompt ({length} chars <= {LENGTH_LONG}) -> Vision model",
        )

    # >1500 chars
    score = min(0.99, round(0.75 + (length - LENGTH_LONG) / 3000 * 0.24, 3))  # 0.75 - 0.99
    return (
        CATEGORY_REASONING,
        score,
        f"Very long prompt ({length} chars > {LENGTH_LONG}) -> Reasoning model",
    )


def resolve_best_available_model(
    target_model_id: str,
    available_model_ids: List[str],
    category: str,
) -> str:
    """
    Resolves the desired target model against models actually present in the system,
    falling back gracefully to installed alternatives without breaking.
    """
    if not available_model_ids:
        return target_model_id

    # 1. Exact match
    if target_model_id in available_model_ids:
        return target_model_id

    # 2. Normalized match (strip tag or prefix)
    target_base = target_model_id.split(":")[0]
    for m in available_model_ids:
        if m == target_model_id or m.startswith(f"{target_base}:"):
            return m

    # 3. Category-specific intelligent fallbacks
    fallback_map = {
        CATEGORY_CODING: ["qwen2.5-coder", "coder", "qwen3.5:9b", "qwen3.5", "deepseek-coder", "deepseek-r1"],
        CATEGORY_VISION: ["qwen2-vl", "vl", "vision", "llava", "qwen3.5:9b", "qwen3.5"],
        CATEGORY_REASONING: ["deepseek-r1:8b", "deepseek-r1", "r1", "llama3.1", "llama-3", "qwen3.5:9b", "qwen3.5"],
        CATEGORY_GENERAL: ["qwen3.5:9b", "llama3.1", "smollm2:1.7b", "smollm2", "smollm", "qwen3.5:0.8b", "qwen3.5", "mistral"],
    }
    for preferred in fallback_map.get(category, []):
        for m in available_model_ids:
            if preferred in m.lower():
                return m

    # 4. Non-router fallback (pick any non-router model)
    non_router_models = [m for m in available_model_ids if m != DEFAULT_ROUTER_MODEL_ID and "router" not in m]
    if non_router_models:
        return non_router_models[0]

    return target_model_id


class SovereignRouteLLMController:
    """
    Controller that routes prompts to the optimal local model
    based on prompt character length.
    """

    def __init__(
        self,
        coding_model: str = DEFAULT_CODING_MODEL,
        vision_model: str = DEFAULT_VISION_MODEL,
        reasoning_model: str = DEFAULT_REASONING_MODEL,
        general_model: str = DEFAULT_GENERAL_MODEL,
        threshold: float = 0.50,
    ):
        self.coding_model = coding_model
        self.vision_model = vision_model
        self.reasoning_model = reasoning_model
        self.general_model = general_model
        self.threshold = threshold

        self._category_to_model = {
            CATEGORY_GENERAL: self.general_model,
            CATEGORY_CODING: self.coding_model,
            CATEGORY_VISION: self.vision_model,
            CATEGORY_REASONING: self.reasoning_model,
        }

    def route_request(
        self,
        prompt: str,
        files: Optional[List[Dict[str, Any]]] = None,
        available_models: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Executes routing decision based on prompt length and returns metadata.
        """
        category, score, reason = classify_by_length(prompt)

        target_model = self._category_to_model[category]

        # Resolve against active models
        resolved_model = resolve_best_available_model(
            target_model, available_models or [], category
        )

        badge_text = f"Auto-routed to {resolved_model} ({reason})"
        return {
            "selected_model_id": resolved_model,
            "target_model_id": target_model,
            "category": category,
            "score": score,
            "reason": reason,
            "router": "length-based-auto-router",
            "threshold": self.threshold,
            "badge_text": badge_text,
        }

    route = route_request


# Global singleton instance
router_controller = SovereignRouteLLMController()


async def route_chat_payload(
    form_data: dict,
    metadata: dict,
    available_models: Optional[List[str]] = None,
) -> Tuple[dict, dict, Dict[str, Any]]:
    """
    Middleware helper: inspects form_data, determines task routing by prompt length,
    and updates payload metadata.
    """
    # Extract last user message content
    messages = form_data.get("messages", [])
    last_user_prompt = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content")
            if isinstance(content, str):
                last_user_prompt = content
            elif isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        parts.append(part.get("text", ""))
                last_user_prompt = "\n".join(parts)
            break

    # Extract files
    files = metadata.get("files", []) or form_data.get("files", [])

    routing_result = router_controller.route_request(
        prompt=last_user_prompt,
        files=files,
        available_models=available_models,
    )

    selected_model_id = routing_result["selected_model_id"]

    # Rewrite model in payload
    form_data["model"] = selected_model_id
    metadata["selected_model_id"] = selected_model_id
    metadata["routing_info"] = routing_result

    return form_data, metadata, routing_result


# ==============================================================================
# Open-WebUI Pipe Function Protocol Implementation
# ==============================================================================
class Pipe:
    """
    Open-WebUI Pipe Function for Dynamic Length-Based Model Auto-Selection.
    Compatible with Open-WebUI's Functions / Pipe system.
    """

    class Valves(BaseModel):
        OLLAMA_BASE_URL: str = Field(
            default="http://localhost:11434",
            description="Base URL for local Ollama instance",
        )
        CODING_MODEL: str = Field(
            default=DEFAULT_CODING_MODEL,
            description="Model for medium-length coding & calculation prompts",
        )
        VISION_MODEL: str = Field(
            default=DEFAULT_VISION_MODEL,
            description="Model for long detailed prompts & vision tasks",
        )
        REASONING_MODEL: str = Field(
            default=DEFAULT_REASONING_MODEL,
            description="Model for very long prompts requiring deep reasoning",
        )
        GENERAL_MODEL: str = Field(
            default=DEFAULT_GENERAL_MODEL,
            description="Model for short general conversational queries",
        )
        ROUTING_THRESHOLD: float = Field(
            default=0.50,
            description="(Unused — kept for config compatibility)",
        )
        ENABLE_ROUTING_BADGE: bool = Field(
            default=True,
            description="Emit status badge in chat explaining routing selection",
        )

    def __init__(self):
        self.type = "pipe"
        self.id = DEFAULT_ROUTER_MODEL_ID
        self.name = "Auto"
        self.valves = self.Valves()

    def get_controller(self) -> SovereignRouteLLMController:
        return SovereignRouteLLMController(
            coding_model=self.valves.CODING_MODEL,
            vision_model=self.valves.VISION_MODEL,
            reasoning_model=self.valves.REASONING_MODEL,
            general_model=self.valves.GENERAL_MODEL,
            threshold=self.valves.ROUTING_THRESHOLD,
        )

    async def pipe(
        self,
        body: dict,
        __event_emitter__: Optional[Any] = None,
        __user__: Optional[dict] = None,
        __request__: Optional[Any] = None,
        __metadata__: Optional[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Classifies prompt by length, emits visual status badge, and streams completion.
        """
        controller = self.get_controller()

        # Extract prompt
        messages = body.get("messages", [])
        prompt = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                c = m.get("content", "")
                if isinstance(c, str):
                    prompt = c
                elif isinstance(c, list):
                    prompt = "\n".join([item.get("text", "") for item in c if isinstance(item, dict)])
                break

        files = (body.get("metadata") or {}).get("files", [])

        # Fetch available models if request is provided
        available_model_ids = []
        if __request__ and hasattr(__request__, "app") and hasattr(__request__.app, "state"):
            models_dict = getattr(__request__.app.state, "MODELS", {})
            available_model_ids = list(models_dict.keys()) if isinstance(models_dict, dict) else []

        decision = controller.route_request(
            prompt=prompt,
            files=files,
            available_models=available_model_ids,
        )

        selected_model_id = decision["selected_model_id"]
        category = decision["category"]
        score = decision["score"]
        reason = decision["reason"]

        log.info(
            f"[AutoRouter] Routed query to {selected_model_id} (Category: {category}, Score: {score}, Reason: {reason})"
        )

        # 1. Emit visual status badge if event emitter is available (no emoji)
        if self.valves.ENABLE_ROUTING_BADGE and __event_emitter__:
            badge_text = f"Auto-routed to {selected_model_id} ({reason})"
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": badge_text,
                        "done": True,
                    },
                }
            )

        # 2. Yield selected_model_id header for Open-WebUI frontend
        yield f'{{"selected_model_id": "{selected_model_id}"}}\n\n'

        # 3. Stream from Ollama endpoint or OpenAI-compatible endpoint
        payload = {**body, "model": selected_model_id}

        ollama_url = f"{self.valves.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
        async with aiohttp.ClientSession() as session:
            try:
                # Convert payload to Ollama format
                ollama_payload = {
                    "model": selected_model_id,
                    "messages": payload.get("messages", []),
                    "stream": True,
                }
                if "options" in payload:
                    ollama_payload["options"] = payload["options"]

                async with session.post(ollama_url, json=ollama_payload) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        yield f"Error from Ollama ({resp.status}): {err_text}"
                        return

                    async for line in resp.content:
                        if line:
                            decoded = line.decode("utf-8", errors="ignore").strip()
                            if decoded:
                                yield f"{decoded}\n"

            except Exception as exc:
                log.error(f"Error streaming from Ollama: {exc}")
                yield f"Error in auto-router pipe execution: {exc}"

