"""
Unit tests for OpenWebUI Warm-First Model Router Pipe.

Run:
  backend\\.venv\\Scripts\\python.exe -m pytest backend/test/test_warm_auto_router.py -v
"""

from __future__ import annotations

import sys
import os

# Allow import from project root without install
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from open_webui.warm_auto_router import (
    Pipe,
    CATEGORY_CODING,
    CATEGORY_REASONING,
    CATEGORY_GENERAL,
    _normalize_model_id,
    _is_warm_match,
    _extract_prompt_text,
)


@pytest.fixture
def pipe():
    return Pipe()


# ---------------------------------------------------------------------------
# normalize_model_id
# ---------------------------------------------------------------------------

class TestNormalizeModelId:
    def test_simple_tag(self):
        assert _normalize_model_id("deepseek-r1:8b") == ("deepseek-r1", "8b")

    def test_no_tag(self):
        assert _normalize_model_id("qwen3.5") == ("qwen3.5", "latest")

    def test_registry_prefix(self):
        assert _normalize_model_id("registry.ollama.ai/library/deepseek-r1:8b") == ("deepseek-r1", "8b")

    def test_uppercase_normalized(self):
        base, tag = _normalize_model_id("DeepSeek-R1:8B")
        assert base == "deepseek-r1"
        assert tag == "8b"


# ---------------------------------------------------------------------------
# _is_warm_match
# ---------------------------------------------------------------------------

class TestIsWarmMatch:
    def test_exact_match(self):
        assert _is_warm_match("deepseek-r1:8b", ["deepseek-r1:8b"]) is True

    def test_registry_prefix_warm(self):
        assert _is_warm_match(
            "deepseek-r1:8b",
            ["registry.ollama.ai/library/deepseek-r1:8b"]
        ) is True

    def test_no_match(self):
        assert _is_warm_match("deepseek-r1:8b", ["smollm2:1.7b", "qwen3.5:4b"]) is False

    def test_different_tag_no_match(self):
        # candidate tag differs (9b vs 4b) - must NOT false positive as warm
        assert _is_warm_match("qwen3.5:9b", ["qwen3.5:4b"]) is False

    def test_empty_warm_list(self):
        assert _is_warm_match("smollm2:1.7b", []) is False


# ---------------------------------------------------------------------------
# _extract_prompt_text
# ---------------------------------------------------------------------------

class TestExtractPromptText:
    def test_string_content(self):
        body = {"messages": [{"role": "user", "content": "Hello MRPL"}]}
        assert _extract_prompt_text(body["messages"]) == "Hello MRPL"

    def test_multimodal_content(self):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Inspect this P&ID"},
                    {"type": "image_url", "image_url": "data:image/png;base64,..."},
                ],
            }
        ]
        assert _extract_prompt_text(messages) == "Inspect this P&ID"

    def test_last_user_message_wins(self):
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "Response"},
            {"role": "user", "content": "Second message"},
        ]
        assert _extract_prompt_text(messages) == "Second message"

    def test_no_user_message(self):
        messages = [{"role": "system", "content": "You are an AI."}]
        assert _extract_prompt_text(messages) == ""


# ---------------------------------------------------------------------------
# Intent Classification
# ---------------------------------------------------------------------------

class TestClassifyIntent:
    def test_code_fence(self, pipe):
        assert pipe.classify_intent("```python\nprint('hello')\n```") == CATEGORY_CODING

    def test_language_name(self, pipe):
        assert pipe.classify_intent("Write a Rust program to parse YAML") == CATEGORY_CODING

    def test_def_syntax(self, pipe):
        assert pipe.classify_intent("def calculate_reynolds(v, d):") == CATEGORY_CODING

    def test_sql_syntax(self, pipe):
        assert pipe.classify_intent("SELECT name FROM employees WHERE dept='ops'") == CATEGORY_CODING

    def test_error_trace(self, pipe):
        assert pipe.classify_intent("I'm getting a TypeError: NoneType not subscriptable") == CATEGORY_CODING

    def test_git_command(self, pipe):
        assert pipe.classify_intent("How do I git merge with no fast forward?") == CATEGORY_CODING

    def test_prove_theorem(self, pipe):
        assert pipe.classify_intent("Prove that sqrt(2) is irrational") == CATEGORY_REASONING

    def test_arithmetic(self, pipe):
        assert pipe.classify_intent("What is 125 * 45 / 3?") == CATEGORY_REASONING

    def test_algebra(self, pipe):
        assert pipe.classify_intent("Solve for x: 3x + 15 = 45") == CATEGORY_REASONING

    def test_integral(self, pipe):
        assert pipe.classify_intent("Calculate the integral of e^x from 0 to infinity") == CATEGORY_REASONING

    def test_general_approval_note(self, pipe):
        assert pipe.classify_intent("Draft an approval note for safety valve replacement") == CATEGORY_GENERAL

    def test_general_mrpl_summary(self, pipe):
        assert pipe.classify_intent("Tell me about MRPL refinery operations") == CATEGORY_GENERAL

    def test_empty_prompt(self, pipe):
        assert pipe.classify_intent("") == CATEGORY_GENERAL

    def test_whitespace_only(self, pipe):
        assert pipe.classify_intent("   ") == CATEGORY_GENERAL


