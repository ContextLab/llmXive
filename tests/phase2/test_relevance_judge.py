"""Tests for the LLM-based topical-relevance judge (spec 005 fix-up #2).

Pure-function tests on the parser + a real LLM smoke test gated on
DARTMOUTH_CHAT_API_KEY so CI without the key still passes.
"""

from __future__ import annotations

import os

import pytest

from llmxive.credentials import load_dartmouth_key
from llmxive.librarian.relevance_judge import (
    JudgeVerdict,
    _parse_verdict,
    judge_one,
)

HAS_DM_KEY = bool(load_dartmouth_key(prompt_if_missing=False))
_REAL = os.environ.get("LLMXIVE_REAL_TESTS") == "1"


# --- Parser tests (no LLM) ----------------------------------------------------


def test_parse_verdict_yes_canonical() -> None:
    text = "VERDICT: YES\n\nThe paper directly addresses the question."
    v = _parse_verdict(text)
    assert v.relevant is True
    assert "directly addresses" in v.rationale


def test_parse_verdict_no_canonical() -> None:
    text = "VERDICT: NO\n\nThe paper is in the same field but addresses a different sub-question."
    v = _parse_verdict(text)
    assert v.relevant is False
    assert "different sub-question" in v.rationale


def test_parse_verdict_yes_lowercase_first_line() -> None:
    text = "Yes, this paper directly tests the asked-about hypothesis."
    v = _parse_verdict(text)
    assert v.relevant is True


def test_parse_verdict_no_lowercase_first_line() -> None:
    text = "No, the paper covers an unrelated phenomenon."
    v = _parse_verdict(text)
    assert v.relevant is False


def test_parse_verdict_empty_response_fail_open() -> None:
    v = _parse_verdict("")
    assert v.relevant is True
    assert "fail-open" in v.rationale


def test_parse_verdict_uninterpretable_fail_open() -> None:
    """A genuinely garbled response defaults to relevant=True with annotation."""
    v = _parse_verdict("Hmm, well, it depends on context...")
    assert v.relevant is True
    assert "fail-open" in v.rationale or "unparseable" in v.rationale


def test_parse_verdict_inline_no_keyword() -> None:
    """Soft fallback: 'Verdict: NO' anywhere in head → no."""
    text = "After reading the abstract carefully, my Verdict: NO. The paper studies a different problem."
    v = _parse_verdict(text)
    assert v.relevant is False


# --- Real LLM smoke test (gated on backend availability) ----------------------


@pytest.mark.skipif(not (HAS_DM_KEY and _REAL), reason="judge LLM requires DARTMOUTH_CHAT_API_KEY + LLMXIVE_REAL_TESTS=1")
def test_judge_one_returns_no_for_field_adjacent_paper() -> None:
    """The bug we're solving: 'GNN for dipole-moment prediction' should
    NOT admit a 'GNN for social-influence prediction' paper, even
    though both pass token-overlap."""
    v = judge_one(
        query="Predicting molecular dipole moments with graph neural networks",
        candidate_title=(
            "Social Influence Prediction with Train and Test Time "
            "Augmentation for Graph Neural Networks"
        ),
        candidate_abstract=(
            "We propose a method for predicting social influence in online "
            "networks using graph neural networks with train- and test-time "
            "data augmentation."
        ),
    )
    assert isinstance(v, JudgeVerdict)
    # Either NO outright, or fail-open with rationale citing the mismatch —
    # either is acceptable behavior, but a clean LLM call should produce NO.
    assert v.relevant is False or v.backend_error is not None, (
        f"judge admitted obviously off-topic paper: rationale={v.rationale!r}"
    )


@pytest.mark.skipif(not (HAS_DM_KEY and _REAL), reason="judge LLM requires DARTMOUTH_CHAT_API_KEY + LLMXIVE_REAL_TESTS=1")
def test_judge_one_returns_yes_for_on_topic_paper() -> None:
    """Conversely a directly-on-topic paper should pass."""
    v = judge_one(
        query="Predicting molecular dipole moments with graph neural networks",
        candidate_title=(
            "PhysNet: A Neural Network for Predicting Energies, Forces, "
            "Dipole Moments, and Partial Charges"
        ),
        candidate_abstract=(
            "We present PhysNet, a deep neural network architecture that "
            "predicts molecular energies, forces, dipole moments, and "
            "partial atomic charges from molecular geometries."
        ),
    )
    assert v.relevant is True, (
        f"judge rejected obviously on-topic paper: rationale={v.rationale!r}"
    )
