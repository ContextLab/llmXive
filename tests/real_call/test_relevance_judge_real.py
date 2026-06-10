"""Real-call: librarian relevance judge determinism (issue #112).

Validates the two-part fix with REAL inference (no mocks — Constitution
III): ``JUDGE_TEMPERATURE = 0.0`` on every call, and the frozen
per-verdict disk cache replaying identical judgments on re-runs.

Uses the verbatim PROJ-261 research question — the project whose
strict/marginal citation split flipped between flesh_out re-runs in the
issue's original evidence.

Backend selection (so the suite runs both in CI and in offline-from-
Dartmouth dev containers):
  - default: Dartmouth Chat + qwen.qwen3.5-122b (nightly CI)
  - override: LLMXIVE_JUDGE_TEST_BACKEND=local +
    LLMXIVE_JUDGE_TEST_MODEL=Qwen/Qwen2.5-0.5B-Instruct exercises the
    same code path through the local transformers backend (validated
    2026-06-10: 3/3 identical verdicts, ~18 s/call on CPU).
"""

from __future__ import annotations

import json
import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="set LLMXIVE_REAL_TESTS=1 to exercise live LLM calls",
)

BACKEND = os.environ.get("LLMXIVE_JUDGE_TEST_BACKEND", "dartmouth")
MODEL = os.environ.get("LLMXIVE_JUDGE_TEST_MODEL", "qwen.qwen3.5-122b")

# PROJ-261 (verbatim from projects/PROJ-261-.../idea/) — the issue #112
# reproduction case.
QUERY = (
    "How does the local density of syntactic code clones correlate with "
    "the perplexity and bug-detection accuracy of pre-trained language "
    "models on open-source Python code?"
)

OFF_TOPIC = dict(
    candidate_title=(
        "Gut microbiome diversity in alpine marmots across seasonal "
        "hibernation cycles"
    ),
    candidate_abstract=(
        "We sequence 16S rRNA from wild marmots to characterize seasonal "
        "shifts in gut microbial composition during hibernation."
    ),
)


def _judge(**extra):
    from llmxive.librarian.relevance_judge import judge_one

    return judge_one(
        query=QUERY,
        model=MODEL,
        default_backend=BACKEND,
        fallback_backends=[],
        **OFF_TOPIC,
        **extra,
    )


def test_judge_is_deterministic_across_reruns_real():
    """Same (query, candidate) × 3 cache-less calls → identical verdicts.

    This is the exact failure mode from #112: pre-fix, backend-default
    sampling flipped these run-to-run."""
    verdicts = [_judge() for _ in range(3)]
    assert all(not v.fail_open for v in verdicts), (
        f"judge produced fail-open verdicts: {verdicts}"
    )
    assert len({v.relevant for v in verdicts}) == 1, (
        f"verdicts flipped across runs: {[v.relevant for v in verdicts]}"
    )
    # An off-domain candidate sharing zero mechanism/vocabulary with the
    # question must be rejected (even the 0.5B local probe gets this right).
    assert verdicts[0].relevant is False


def test_judge_verdict_frozen_in_cache_real(tmp_path):
    """First real resolution freezes the verdict; the second call replays
    it from disk without re-rolling the LLM."""
    from llmxive.librarian.relevance_judge import (
        JUDGE_PROMPT_VERSION,
        _verdict_cache_key,
        _verdict_cache_path,
    )

    pointer = "probe:marmot-microbiome-2026"
    first = _judge(candidate_pointer=pointer, repo_root=tmp_path)
    assert first.fail_open is False
    assert first.cached is False

    key = _verdict_cache_key(QUERY, pointer)
    cache_file = _verdict_cache_path(tmp_path, key)
    assert cache_file.is_file()
    entry = json.loads(cache_file.read_text(encoding="utf-8"))
    assert entry["prompt_version"] == JUDGE_PROMPT_VERSION
    assert entry["relevant"] is first.relevant

    second = _judge(candidate_pointer=pointer, repo_root=tmp_path)
    assert second.cached is True
    assert second.relevant is first.relevant
