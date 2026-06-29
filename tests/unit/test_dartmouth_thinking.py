"""Qwen3 reasoning models default to a hidden ``<think>`` mode that makes every
llmXive call 30-50s (or empty -> empty-reply retry storms -> multi-minute stalls,
the pipeline throughput wall). Disabling it via the vLLM ``chat_template_kwargs``
makes the SAME call ~0.9s (verified). This pins the ``_dartmouth_model_kwargs``
policy that carries the fix into every Dartmouth call.
"""
from __future__ import annotations

from llmxive.backends.dartmouth import _dartmouth_model_kwargs


def test_qwen_disables_thinking_by_default() -> None:
    mk = _dartmouth_model_kwargs("qwen.qwen3.5-122b")
    assert mk["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}
    assert "timeout" in mk  # the hard per-request deadline is still set


def test_qwen_thinking_reenabled_via_env(monkeypatch) -> None:
    monkeypatch.setenv("LLMXIVE_QWEN_ENABLE_THINKING", "1")
    mk = _dartmouth_model_kwargs("qwen.qwen3.5-122b")
    assert "extra_body" not in mk  # opt-in escape hatch restores chain-of-thought
    assert "timeout" in mk


def test_non_qwen_models_untouched() -> None:
    for model in (
        "openai.gpt-oss-120b",
        "google.gemma-3-27b-it",
        "meta.llama-3-2-3b-instruct",
    ):
        mk = _dartmouth_model_kwargs(model)
        assert "extra_body" not in mk, model
        assert "timeout" in mk
