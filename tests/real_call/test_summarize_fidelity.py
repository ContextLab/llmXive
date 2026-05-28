"""Real-call fidelity test for the summarize/desummarize primitive (spec 015 T009/T018).

Gated on ``LLMXIVE_REAL_TESTS=1``. Exercises the FULL path with a real Dartmouth
(qwen3.5-122b) summarize_fn and asserts that, even with a real LLM producing the
per-chunk prose summaries, NO check-critical element (URL/DOI/number/FR-SC-task id)
is lost — they are preserved verbatim on disk and recovered by ``desummarize``
(FR-002/005, SC-001). This is the "validated FIRST" gate for the whole feature.
"""

from __future__ import annotations

import os

import pytest

from llmxive.backends.base import ChatMessage
from llmxive.backends.router import chat_with_fallback
from llmxive.credentials import load_dartmouth_key
from llmxive.tools.summarize import desummarize, estimate_tokens, extract_critical, summarize

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="real-call test; set LLMXIVE_REAL_TESTS=1 to enable",
)

MODEL = "qwen.qwen3.5-122b"
TOKEN_BUDGET = 2_000  # forces overflow + a couple of real summarization calls


def _doc() -> str:
    parts = []
    for i in range(12):
        parts.append(
            f"## Finding {i}\n"
            f"The dataset is at https://example.org/data/{i}/v1 (DOI 10.5281/zenodo.{i:07d}). "
            f"Accuracy was {50 + i}.{i}% (N={1000 + i}); see arXiv:2403.{i:05d}. "
            f"Requirement FR-{i:03d} is covered by task T{i:03d}.\n"
            f"Discussion: " + ("the methodology is described at length with much "
            "supporting prose that a summarizer can safely compress. " * 12) + "\n\n"
        )
    return "".join(parts)


def test_summarize_real_llm_loses_no_critical_element(tmp_path):
    try:
        load_dartmouth_key()
    except Exception as exc:  # key may be unavailable; skip rather than crash
        pytest.skip(f"Dartmouth API key unavailable: {exc}")

    doc = _doc()
    assert estimate_tokens(doc) > TOKEN_BUDGET, "doc must overflow to exercise the LLM path"

    llm_calls = {"n": 0}

    def real_summary_fn(chunk: str, goal: str) -> str:
        llm_calls["n"] += 1
        prompt = (
            f"Summarize the following text for a reviewer whose goal is: {goal}\n"
            f"Be concise (shorter than the input). Output prose only.\n\n=== TEXT ===\n{chunk}"
        )
        resp = chat_with_fallback(
            [ChatMessage(role="user", content=prompt)],
            default_backend="dartmouth",
            fallback_backends=[],
            model=MODEL,
        )
        return (resp.text or "").strip()

    block = summarize(
        doc,
        goal="preserve every URL, DOI, arXiv id, numeric result, and FR/SC/task id verbatim",
        model=MODEL,
        token_budget=TOKEN_BUDGET,
        cache_dir=tmp_path,
        summarize_fn=real_summary_fn,
    )

    # The real LLM path actually ran.
    assert llm_calls["n"] >= 1, "real summarize_fn was never invoked"
    # The returned block fits the budget.
    assert block.startswith("[[LLMXIVE-SUMMARY v1]]")
    assert estimate_tokens(block) <= TOKEN_BUDGET

    # CORE GUARANTEE: every check-critical element survives the real-LLM reduction.
    restored = desummarize(block)
    missing = [c for c in extract_critical(doc) if c not in restored]
    assert not missing, f"real-LLM summarization lost critical elements: {missing}"
