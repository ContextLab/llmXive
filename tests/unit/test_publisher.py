"""Spec 013 / US6 — unit tests for paper_publisher agent (T036).

Covers:
- resolve_badge: 2-state vs 3-state decision per FR-022
- VolumeIssue.from_datetime: YY.MM derivation per FR-024
- publish_blocked counter increments / resets per FR-030
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from llmxive.agents.publisher import _bump_failure_counter, resolve_badge
from llmxive.types import RevisionRound, VolumeIssue

_NOW = datetime(2026, 5, 19, 10, 0, 0, tzinfo=UTC)


def _round(tasks_done: int) -> RevisionRound:
    return RevisionRound(
        round_number=1, ran_at=_NOW,
        implementer_agent="llmXive-implementer-v1.0",
        canonical_identity="canon",
        tasks_done=tasks_done, tasks_failed=0, tasks_skipped=0,
        resulting_pdf_sha256="a" * 64,
        implementer_log_path="x",
        task_outcomes=[],
    )


class TestResolveBadge:
    def test_two_state_when_no_rounds(self) -> None:
        assert resolve_badge([]) == "Auto-Reviewed | Published"

    def test_three_state_when_any_round_has_successes(self) -> None:
        assert resolve_badge([_round(0), _round(5)]) == \
            "Auto-Reviewed | Auto-Revised | Published"

    def test_two_state_when_all_rounds_zero_success(self) -> None:
        """Edge case: rounds exist but every one was all-failed.
        Falls back to the 2-state badge (no revisions actually applied)."""
        assert resolve_badge([_round(0), _round(0)]) == \
            "Auto-Reviewed | Published"

    def test_three_state_single_successful_round(self) -> None:
        assert resolve_badge([_round(1)]) == \
            "Auto-Reviewed | Auto-Revised | Published"


class TestVolumeIssue:
    def test_from_datetime_yy_mm(self) -> None:
        vi = VolumeIssue.from_datetime(datetime(2026, 5, 19, tzinfo=UTC))
        assert vi.volume == "26"
        assert vi.issue == "05"
        assert vi.display == "26.05"

    def test_january(self) -> None:
        vi = VolumeIssue.from_datetime(datetime(2026, 1, 1, tzinfo=UTC))
        assert vi.display == "26.01"

    def test_december(self) -> None:
        vi = VolumeIssue.from_datetime(datetime(2099, 12, 31, tzinfo=UTC))
        assert vi.display == "99.12"


class TestFailureCounter:
    def test_first_failure_increments_to_1(self, tmp_path: Path) -> None:
        n = _bump_failure_counter(tmp_path, "PROJ-X", failed=True)
        assert n == 1

    def test_consecutive_failures_accumulate(self, tmp_path: Path) -> None:
        for expected in (1, 2, 3, 4, 5):
            assert _bump_failure_counter(tmp_path, "PROJ-X", failed=True) == expected

    def test_success_resets_counter(self, tmp_path: Path) -> None:
        _bump_failure_counter(tmp_path, "PROJ-X", failed=True)
        _bump_failure_counter(tmp_path, "PROJ-X", failed=True)
        n = _bump_failure_counter(tmp_path, "PROJ-X", failed=False)
        assert n == 0

    def test_per_project_isolation(self, tmp_path: Path) -> None:
        _bump_failure_counter(tmp_path, "PROJ-A", failed=True)
        _bump_failure_counter(tmp_path, "PROJ-A", failed=True)
        n = _bump_failure_counter(tmp_path, "PROJ-B", failed=True)
        assert n == 1  # PROJ-B's counter is independent of PROJ-A's


class TestPaperPublisherSmoke:
    """Smoke test that the publisher agent class instantiates and
    exposes the expected interface without crashing on import."""

    def test_can_import_class(self) -> None:
        from llmxive.agents.publisher import PaperPublisher
        assert PaperPublisher.__name__ == "PaperPublisher"

    def test_can_construct_with_registry_entry(self) -> None:
        from llmxive.agents.publisher import PaperPublisher
        from llmxive.agents.registry import load
        reg = load()
        entry = next(e for e in reg.agents if e.name == "paper_publisher")
        agent = PaperPublisher(registry_entry=entry)
        assert agent.entry.name == "paper_publisher"
