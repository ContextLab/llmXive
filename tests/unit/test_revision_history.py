"""Spec 013 — unit tests for state/revision_history.py (FR-004, FR-009).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from llmxive.state import revision_history as rh
from llmxive.types import (
    ImplementerLog,
    ImplementerLogEntry,
    RevisionRound,
)


_NOW = datetime(2026, 5, 19, 10, 14, 0, tzinfo=timezone.utc)


def _make_round(round_n: int, tasks_done: int = 5) -> RevisionRound:
    return RevisionRound(
        round_number=round_n,
        ran_at=_NOW,
        implementer_agent="llmXive-implementer-v1.0",
        canonical_identity=f"llmXive-implementer-v1.0 (m on b, {_NOW:%Y-%m-%d})",
        tasks_done=tasks_done,
        tasks_failed=0,
        tasks_skipped=0,
        resulting_pdf_sha256="a" * 64,
        implementer_log_path=f"specs/auto-revisions/PROJ-001-test/round-{round_n}/implementer-log.yaml",
        task_outcomes=[],
    )


def _make_log(round_n: int, total: int = 5, done: int = 5) -> ImplementerLog:
    outcomes = [
        ImplementerLogEntry(
            task_id=f"task{i}",
            status="done" if i < done else "compile-failed",
            action_item_severity="writing",
            action_item_text=f"task {i}",
            duration_s=1.0,
        )
        for i in range(total)
    ]
    return ImplementerLog(
        round_number=round_n,
        project_id="PROJ-001-test",
        revision_spec_path=f"specs/auto-revisions/PROJ-001-test/round-{round_n}",
        implementer_agent="llmXive-implementer-v1.0",
        agent_version="1.0.0",
        model_name="m",
        backend="b",
        canonical_identity=f"llmXive-implementer-v1.0 (m on b, {_NOW:%Y-%m-%d})",
        started_at=_NOW,
        ended_at=_NOW,
        duration_s=0.0,
        exit_reason="all-tasks-processed",
        total_tasks=total,
        tasks_done=done,
        tasks_compile_failed=total - done,
        tasks_file_not_found=0,
        tasks_skipped=0,
        tasks_needs_external_data=0,
        task_outcomes=outcomes,
    )


class TestRevisionHistory:
    def test_load_empty(self, tmp_path: Path) -> None:
        hist = rh.load("PROJ-001-test", repo_root=tmp_path)
        assert hist.rounds == []

    def test_append_round_persists(self, tmp_path: Path) -> None:
        rh.append_round("PROJ-001-test", _make_round(1), repo_root=tmp_path)
        hist = rh.load("PROJ-001-test", repo_root=tmp_path)
        assert len(hist.rounds) == 1
        assert hist.rounds[0].round_number == 1

    def test_append_duplicate_round_raises(self, tmp_path: Path) -> None:
        rh.append_round("PROJ-001-test", _make_round(1), repo_root=tmp_path)
        with pytest.raises(ValueError, match="round 1 already recorded"):
            rh.append_round("PROJ-001-test", _make_round(1), repo_root=tmp_path)

    def test_append_multiple_rounds_in_order(self, tmp_path: Path) -> None:
        rh.append_round("PROJ-001-test", _make_round(2), repo_root=tmp_path)
        rh.append_round("PROJ-001-test", _make_round(1), repo_root=tmp_path)
        rh.append_round("PROJ-001-test", _make_round(3), repo_root=tmp_path)
        hist = rh.load("PROJ-001-test", repo_root=tmp_path)
        assert [r.round_number for r in hist.rounds] == [1, 2, 3]

    def test_last_n_rounds(self, tmp_path: Path) -> None:
        for i in (1, 2, 3, 4):
            rh.append_round("PROJ-001-test", _make_round(i), repo_root=tmp_path)
        last = rh.last_n_rounds("PROJ-001-test", 3, repo_root=tmp_path)
        assert [r.round_number for r in last] == [2, 3, 4]


class TestImplementerLog:
    def test_save_and_load_round(self, tmp_path: Path) -> None:
        log = _make_log(1)
        rh.save_round("PROJ-001-test", 1, log, repo_root=tmp_path)
        loaded = rh.load_round("PROJ-001-test", 1, repo_root=tmp_path)
        assert loaded.round_number == 1
        assert loaded.total_tasks == 5
        assert len(loaded.task_outcomes) == 5

    def test_save_round_mismatch_raises(self, tmp_path: Path) -> None:
        log = _make_log(1)
        with pytest.raises(ValueError):
            rh.save_round("PROJ-001-test", 99, log, repo_root=tmp_path)

    def test_list_rounds(self, tmp_path: Path) -> None:
        rh.save_round("PROJ-001-test", 1, _make_log(1), repo_root=tmp_path)
        rh.save_round("PROJ-001-test", 3, _make_log(3), repo_root=tmp_path)
        assert rh.list_rounds("PROJ-001-test", repo_root=tmp_path) == [1, 3]

    def test_log_count_invariant_enforced(self) -> None:
        """ImplementerLog model_validator: sum of outcomes == total_tasks."""
        with pytest.raises(ValueError, match="must sum to total_tasks"):
            ImplementerLog(
                round_number=1, project_id="PROJ-001-test", revision_spec_path="x",
                implementer_agent="x", agent_version="1", model_name="m",
                backend="b", canonical_identity="x",
                started_at=_NOW, ended_at=_NOW, duration_s=0.0,
                exit_reason="all-tasks-processed",
                total_tasks=5,
                tasks_done=2, tasks_compile_failed=2,
                tasks_file_not_found=0, tasks_skipped=0, tasks_needs_external_data=0,
                task_outcomes=[],  # 0 != 5
            )