# ---------------------------------------------------------------------------
# Model Selection (synchronous helper, no async needed)
# ---------------------------------------------------------------------------

class TestSelectModelFromCandidates:
    def test_reasoning_warm_hit(self, pipe):
        model, is_warm = pipe.select_model_from_candidates(
            CATEGORY_REASONING, ["deepseek-r1:8b"]
        )
        assert model == "deepseek-r1:8b"
        assert is_warm is True

    def test_coding_warm_secondary(self, pipe):
        # qwen3.5:9b is cold, but secondary candidate qwen3.5:4b is warm in VRAM.
        # Router skips cold 9b and selects warm 4b without thrashing GPU.
        model, is_warm = pipe.select_model_from_candidates(
            CATEGORY_CODING, ["qwen3.5:4b"]
        )
        assert model == "qwen3.5:4b"
        assert is_warm is True

    def test_general_cold_start(self, pipe):
        model, is_warm = pipe.select_model_from_candidates(
            CATEGORY_GENERAL, []
        )
        assert model == "smollm2:1.7b"
        assert is_warm is False

    def test_reasoning_cold_start(self, pipe):
        model, is_warm = pipe.select_model_from_candidates(
            CATEGORY_REASONING, []
        )
        assert model == "deepseek-r1:8b"
        assert is_warm is False

    def test_warm_priority_order(self, pipe):
        # Both warm - first candidate wins
        model, is_warm = pipe.select_model_from_candidates(
            CATEGORY_CODING, ["qwen3.5:4b", "qwen3.5:9b"]
        )
        assert model == "qwen3.5:9b"  # 9b is first in CODER_MODELS
        assert is_warm is True

    def test_registry_prefix_warm(self, pipe):
        model, is_warm = pipe.select_model_from_candidates(
            CATEGORY_REASONING,
            ["registry.ollama.ai/library/deepseek-r1:8b"]
        )
        assert model == "deepseek-r1:8b"
        assert is_warm is True

    def test_empty_candidates_fallback(self, pipe):
        # Override CODER_MODELS to empty
        pipe.valves.CODER_MODELS = ""
        model, is_warm = pipe.select_model_from_candidates(CATEGORY_CODING, [])
        assert model == "smollm2:1.7b"
        assert is_warm is False
        # Restore
        pipe.valves = pipe.Valves()


# ---------------------------------------------------------------------------
# Async: get_warm_models graceful degradation
# ---------------------------------------------------------------------------

class TestGetWarmModels:
    @pytest.mark.asyncio
    async def test_returns_empty_on_connection_error(self, pipe):
        # Point to unreachable URL
        pipe.valves.OLLAMA_BASE_URL = "http://127.0.0.1:19999"
        pipe.valves.PS_TIMEOUT_SECONDS = 0.5
        warm = await pipe.get_warm_models()
        assert warm == []
        # Restore
        pipe.valves = pipe.Valves()


# ---------------------------------------------------------------------------
# Message Sanitization Tests
# ---------------------------------------------------------------------------

class TestSanitizeMessages:
    def test_strip_internal_metadata_and_function_calls(self):
        raw = [
            {"role": "user", "content": "hello", "id": "123", "models": ["Auto"]},
            {"role": "assistant", "type": "function_call", "name": "terminal", "content": ""},
            {"role": "assistant", "content": "Hi there!", "statusHistory": []},
            {"role": "user", "content": [{"type": "text", "text": "Solve step by step"}]},
        ]
        from open_webui.warm_auto_router import _sanitize_messages
        clean = _sanitize_messages(raw)
        assert len(clean) == 3
        assert clean[0] == {"role": "user", "content": "hello"}
        assert clean[1] == {"role": "assistant", "content": "Hi there!"}
        assert clean[2] == {"role": "user", "content": "Solve step by step"}
