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


__all__ = [
    "MAX_EXECUTION_FIX_ROUNDS",
    "fix_rounds",
    "is_ok",
    "load",
    "record",
]
