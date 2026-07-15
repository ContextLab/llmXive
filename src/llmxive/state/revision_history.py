"""Revision-history reader/writer (spec 013 / FR-009 + FR-004).

Owns two on-disk artifacts:

  projects/<PROJ-ID>/paper/revision_history.yaml
    Append-only summary across the paper's lifetime. One entry per
    implementer round. Read by the publisher (badge resolution),
    post-paper-appendix renderer, and the dashboard.

  specs/auto-revisions/<PROJ-ID>/round-<N>/implementer-log.yaml
    Per-task detail for one round. Written once at the end of the round.

Contracts:
  specs/013-paper-revision-implementer/contracts/revision-history-yaml.md
  specs/013-paper-revision-implementer/contracts/implementer-log-yaml.md
"""

from __future__ import annotations

from pathlib import Path

import yaml

from llmxive.state._io import atomic_write_text
from llmxive.types import ImplementerLog, RevisionHistory, RevisionRound


def _hist_path(project_id: str, *, repo_root: Path) -> Path:
    return repo_root / "projects" / project_id / "paper" / "revision_history.yaml"


def _round_path(project_id: str, round_number: int, *, repo_root: Path) -> Path:
    return (
        repo_root / "specs" / "auto-revisions" / project_id
        / f"round-{round_number}" / "implementer-log.yaml"
    )


def load(project_id: str, *, repo_root: Path) -> RevisionHistory:
    """Load `revision_history.yaml`. Returns an empty history if the file
    doesn't exist (the project hasn't had any rounds yet)."""
    p = _hist_path(project_id, repo_root=repo_root)
    if not p.is_file():
        return RevisionHistory(project_id=project_id, rounds=[])
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return RevisionHistory.model_validate(data)


def append_round(
    project_id: str, round: RevisionRound, *, repo_root: Path
) -> None:
    """Append a new round to `revision_history.yaml`. Raises if
    `round.round_number` is already recorded — rounds are 1-indexed and
    strictly monotonic."""
    hist = load(project_id, repo_root=repo_root)
    existing = {r.round_number for r in hist.rounds}
    if round.round_number in existing:
        raise ValueError(f"round {round.round_number} already recorded")
    hist.rounds.append(round)
    hist.rounds.sort(key=lambda r: r.round_number)
    atomic_write_text(
        _hist_path(project_id, repo_root=repo_root),
        yaml.safe_dump(hist.model_dump(mode="json"), sort_keys=False),
    )


def last_n_rounds(
    project_id: str, n: int, *, repo_root: Path
) -> list[RevisionRound]:
    """Return the last `n` rounds (most-recent last). Used by the
    3-consecutive-zero failsafe (FR-015)."""
    if n < 0:
        raise ValueError("n must be >= 0")
    return load(project_id, repo_root=repo_root).rounds[-n:]


def load_round(
    project_id: str, round_number: int, *, repo_root: Path
) -> ImplementerLog:
    """Load `implementer-log.yaml` for a specific round."""
    p = _round_path(project_id, round_number, repo_root=repo_root)
    if not p.is_file():
        raise FileNotFoundError(f"no implementer-log at {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return ImplementerLog.model_validate(data)


def save_round(
    project_id: str,
    round_number: int,
    log: ImplementerLog,
    *,
    repo_root: Path,
) -> None:
    """Write `implementer-log.yaml` for a round. Round directory
    (`specs/auto-revisions/<id>/round-<N>/`) is created if missing."""
    if log.round_number != round_number:
        raise ValueError(
            f"log.round_number={log.round_number} != round_number={round_number}"
        )
    if log.project_id != project_id:
        raise ValueError(
            f"log.project_id={log.project_id!r} != project_id={project_id!r}"
        )
    atomic_write_text(
        _round_path(project_id, round_number, repo_root=repo_root),
        yaml.safe_dump(log.model_dump(mode="json"), sort_keys=False),
    )


def list_rounds(project_id: str, *, repo_root: Path) -> list[int]:
    """Return the sorted list of round numbers that have on-disk logs."""
    base = (repo_root / "specs" / "auto-revisions" / project_id)
    if not base.is_dir():
        return []
    out: list[int] = []
    for d in base.iterdir():
        if d.is_dir() and d.name.startswith("round-"):
            try:
                out.append(int(d.name.removeprefix("round-")))
            except ValueError:
                continue
    return sorted(out)
