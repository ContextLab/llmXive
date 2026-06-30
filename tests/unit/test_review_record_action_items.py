"""Tests for ReviewRecord.action_items field (spec 012 / FR-018)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from llmxive.types import ActionItem, BackendName, ReviewerKind, ReviewRecord


def _base_kwargs(verdict: str = "accept", score: float = 0.5, prompt_version: str = "1.1.0",
                  action_items: list[ActionItem] | None = None) -> dict:
    return {
        "reviewer_name": "paper_reviewer_jargon_police",
        "reviewer_kind": ReviewerKind.LLM,
        "artifact_path": "projects/PROJ-100-test/paper/metadata.json",
        "artifact_hash": "a" * 64,
        "score": score,
        "verdict": verdict,
        "feedback": "x",
        "reviewed_at": datetime.now(UTC),
        "prompt_version": prompt_version,
        "model_name": "qwen.qwen3.5-122b",
        "backend": BackendName.DARTMOUTH,
        "action_items": action_items if action_items is not None else [],
    }


class TestReviewRecordActionItems:
    def test_accept_with_empty_action_items_is_valid(self) -> None:
        rec = ReviewRecord(**_base_kwargs(verdict="accept", score=0.5))
        assert rec.action_items == []

    def test_accept_with_action_items_is_valid_informational(self) -> None:
        # Per spec: accept verdict MAY have action_items (informational only).
        items = [ActionItem.from_text("minor: consider rewording intro.", "writing")]
        rec = ReviewRecord(**_base_kwargs(verdict="accept", score=0.5,
                                          action_items=items))
        assert len(rec.action_items) == 1

    def test_minor_revision_without_action_items_v110_raises(self) -> None:
        # FR-018: non-accept verdict under prompt_version >= 1.1.0 must have ≥1 item.
        with pytest.raises(ValidationError):
            ReviewRecord(**_base_kwargs(verdict="minor_revision", score=0.0,
                                        prompt_version="1.1.0", action_items=[]))

    def test_minor_revision_with_action_items_v110_is_valid(self) -> None:
        items = [ActionItem.from_text("Add unit to Table column.", "writing")]
        rec = ReviewRecord(**_base_kwargs(verdict="minor_revision", score=0.0,
                                          prompt_version="1.1.0", action_items=items))
        assert rec.verdict == "minor_revision"

    def test_backcompat_v100_legacy_record_loads_without_items(self) -> None:
        # Legacy records emitted under prompt_version 1.0.0 are grandfathered:
        # the action_items validator doesn't fire.
        rec = ReviewRecord(**_base_kwargs(verdict="minor_revision", score=0.0,
                                          prompt_version="1.0.0", action_items=[]))
        assert rec.action_items == []

    def test_fatal_severity_action_item(self) -> None:
        # A fatal action item is allowed alongside any non-accept verdict.
        items = [ActionItem.from_text("Central hypothesis is unsupportable.", "fatal")]
        rec = ReviewRecord(**_base_kwargs(verdict="fundamental_flaws", score=0.0,
                                          prompt_version="1.1.0", action_items=items))
        assert rec.action_items[0].severity == "fatal"


def test_canonical_llm_review_score_derives_from_verdict() -> None:
    """The LLM review score is a pure function of the verdict (accept -> 0.5,
    every non-accept -> 0.0). The reviewer agents derive it through this helper
    so a weak model's stray score never fails ReviewRecord validation."""
    from llmxive.types import canonical_llm_review_score

    assert canonical_llm_review_score("accept") == 0.5
    for v in ("minor_revision", "full_revision", "reject",
              "major_revision_writing", "major_revision_science", "fundamental_flaws"):
        assert canonical_llm_review_score(v) == 0.0


def test_derived_score_repairs_model_verdict_score_mismatch() -> None:
    """A weak model emits `accept` + score 1.0 (a valid-set member, but wrong for
    the verdict) — `_score_matches_verdict` rejects it, which burned the whole
    reviewer retry budget at research_review (live PROJ-552 first-crossing run).
    Deriving the score from the verdict before validation makes the record
    valid — exactly what research_reviewer / paper_reviewer now do."""
    from llmxive.types import canonical_llm_review_score

    front = _base_kwargs(verdict="accept", score=1.0)  # as the weak model wrote it
    with pytest.raises(ValidationError, match="accept must score 0.5"):
        ReviewRecord(**front)
    front["score"] = canonical_llm_review_score(front["verdict"])
    rec = ReviewRecord(**front)
    assert rec.score == 0.5 and rec.verdict == "accept"
