"""Unit tests for the spec-012 convergence pipeline routing in advancement.py.

Covers FR-001-008 (most-recent-verdict acceptance gate + severity-based
routing), FR-021/022 (arxiv-intake guardrail), and the helper functions
that compose them.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from llmxive.agents.advancement import (
    _all_specialists_accept_most_recent,
    _consolidate_action_items,
    _infer_live_hash,
    _max_severity_across_specialists,
    _most_recent_per_specialist,
)
from llmxive.agents.upstream_feedback import is_arxiv_intake, record_round
from llmxive.types import ActionItem, BackendName, ReviewerKind, ReviewRecord


# --- Helpers -----------------------------------------------------------------


_HASH_A = "a" * 64
_HASH_B = "b" * 64
_NOW = datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc)


def _rec(name: str, verdict: str, *, hash_: str = _HASH_A, when: datetime = _NOW,
         items: list[ActionItem] | None = None, prompt_version: str = "1.1.0") -> ReviewRecord:
    score = 0.5 if verdict == "accept" else 0.0
    if verdict != "accept" and not items:
        items = [ActionItem.from_text("placeholder concern.", "writing")]
    return ReviewRecord(
        reviewer_name=name,
        reviewer_kind=ReviewerKind.LLM,
        artifact_path="projects/PROJ-100-test/paper/metadata.json",
        artifact_hash=hash_,
        score=score,
        verdict=verdict,
        feedback="x",
        reviewed_at=when,
        prompt_version=prompt_version,
        model_name="qwen.qwen3.5-122b",
        backend=BackendName.DARTMOUTH,
        action_items=items or [],
    )


# --- Most-recent-per-specialist gate -----------------------------------------


class TestAllSpecialistsAcceptMostRecent:
    def test_all_accept_passes(self) -> None:
        required = {"paper_reviewer_a", "paper_reviewer_b"}
        records = [_rec("paper_reviewer_a", "accept"), _rec("paper_reviewer_b", "accept")]
        assert _all_specialists_accept_most_recent(records, required, live_hash=_HASH_A) is True

    def test_one_minor_revision_fails(self) -> None:
        required = {"paper_reviewer_a", "paper_reviewer_b"}
        records = [_rec("paper_reviewer_a", "accept"),
                   _rec("paper_reviewer_b", "minor_revision")]
        assert _all_specialists_accept_most_recent(records, required, live_hash=_HASH_A) is False

    def test_most_recent_overrides_older(self) -> None:
        """Specialist A's old verdict was minor_revision; new one is accept.
        The gate honors the NEW verdict."""
        required = {"paper_reviewer_a"}
        old = _rec("paper_reviewer_a", "minor_revision", when=_NOW - timedelta(hours=1))
        new = _rec("paper_reviewer_a", "accept", when=_NOW)
        assert _all_specialists_accept_most_recent([old, new], required, live_hash=_HASH_A) is True

    def test_stale_hash_treated_as_no_review(self) -> None:
        """Specialist A's record has stale artifact_hash → as if they hadn't reviewed.
        Gate fails (not all required have non-stale most-recent accepts)."""
        required = {"paper_reviewer_a", "paper_reviewer_b"}
        records = [
            _rec("paper_reviewer_a", "accept", hash_=_HASH_A),
            _rec("paper_reviewer_b", "accept", hash_=_HASH_B),  # stale
        ]
        assert _all_specialists_accept_most_recent(records, required, live_hash=_HASH_A) is False

    def test_empty_required_gate_passes_trivially(self) -> None:
        """No specialists registered (e.g., empty test registry) → gate is vacuously true."""
        assert _all_specialists_accept_most_recent([], set(), live_hash=_HASH_A) is True


# --- Severity-based routing --------------------------------------------------


class TestMaxSeverityAcrossSpecialists:
    def test_all_accept_returns_none(self) -> None:
        records = [_rec("paper_reviewer_a", "accept"), _rec("paper_reviewer_b", "accept")]
        assert _max_severity_across_specialists(records, live_hash=_HASH_A) is None

    def test_writing_only(self) -> None:
        items = [ActionItem.from_text("typo in abstract.", "writing")]
        records = [_rec("paper_reviewer_a", "minor_revision", items=items)]
        assert _max_severity_across_specialists(records, live_hash=_HASH_A) == "writing"

    def test_science_outranks_writing(self) -> None:
        records = [
            _rec("paper_reviewer_a", "minor_revision",
                 items=[ActionItem.from_text("typo.", "writing")]),
            _rec("paper_reviewer_b", "minor_revision",
                 items=[ActionItem.from_text("missing control condition.", "science")]),
        ]
        assert _max_severity_across_specialists(records, live_hash=_HASH_A) == "science"

    def test_fatal_outranks_all(self) -> None:
        records = [
            _rec("paper_reviewer_a", "minor_revision",
                 items=[ActionItem.from_text("typo.", "writing")]),
            _rec("paper_reviewer_b", "fundamental_flaws",
                 items=[ActionItem.from_text("central hypothesis is unsupportable.", "fatal")]),
        ]
        assert _max_severity_across_specialists(records, live_hash=_HASH_A) == "fatal"

    def test_stale_records_ignored(self) -> None:
        records = [
            _rec("paper_reviewer_a", "accept", hash_=_HASH_A),
            _rec("paper_reviewer_b", "fundamental_flaws", hash_=_HASH_B,
                 items=[ActionItem.from_text("fatal.", "fatal")]),
        ]
        # The fatal record is on a stale hash → ignored. Live is all-accept.
        assert _max_severity_across_specialists(records, live_hash=_HASH_A) is None


# --- Consolidation -----------------------------------------------------------


class TestConsolidateActionItems:
    def test_deduplicates_by_id(self) -> None:
        item_a = ActionItem.from_text("missing β_k.", "writing")
        item_b = ActionItem.from_text("missing β_k value.", "writing")
        # These canonicalize differently in our helper (different texts), but
        # the canonical IDs may not collide. We test that EXACTLY identical
        # items dedupe.
        same = ActionItem.from_text("missing β_k.", "writing")
        records = [
            _rec("paper_reviewer_a", "minor_revision", items=[item_a]),
            _rec("paper_reviewer_b", "minor_revision", items=[same]),  # same id as item_a
        ]
        out = _consolidate_action_items(records, live_hash=_HASH_A)
        assert len(out) == 1
        assert out[0].id == item_a.id

    def test_accept_records_contribute_nothing(self) -> None:
        records = [_rec("paper_reviewer_a", "accept"),
                   _rec("paper_reviewer_b", "minor_revision",
                        items=[ActionItem.from_text("x.", "writing")])]
        out = _consolidate_action_items(records, live_hash=_HASH_A)
        assert len(out) == 1


# --- Live-hash inference -----------------------------------------------------


class TestInferLiveHash:
    def test_picks_most_recent(self) -> None:
        records = [
            _rec("paper_reviewer_a", "accept", hash_=_HASH_A, when=_NOW - timedelta(hours=2)),
            _rec("paper_reviewer_b", "accept", hash_=_HASH_B, when=_NOW),
        ]
        assert _infer_live_hash(records) == _HASH_B

    def test_empty_returns_none(self) -> None:
        assert _infer_live_hash([]) is None


# --- arxiv-intake guardrail (FR-021/022) -------------------------------------


class TestArxivIntakeGuardrail:
    def test_is_arxiv_intake_true_for_metadata_no_specs(self, tmp_path: Path) -> None:
        proj = tmp_path / "projects" / "PROJ-999-x" / "paper"
        proj.mkdir(parents=True)
        (proj / "metadata.json").write_text("{}", encoding="utf-8")
        assert is_arxiv_intake(tmp_path / "projects" / "PROJ-999-x")

    def test_is_arxiv_intake_false_when_specs_exist(self, tmp_path: Path) -> None:
        proj = tmp_path / "projects" / "PROJ-999-x" / "paper"
        (proj / "specs").mkdir(parents=True)
        (proj / "metadata.json").write_text("{}", encoding="utf-8")
        assert not is_arxiv_intake(tmp_path / "projects" / "PROJ-999-x")

    def test_is_arxiv_intake_false_when_no_metadata(self, tmp_path: Path) -> None:
        proj = tmp_path / "projects" / "PROJ-999-x" / "paper"
        proj.mkdir(parents=True)
        assert not is_arxiv_intake(tmp_path / "projects" / "PROJ-999-x")

    def test_record_round_creates_then_appends(self, tmp_path: Path) -> None:
        # Make a project dir + metadata so arxiv_id can be read
        (tmp_path / "projects" / "PROJ-100-x" / "paper").mkdir(parents=True)
        (tmp_path / "projects" / "PROJ-100-x" / "paper" / "metadata.json").write_text(
            '{"arxiv_id": "2605.99999"}', encoding="utf-8"
        )
        items1 = [ActionItem.from_text("Add citation.", "writing")]
        items2 = [ActionItem.from_text("Re-run baseline.", "science")]
        p1 = record_round("PROJ-100-x", verdict_class="writing",
                          action_items=items1, note="round 1", repo_root=tmp_path)
        p2 = record_round("PROJ-100-x", verdict_class="science",
                          action_items=items2, note="round 2", repo_root=tmp_path)
        assert p1 == p2  # same target path
        import yaml as Y
        data = Y.safe_load(p1.read_text())
        assert data["schema_version"] == 1
        assert data["arxiv_id"] == "2605.99999"
        assert len(data["rounds"]) == 2
        assert data["rounds"][0]["round_number"] == 1
        assert data["rounds"][1]["round_number"] == 2
        assert data["rounds"][1]["verdict_class"] == "science"
