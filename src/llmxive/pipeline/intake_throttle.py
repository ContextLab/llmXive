"""Automatic new-idea intake throttling (spec 023 / FR-008).

The idea-stage backlog (brainstormed → flesh-out → awaiting validation)
grew without bound pre-023: hourly brainstorm + HF-papers intake added
ideas faster than anything drained them (589 projects parked at
``flesh_out_complete``; issue #303). Every AUTOMATED intake entry point
now asks :func:`intake_allowance` before seeding ideas:

- each call records a (timestamp, backlog-depth) sample into the
  observable throttle state at ``state/intake_throttle.yaml``;
- when the backlog GREW over the measurement window (drain < intake),
  the allowance shrinks proportionally to the growth — down to zero for
  ``kind="auto"`` intake;
- when the backlog is flat or draining, full allowance resumes
  automatically (throttling is proportional and self-recovering —
  spec 023 edge case: no permanent starvation);
- human submissions (``kind="human"``) are never throttled below
  ``MIN_HUMAN_ALLOWANCE`` per tick — the throttle targets automated
  intake, not people.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml

from llmxive.config import repo_root as _repo_root
from llmxive.state import project as project_store
from llmxive.types import Stage

#: Stages counted as "the idea-stage backlog" — everything between intake
#: and a passed validation.
IDEA_BACKLOG_STAGES: frozenset[Stage] = frozenset(
    {
        Stage.BRAINSTORMED,
        Stage.FLESH_OUT_IN_PROGRESS,
        Stage.FLESH_OUT_COMPLETE,
    }
)

#: Backlog-growth measurement window.
WINDOW_HOURS: float = 24.0

#: Growth (projects added net over the window) at which automated intake
#: shuts off entirely; below it the allowance scales linearly.
FULL_STOP_GROWTH: int = 20

#: Human submissions are never throttled below this per tick.
MIN_HUMAN_ALLOWANCE: int = 1

_STATE_REL = Path("state") / "intake_throttle.yaml"


@dataclass(frozen=True)
class IntakeDecision:
    """Observable record of one throttle decision (FR-008)."""

    requested: int
    allowed: int
    backlog: int
    growth: int
    window_hours: float
    kind: str
    reason: str
    decided_at: str

    @property
    def throttled(self) -> bool:
        return self.allowed < self.requested


def _state_path(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / _STATE_REL


def _load_state(repo_root: Path | None = None) -> dict:
    path = _state_path(repo_root)
    if not path.is_file():
        return {"samples": [], "last_decision": None}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data.setdefault("samples", [])
    data.setdefault("last_decision", None)
    return data


def _save_state(data: dict, repo_root: Path | None = None) -> None:
    path = _state_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def backlog_depth(*, repo_root: Path | None = None) -> int:
    """Current idea-stage backlog size from canonical project state."""
    return sum(
        1
        for p in project_store.list_all(repo_root=repo_root)
        if p.current_stage in IDEA_BACKLOG_STAGES
    )


def intake_allowance(
    requested: int,
    *,
    repo_root: Path | None = None,
    kind: str = "auto",
    now: datetime | None = None,
) -> IntakeDecision:
    """How many new ideas this intake tick may seed (FR-008).

    Records the backlog sample + the decision into the observable
    throttle state. ``kind="human"`` floors the allowance at
    ``MIN_HUMAN_ALLOWANCE``.
    """
    now = now or datetime.now(UTC)
    depth = backlog_depth(repo_root=repo_root)
    state = _load_state(repo_root)
    cutoff = now - timedelta(hours=WINDOW_HOURS)
    samples = [
        s
        for s in state["samples"]
        if datetime.fromisoformat(str(s["at"])) >= cutoff
    ]
    samples.append({"at": now.isoformat(), "backlog": depth})

    growth = 0
    if len(samples) >= 2:
        growth = depth - int(samples[0]["backlog"])

    requested = max(0, requested)
    if growth <= 0:
        allowed = requested
        reason = (
            f"backlog flat/draining over the window (growth={growth}); "
            "full intake"
        )
    else:
        # Proportional damping: linear from full allowance at growth=0 to
        # zero at FULL_STOP_GROWTH.
        fraction = max(0.0, 1.0 - growth / FULL_STOP_GROWTH)
        allowed = int(requested * fraction)
        reason = (
            f"backlog grew by {growth} over {WINDOW_HOURS:.0f}h "
            f"(drain < intake); allowance damped to {fraction:.0%}"
        )
    if kind == "human":
        allowed = max(allowed, min(requested, MIN_HUMAN_ALLOWANCE))

    decision = IntakeDecision(
        requested=requested,
        allowed=allowed,
        backlog=depth,
        growth=growth,
        window_hours=WINDOW_HOURS,
        kind=kind,
        reason=reason,
        decided_at=now.isoformat(),
    )
    state["samples"] = samples
    state["last_decision"] = asdict(decision)
    _save_state(state, repo_root)
    return decision


__all__ = [
    "FULL_STOP_GROWTH",
    "IDEA_BACKLOG_STAGES",
    "MIN_HUMAN_ALLOWANCE",
    "WINDOW_HOURS",
    "IntakeDecision",
    "backlog_depth",
    "intake_allowance",
]
