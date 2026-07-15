"""Append-only JSON Lines run-log writer (T014).

One line per agent invocation under
state/run-log/<YYYY-MM>/<run-id>.jsonl. Schema-validation failures raise
and the failed entry is parked under .invalid/<entry_id>.json for
postmortem (FIX C7 — guarantees SC-003 100% compliance).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import ValidationError  # type: ignore[import-untyped]  # installed, no stubs
from pydantic import ValidationError as PydanticValidationError

from llmxive.config import repo_root as _repo_root
from llmxive.contract_validate import validate
from llmxive.state._io import atomic_write_text
from llmxive.types import Outcome, RunLogEntry


def _state_root() -> Path:
    """The repo's state/ directory.

    Resolved relative to this file (src/llmxive/state/runlog.py → repo/state).
    """
    return _repo_root() / "state"


class CostInvariantError(RuntimeError):
    """Raised when an agent logs a non-zero cost without paid opt-in.

    Per FR-020 + Constitution Principle IV (Free First), runs default to
    free models only (``cost_estimate_usd == 0.0``). The ONLY sanctioned
    non-zero-cost path is the credit-managed Dartmouth daily budget
    (issue #295), active solely when ``LLMXIVE_PAID_OPT_IN`` is set —
    see :mod:`llmxive.backends.credits`. A non-zero cost WITHOUT that
    switch indicates either (a) a backend implementation bug or (b) a
    registry compromise — both warrant a hard failure.
    """


def _check_cost_invariant(entry: RunLogEntry) -> None:
    """T103: hard-block any non-zero cost unless paid opt-in is active.

    When ``LLMXIVE_PAID_OPT_IN`` is enabled, opted-in paid calls log
    their real list-price estimate (honest accounting of credit
    consumption); the backend's credit guard
    (:func:`llmxive.backends.credits.paid_call_allowed`) enforces the
    daily-budget cap before any such call is made.
    """
    if entry.cost_estimate_usd > 0:
        from llmxive.backends.credits import paid_opt_in_enabled

        if paid_opt_in_enabled():
            return
        raise CostInvariantError(
            f"agent {entry.agent_name!r} attempted to log "
            f"cost_estimate_usd={entry.cost_estimate_usd} on backend "
            f"{entry.backend.value!r} without LLMXIVE_PAID_OPT_IN; the "
            f"free-first invariant is 0.0 (the only sanctioned paid path "
            f"is the credit-managed opt-in — issue #295, backends/credits.py)"
        )


def append_entry(entry: RunLogEntry, *, repo_root: Path | None = None) -> Path:
    """Append `entry` to its month's run-log file. Returns the file path.

    Raises ValidationError if the entry's JSON form fails contract validation.
    Raises CostInvariantError if cost_estimate_usd > 0 (T103).
    """
    _check_cost_invariant(entry)

    state_dir = (repo_root / "state") if repo_root else _state_root()
    month = entry.started_at.astimezone(UTC).strftime("%Y-%m")
    log_dir = state_dir / "run-log" / month
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{entry.run_id}.jsonl"

    payload = entry.model_dump(mode="json")
    try:
        validate("run-log-entry", payload)
    except ValidationError:
        invalid_dir = log_dir / ".invalid"
        # Full-file dump of the parked invalid entry — write atomically so a
        # crash mid-dump can't leave a truncated postmortem artifact.
        atomic_write_text(
            invalid_dir / f"{entry.entry_id}.json",
            json.dumps(payload, indent=2, sort_keys=True),
        )
        raise

    # The run-log itself is append-only (one JSONL line per invocation); an
    # append cannot be made atomic the way a full-file rewrite can, so it is
    # left as a bare append (POSIX single-write append is the tolerable case).
    with log_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")
    return log_file


def _parse_run_log_entry(line: str) -> RunLogEntry | None:
    """Parse one ``.jsonl`` line as a RunLogEntry, or None if it isn't one.

    Run-log files also hold FOREIGN records that are not pipeline RunLogEntry
    rows — notably personality-activity entries written by ``personality.py``
    (``action``/``personality_slug``/``display_name`` ... no ``run_id``). The
    strict RunLogEntry model rejects them; every reader here wants only true
    run-log entries, so non-matching lines are skipped rather than crashing
    (the readers previously raised ValidationError on the first such line)."""
    try:
        return RunLogEntry.model_validate_json(line)
    except PydanticValidationError:
        # Foreign record (e.g. personality activity) — not a RunLogEntry.
        return None


def read_entries(run_id: str, *, repo_root: Path | None = None) -> list[RunLogEntry]:
    """Read every entry written for a given run_id, in append order."""
    state_dir = (repo_root / "state") if repo_root else _state_root()
    log_root = state_dir / "run-log"
    if not log_root.is_dir():
        return []
    entries: list[RunLogEntry] = []
    for month_dir in sorted(log_root.iterdir()):
        if not month_dir.is_dir() or month_dir.name.startswith("."):
            continue
        candidate = month_dir / f"{run_id}.jsonl"
        if not candidate.exists():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            parsed = _parse_run_log_entry(line)
            if parsed is not None:
                entries.append(parsed)
    return entries


def latest_for_project(project_id: str, *, repo_root: Path | None = None) -> RunLogEntry | None:
    """Return the most recent entry for a project, scanning all months."""
    state_dir = (repo_root / "state") if repo_root else _state_root()
    log_root = state_dir / "run-log"
    if not log_root.is_dir():
        return None
    latest: RunLogEntry | None = None
    for month_dir in sorted(log_root.iterdir(), reverse=True):
        if not month_dir.is_dir() or month_dir.name.startswith("."):
            continue
        for jsonl in sorted(month_dir.glob("*.jsonl"), reverse=True):
            for line in reversed(jsonl.read_text(encoding="utf-8").splitlines()):
                if not line.strip():
                    continue
                entry = _parse_run_log_entry(line)
                if entry is None:
                    continue
                if entry.project_id == project_id:
                    if latest is None or entry.ended_at > latest.ended_at:
                        latest = entry
                    break  # done with this file
            if latest is not None:
                return latest
    return latest


def producer_of_artifact(
    project_id: str, artifact_path: str, *, repo_root: Path | None = None
) -> str | None:
    """Return the ``agent_name`` that most recently recorded ``artifact_path``
    in its run-log ``outputs`` for ``project_id``, or None if none did.

    Used for self-review prevention (discrepancy #7 / #49): a reviewer whose
    name equals the artifact's producer must not review its own output (the
    ``reviews_store.write`` guard refuses it). Resolving the real producer here
    replaces the former ``produced_by_agent=None`` stub. Scans newest-first and
    returns on the first match (the most-recently-logged producer). Matching is
    by posix path with suffix tolerance so a run-log ``outputs`` entry and a
    ReviewRecord ``artifact_path`` (both repo-relative) compare robustly.
    """
    if not artifact_path:
        return None
    state_dir = (repo_root / "state") if repo_root else _state_root()
    log_root = state_dir / "run-log"
    if not log_root.is_dir():
        return None
    target = artifact_path.replace("\\", "/").strip("/")
    for month_dir in sorted(log_root.iterdir(), reverse=True):
        if not month_dir.is_dir() or month_dir.name.startswith("."):
            continue
        for jsonl in sorted(month_dir.glob("*.jsonl"), reverse=True):
            for line in reversed(jsonl.read_text(encoding="utf-8").splitlines()):
                if not line.strip():
                    continue
                entry = _parse_run_log_entry(line)
                if entry is None or entry.project_id != project_id:
                    continue
                for out in entry.outputs:
                    o = out.replace("\\", "/").strip("/")
                    if o == target or o.endswith("/" + target) or target.endswith("/" + o):
                        return entry.agent_name
    return None


def paper_contributor_models(
    project_id: str, *, repo_root: Path | None = None
) -> dict[str, tuple[str, datetime]]:
    """Return the distinct MODELS that produced paper *content* for a project.

    Scans every run-log entry for ``project_id`` and keeps the successful ones
    whose ``outputs`` touched the manuscript itself — any path under
    ``projects/<id>/paper/`` EXCEPT ``paper/reviews/`` (reviewer records are a
    separate role, not authorship). Authorship is by MODEL, not agent: many
    agent roles (paper writer, figure generator, revision implementer) share a
    single model, and that model is the thing that did the cognition. Returns
    ``{model_name: (backend, earliest_started_at)}`` — one entry per distinct
    model, dated by its FIRST contribution (deterministic author ordering).
    """
    state_dir = (repo_root / "state") if repo_root else _state_root()
    log_root = state_dir / "run-log"
    out: dict[str, tuple[str, datetime]] = {}
    if not log_root.is_dir():
        return out
    paper_prefix = f"projects/{project_id}/paper/"
    reviews_prefix = f"projects/{project_id}/paper/reviews/"
    for month_dir in sorted(log_root.iterdir()):
        if not month_dir.is_dir() or month_dir.name.startswith("."):
            continue
        for jsonl in sorted(month_dir.glob("*.jsonl")):
            for line in jsonl.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                entry = _parse_run_log_entry(line)
                if (
                    entry is None
                    or entry.project_id != project_id
                    or entry.outcome is not Outcome.SUCCESS
                    or not entry.model_name
                ):
                    continue
                touched_paper = any(
                    (paper_prefix in (o.replace("\\", "/")))
                    and (reviews_prefix not in (o.replace("\\", "/")))
                    for o in entry.outputs
                )
                if not touched_paper:
                    continue
                prev = out.get(entry.model_name)
                if prev is None or entry.started_at < prev[1]:
                    out[entry.model_name] = (entry.backend.value, entry.started_at)
    return out


def now_utc() -> datetime:
    """UTC-aware current time helper used across run-log writers."""
    return datetime.now(UTC)


__all__ = [
    "CostInvariantError",
    "append_entry",
    "latest_for_project",
    "now_utc",
    "paper_contributor_models",
    "producer_of_artifact",
    "read_entries",
]
