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

#: Stages counted as DOWNSTREAM in-flight work — a project that has left the idea
#: stages and entered the implementation/execution pipeline. Seeding MORE ideas
#: while this pit is congested (the live #1139 state: 492 projects at in_progress,
#: ~0 reaching research_complete) just grows unbounded WIP behind a stalled
#: pipeline — the intake throttle was BLIND to it (it watched only the idea
#: backlog ~192, which was flat, so it granted full intake). issue #1139 M1.
DOWNSTREAM_WIP_STAGES: frozenset[Stage] = frozenset(
    {
        Stage.PLANNED,
        Stage.TASKED,
        Stage.ANALYZE_IN_PROGRESS,
        Stage.ANALYZED,
        Stage.IN_PROGRESS,
    }
)

#: Backlog-growth measurement window.
WINDOW_HOURS: float = 24.0

#: Growth (projects added net over the window) at which automated intake
#: shuts off entirely; below it the allowance scales linearly.
FULL_STOP_GROWTH: int = 20

#: Net DOWNSTREAM-WIP growth over the window at which automated intake shuts off
#: (drain < intake through the whole pipeline, not just the idea stages).
DOWNSTREAM_FULL_STOP_GROWTH: int = 40

#: Absolute downstream-WIP size above which automated intake is damped REGARDLESS
#: of growth — a congested implementation pipeline must DRAIN (projects reaching
#: research_complete) before more ideas enter. Self-recovering: as WIP falls back
#: under the ceiling the allowance returns to full.
DOWNSTREAM_WIP_CEILING: int = 250

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


def downstream_wip_depth(*, repo_root: Path | None = None) -> int:
    """Current DOWNSTREAM in-flight work (implementation/execution pipeline)."""
    return sum(
        1
        for p in project_store.list_all(repo_root=repo_root)
        if p.current_stage in DOWNSTREAM_WIP_STAGES
    )


def _growth_fraction(growth: int, full_stop: int) -> float:
    """Linear allowance fraction: 1.0 at growth<=0, 0.0 at ``full_stop``."""
    if growth <= 0:
        return 1.0
    return max(0.0, 1.0 - growth / full_stop)


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
    wip = downstream_wip_depth(repo_root=repo_root)
    state = _load_state(repo_root)
    cutoff = now - timedelta(hours=WINDOW_HOURS)
    samples = [
        s
        for s in state["samples"]
        if datetime.fromisoformat(str(s["at"])) >= cutoff
    ]
    samples.append({"at": now.isoformat(), "backlog": depth, "wip": wip})

    growth = 0
    wip_growth = 0
    if len(samples) >= 2:
        growth = depth - int(samples[0]["backlog"])
        # Old samples (pre-#1139-M1) have no "wip" key → treat as the current
        # value so a missing history contributes 0 growth (never a false stop).
        wip_growth = wip - int(samples[0].get("wip", wip))

    requested = max(0, requested)
    # Three self-recovering signals, each a linear allowance fraction; the
    # allowance is damped by the WORST (smallest) of them (issue #1139 M1):
    #   1. idea-stage backlog growth (the original FR-008 signal);
    #   2. DOWNSTREAM-WIP growth (the implementation pipeline filling faster than
    #      it drains) — the signal the throttle was blind to;
    #   3. an absolute downstream-WIP ceiling (a congested pipeline must DRAIN
    #      before more ideas enter, regardless of growth).
    f_backlog = _growth_fraction(growth, FULL_STOP_GROWTH)
    f_wip_growth = _growth_fraction(wip_growth, DOWNSTREAM_FULL_STOP_GROWTH)
    f_wip_ceiling = _growth_fraction(
        max(0, wip - DOWNSTREAM_WIP_CEILING), DOWNSTREAM_WIP_CEILING
    )
    fraction = min(f_backlog, f_wip_growth, f_wip_ceiling)
    allowed = int(requested * fraction)
    if fraction >= 1.0:
        reason = (
            f"backlog flat/draining (growth={growth}) and downstream WIP "
            f"healthy (wip={wip}, growth={wip_growth}); full intake"
        )
    else:
        # Name the binding constraint so the decision is self-explaining.
        binding = min(
            ("idea-backlog", f_backlog),
            ("downstream-WIP-growth", f_wip_growth),
            ("downstream-WIP-ceiling", f_wip_ceiling),
            key=lambda kv: kv[1],
        )[0]
        reason = (
            f"damped to {fraction:.0%} by {binding} "
            f"(idea growth={growth}, wip={wip}, wip growth={wip_growth}, "
            f"ceiling={DOWNSTREAM_WIP_CEILING})"
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
    "DOWNSTREAM_FULL_STOP_GROWTH",
    "DOWNSTREAM_WIP_CEILING",
    "DOWNSTREAM_WIP_STAGES",
    "FULL_STOP_GROWTH",
    "IDEA_BACKLOG_STAGES",
    "MIN_HUMAN_ALLOWANCE",
    "WINDOW_HOURS",
    "IntakeDecision",
    "backlog_depth",
    "downstream_wip_depth",
    "intake_allowance",
]
