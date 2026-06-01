"""Unit tests for reasoning-aware wall-clock deadlines on the Dartmouth backend.

qwen.qwen3.5-122b (and the gpt-oss family) are *reasoning* models: they spend
completion-token budget on hidden <think> tokens before emitting any answer. A
realistic full-spec (~7k-token) review prompt completes in ~234s — past the
non-reasoning 180s deadline. So reasoning models need a longer wall-clock
deadline (default 360s) while non-reasoning models keep the 180s default.

These tests exercise the REAL ``_deadline_for_model`` seam and module constants
directly — no external model is contacted.
"""

from __future__ import annotations

import importlib

import pytest

from llmxive.backends import dartmouth


def test_reasoning_deadline_default_is_360():
    assert dartmouth._DEFAULT_REASONING_DEADLINE_S == pytest.approx(360.0)


def test_nonreasoning_deadline_default_is_180():
    assert dartmouth._DEFAULT_DEADLINE_S == pytest.approx(180.0)


def test_deadline_for_reasoning_model_is_360():
    # qwen3.5-122b is a reasoning model (hidden <think> tokens).
    assert dartmouth._deadline_for_model("qwen.qwen3.5-122b") == pytest.approx(360.0)


def test_deadline_for_gpt_oss_is_360():
    # gpt-oss family also reasons before answering.
    assert dartmouth._deadline_for_model("openai.gpt-oss-120b") == pytest.approx(360.0)


def test_deadline_for_nonreasoning_model_is_180():
    # gemma is NOT a reasoning model — keep the standard 180s deadline.
    assert dartmouth._deadline_for_model("google.gemma-3-27b-it") == pytest.approx(180.0)


def test_deadline_for_unknown_model_is_180():
    assert dartmouth._deadline_for_model("meta.llama-3-2-3b-instruct") == pytest.approx(
        180.0
    )


def test_deadline_env_overrides(monkeypatch):
    """Both deadlines are env-overridable (matching the _DEFAULT_* pattern)."""
    monkeypatch.setenv("LLMXIVE_DARTMOUTH_DEADLINE_S", "111")
    monkeypatch.setenv("LLMXIVE_DARTMOUTH_REASONING_DEADLINE_S", "222")
    mod = importlib.reload(dartmouth)
    try:
        assert mod._DEFAULT_DEADLINE_S == pytest.approx(111.0)
        assert mod._DEFAULT_REASONING_DEADLINE_S == pytest.approx(222.0)
        assert mod._deadline_for_model("qwen.qwen3.5-122b") == pytest.approx(222.0)
        assert mod._deadline_for_model("google.gemma-3-27b-it") == pytest.approx(111.0)
    finally:
        monkeypatch.delenv("LLMXIVE_DARTMOUTH_DEADLINE_S", raising=False)
        monkeypatch.delenv("LLMXIVE_DARTMOUTH_REASONING_DEADLINE_S", raising=False)
        importlib.reload(dartmouth)
