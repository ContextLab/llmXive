"""Per-project analysis-execution status (spec 023 defect #25).

One canonical JSON record per project under
``state/execution_status/<id>.json`` recording the outcome of the dedicated
execution phase: did the project's analysis code actually RUN and produce
real artifacts? ``research_complete`` is gated on ``ok``; failures drive the
bounded auto-fix loop (re-open failing tasks → implementer fixes → re-run).

Mirrors :mod:`llmxive.state.paper_status` (the established status-record
pattern). No silent fallbacks: a hollow/failed run records ``ok=False`` with
the precise reason + failing-command tails so the next implementer tick has
something concrete to fix.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from llmxive.config import repo_root as _repo_root

#: After this many execution-fix rounds without a clean run, the project
#: escalates honestly (HUMAN_INPUT_NEEDED) instead of looping forever.
#: The cumulative contract ledger (shared_contract.accumulate_contract_issues)
#: prevents true fix-one-break-another thrash, so each extra round is a real
#: convergence opportunity rather than a wasted spin — hence a generous cap.
MAX_EXECUTION_FIX_ROUNDS = 12


def _dir(repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root()
    return root / "state" / "execution_status"


def _path(project_id: str, *, repo_root: Path | None = None) -> Path:
    return _dir(repo_root) / f"{project_id}.json"


def load(project_id: str, *, repo_root: Path | None = None) -> dict[str, Any] | None:
    p = _path(project_id, repo_root=repo_root)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def is_ok(project_id: str, *, repo_root: Path | None = None) -> bool:
    """True iff the latest recorded execution run produced real artifacts."""
    rec = load(project_id, repo_root=repo_root)
    return bool(rec and rec.get("ok") is True)


def fix_rounds(project_id: str, *, repo_root: Path | None = None) -> int:
    rec = load(project_id, repo_root=repo_root) or {}
    n = rec.get("fix_rounds", 0)
    return int(n) if isinstance(n, int) and n >= 0 else 0


def record(
    project_id: str,
    *,
    ok: bool,
    reason: str,
    artifacts: list[str],
    failures: list[str],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Persist one execution attempt. Bumps ``fix_rounds`` on failure (so the
    bounded auto-fix loop terminates), resets it to 0 on success."""
    existing = load(project_id, repo_root=repo_root) or {}
    prior_rounds = existing.get("fix_rounds", 0)
    prior_rounds = int(prior_rounds) if isinstance(prior_rounds, int) and prior_rounds >= 0 else 0
    rec = {
        "project_id": project_id,
        "ok": bool(ok),
        "reason": reason[:2000],
        "artifacts": list(artifacts),
        "failures": [f[:600] for f in failures][:30],
        "fix_rounds": 0 if ok else prior_rounds + 1,
        "updated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    d = _dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    _path(project_id, repo_root=repo_root).write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8"
    )
    return rec


def record_offload(
    project_id: str,
    *,
    status: str,
    kernel_ref: str,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Persist the async GPU-offload tri-state (issue #367) on the record.

    ``status`` is one of ``submitted|running|retrieved|failed``. CRUCIAL: this
    NEVER bumps ``fix_rounds`` — a pending offload is NOT a failure, so the
    bounded auto-fix loop must not advance and the project must not escalate to
    human_input_needed while a kernel is in flight (it stays IN_PROGRESS and
    keeps polling). The rest of the execution record (ok, reason, artifacts,
    failures, fix_rounds) is PRESERVED untouched.
    """
    existing = load(project_id, repo_root=repo_root) or {}
    prior_rounds = existing.get("fix_rounds", 0)
    prior_rounds = int(prior_rounds) if isinstance(prior_rounds, int) and prior_rounds >= 0 else 0
    prior_offload = existing.get("offload") or {}
    submitted_at = (
        prior_offload.get("submitted_at")
        if status in ("running", "retrieved", "failed")
        else None
    ) or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    rec = {
        "project_id": project_id,
        "ok": bool(existing.get("ok", False)),
        "reason": str(existing.get("reason", "")),
        "artifacts": list(existing.get("artifacts", [])),
        "failures": list(existing.get("failures", [])),
        "fix_rounds": prior_rounds,  # NEVER bumped by an offload transition
        "offload": {
            "status": status,
            "kernel_ref": kernel_ref,
            "submitted_at": submitted_at,
        },
        "updated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    d = _dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    _path(project_id, repo_root=repo_root).write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8"
    )
    return rec


def offload_state(project_id: str, *, repo_root: Path | None = None) -> dict[str, Any] | None:
    """The offload sub-record (``{status, kernel_ref, submitted_at}``) or None."""
    rec = load(project_id, repo_root=repo_root) or {}
    off = rec.get("offload")
    return off if isinstance(off, dict) and off.get("kernel_ref") else None


def is_offload_pending(project_id: str, *, repo_root: Path | None = None) -> bool:
    """True iff an offload kernel is in flight (status ``submitted`` or
    ``running``). While pending the gate polls instead of re-running the
    analysis, and the project stays IN_PROGRESS (never escalated)."""
    off = offload_state(project_id, repo_root=repo_root)
    return bool(off and off.get("status") in ("submitted", "running"))


def clear_offload(project_id: str, *, repo_root: Path | None = None) -> None:
    """Drop the offload sub-record (called after a retrieved run is recorded ok),
    leaving the rest of the execution record intact."""
    existing = load(project_id, repo_root=repo_root)
    if not existing or "offload" not in existing:
        return
    existing.pop("offload", None)
    existing["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    d = _dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    _path(project_id, repo_root=repo_root).write_text(
        json.dumps(existing, indent=2) + "\n", encoding="utf-8"
    )


__all__ = [
    "MAX_EXECUTION_FIX_ROUNDS",
    "clear_offload",
    "fix_rounds",
    "is_offload_pending",
    "is_ok",
    "load",
    "offload_state",
    "record",
    "record_offload",
]
