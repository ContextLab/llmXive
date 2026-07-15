"""The scheduler honours the advance-error ledger (issue #1139, defect D5).

``_eligible_candidates`` must EXCLUDE a project whose typed ledger record
(:mod:`llmxive.pipeline.advance_ledger`) is still holding it out of scheduling —
inside a transient backoff window, or in a rerouted/terminal disposition — and
INCLUDE it again once the backoff elapses. A terminal/invariant record is never
resurrected by backoff, and a record for a stage the project has since left is
stale and ignored. Real project YAMLs + real ledger files (no mocks).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from llmxive.pipeline import advance_ledger as al
from llmxive.pipeline import scheduler
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


def _make(repo: Path, pid: str, stage: Stage = Stage.PROJECT_INITIALIZED) -> Project:
    now = datetime.now(UTC)
    p = Project(
        id=pid, title=pid, field="test", current_stage=stage,
        created_at=now, updated_at=now, artifact_hashes={},
    )
    project_store.save(p, repo_root=repo)
    return p


def _repo(tmp_path: Path) -> Path:
    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)
    return tmp_path


def _eligible_ids(repo: Path) -> set[str]:
    return {p.id for p in scheduler._eligible_candidates(repo_root=repo, stage=None)}


def test_backoff_excludes_then_includes(tmp_path) -> None:
    repo = _repo(tmp_path)
    chain = "every backend in chain ['dartmouth', 'local'] failed"

    # A: transient failure recorded NOW -> retry_after in the future -> HELD.
    a = _make(repo, "PROJ-810-a")
    al.record_failure(a, RuntimeError(chain), repo_root=repo, now=datetime.now(UTC))

    # B: transient failure recorded 2 days ago -> retry_after long past -> ELIGIBLE.
    b = _make(repo, "PROJ-811-b")
    al.record_failure(
        b, RuntimeError(chain), repo_root=repo,
        now=datetime.now(UTC) - timedelta(days=2),
    )

    # C: no ledger record at all -> ELIGIBLE.
    _make(repo, "PROJ-812-c")

    ids = _eligible_ids(repo)
    assert "PROJ-810-a" not in ids  # excluded: inside backoff window
    assert "PROJ-811-b" in ids  # included: backoff elapsed
    assert "PROJ-812-c" in ids  # included: no record


def test_terminal_and_rerouted_records_are_held_not_resurrected(tmp_path) -> None:
    repo = _repo(tmp_path)

    # D: invariant (invalid transition) -> terminal, no retry_after -> HELD.
    d = _make(repo, "PROJ-820-d", Stage.PROJECT_INITIALIZED)
    al.record_failure(
        d, RuntimeError("invalid transition in_progress -> clarified"), repo_root=repo
    )

    # E: permanent (dead reference) -> rerouted, no retry_after -> HELD.
    e = _make(repo, "PROJ-821-e")
    al.record_failure(
        e, RuntimeError("research.md reference is unreachable: 'https://x/' (HTTP 404)"),
        repo_root=repo,
    )

    ids = _eligible_ids(repo)
    assert "PROJ-820-d" not in ids
    assert "PROJ-821-e" not in ids

    # Force a *past* retry_after onto the terminal record: a terminal disposition
    # must NOT be resurrected by an elapsed backoff time.
    rec = al.load_record("PROJ-820-d", repo_root=repo)
    rec["retry_after"] = (datetime.now(UTC) - timedelta(days=30)).isoformat()
    al.record_path("PROJ-820-d", repo).write_text(__import__("json").dumps(rec))
    assert "PROJ-820-d" not in _eligible_ids(repo)  # still held


def test_stale_record_for_earlier_stage_is_ignored(tmp_path) -> None:
    repo = _repo(tmp_path)
    # Fail at flesh_out_complete (future backoff -> would be held)...
    f = _make(repo, "PROJ-830-f", Stage.FLESH_OUT_COMPLETE)
    al.record_failure(
        f, RuntimeError("every backend in chain ['dartmouth','local'] failed"),
        repo_root=repo, now=datetime.now(UTC),
    )
    assert "PROJ-830-f" not in _eligible_ids(repo)  # held at flesh_out_complete

    # ...then the project advances. The record is now for a stage it has left
    # -> stale -> ignored -> ELIGIBLE again.
    _make(repo, "PROJ-830-f", Stage.PROJECT_INITIALIZED)  # re-save at the later stage
    assert "PROJ-830-f" in _eligible_ids(repo)


def test_no_records_is_unchanged_behavior(tmp_path) -> None:
    # With no ledger dir at all, eligibility is exactly as before (no regressions).
    repo = _repo(tmp_path)
    _make(repo, "PROJ-840-a")
    _make(repo, "PROJ-841-b", Stage.FLESH_OUT_COMPLETE)
    _make(repo, "PROJ-842-posted", Stage.POSTED)  # terminal stage still excluded
    ids = _eligible_ids(repo)
    assert ids == {"PROJ-840-a", "PROJ-841-b"}
