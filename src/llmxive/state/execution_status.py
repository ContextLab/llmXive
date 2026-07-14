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
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from llmxive.config import repo_root as _repo_root

logger = logging.getLogger(__name__)

#: After this many execution-fix rounds without a clean run AT THE CURRENT
#: model tier, the project ESCALATES to the next model tier (resetting
#: fix_rounds to 0) — and only when ALL tiers are exhausted does it re-plan
#: deterministically. It NEVER parks a project at HUMAN_INPUT_NEEDED (the sole
#: sanctioned human gate is publication DOI sign-off).
#: The cumulative contract ledger (shared_contract.accumulate_contract_issues)
#: prevents true fix-one-break-another thrash, so each extra round is a real
#: convergence opportunity rather than a wasted spin — hence a generous cap.
MAX_EXECUTION_FIX_ROUNDS = 12

#: Cap on the OUTER loop: how many times a project may be re-planned out of the
#: execution fix-loop before we admit its analysis cannot be run here. Each re-plan
#: already costs a FULL ladder (MAX_EXECUTION_FIX_ROUNDS x every model tier), so this
#: is a generous bound, not a hair trigger. Beyond it the honest outcome is a terminal
#: rejection — NOT another lap. Unbounded, this loop let a single unrunnable project
#: burn 843 implementer calls in one day while 400 projects got none.
MAX_REPLAN_ROUNDS = 3

#: Ordered model ladder for the execution fix-loop (autonomous exhaustion
#: handling). When the fix-round cap is hit at one tier, the project bumps to
#: the next tier and retries the FULL cap with a different/stronger model.
#:
#:   tier 0 → "" (empty) means NO override: the implementer's REGISTERED default
#:            model (do not hardcode it here — the registry is the SSoT).
#:   tier 1 → a DIFFERENT capable FREE model (a free "second opinion"). Both
#:            qwen.qwen3.5-122b and openai.gpt-oss-120b are confirmed live + free
#:            on Dartmouth; gpt-oss-120b is the canonical second free model.
#:   tiers 2+ → OPTIONAL paid tiers, read at runtime from
#:            ``LLMXIVE_EXECUTION_PAID_TIERS`` (comma-separated model ids,
#:            DEFAULT EMPTY). A paid tier is usable ONLY when paid opt-in is on
#:            AND it passes the credit-budget guard; otherwise it is SKIPPED.
#:
#: This keeps the default behavior FREE-FIRST (tier0 → tier1 → re-plan); paid
#: escalation (e.g. haiku/sonnet/opus) is enabled later by config, no code change.
FREE_MODEL_TIERS: tuple[str, ...] = ("", "openai.gpt-oss-120b")

#: Env hook for OPTIONAL paid escalation tiers (comma-separated model ids).
EXECUTION_PAID_TIERS_ENV = "LLMXIVE_EXECUTION_PAID_TIERS"


def _paid_model_tiers() -> tuple[str, ...]:
    """Paid escalation tiers from the env hook (default empty)."""
    raw = os.environ.get(EXECUTION_PAID_TIERS_ENV, "").strip()
    if not raw:
        return ()
    return tuple(m.strip() for m in raw.split(",") if m.strip())


def model_tier_ladder() -> tuple[str, ...]:
    """The full ordered model ladder: free tiers then any configured paid tiers.

    Index = tier number; the value is a model-id OVERRIDE (``""`` = tier 0 =
    no override = the agent's registered default). Paid tiers are *listed* here
    so the tier index is stable; usability is gated separately by
    :func:`paid_tier_usable` (opt-in + credit budget).
    """
    return (*FREE_MODEL_TIERS, *_paid_model_tiers())


def paid_tier_usable(model: str) -> bool:
    """Whether a PAID escalation tier may be used right now.

    Requires the process-level paid opt-in AND headroom under the daily credit
    budget cap (the existing FREE-FIRST guard). Fails closed on any doubt.
    """
    if not model:
        return True  # tier 0 / free models never consult the paid guard
    try:
        from llmxive.backends.credits import paid_call_allowed, paid_opt_in_enabled

        if not paid_opt_in_enabled():
            return False
        allowed, _reason = paid_call_allowed(model)
        return bool(allowed)
    except Exception as exc:  # fail closed — never let the guard crash routing
        logger.warning("paid_tier_usable check failed for %r: %s", model, exc)
        return False


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


def model_tier(project_id: str, *, repo_root: Path | None = None) -> int:
    """Current execution-fix-loop model tier (default 0 = registered default)."""
    rec = load(project_id, repo_root=repo_root) or {}
    t = rec.get("model_tier", 0)
    return int(t) if isinstance(t, int) and t >= 0 else 0


def tier_model(tier: int) -> str:
    """The model-id OVERRIDE for ``tier`` (``""`` = no override = registered
    default). Out-of-range tiers clamp to the last ladder entry."""
    ladder = model_tier_ladder()
    if tier <= 0:
        return ladder[0]
    return ladder[min(tier, len(ladder) - 1)]


def execution_model_override(
    project_id: str,
    *,
    default_model: str,
    repo_root: Path | None = None,
) -> str:
    """Resolve the model the execution-fix-loop implementer should use NOW.

    Tier 0 (or any tier whose ladder entry is empty) → the agent's registered
    ``default_model``. A higher tier returns its ladder model id. A PAID tier
    that is not currently usable (opt-in off / over budget) falls back to the
    registered default rather than crash — the tier still ADVANCES (so the loop
    makes progress), it just doesn't get the paid model this run.
    """
    override = tier_model(model_tier(project_id, repo_root=repo_root))
    if not override:
        return default_model
    if override not in FREE_MODEL_TIERS and not paid_tier_usable(override):
        return default_model
    return override


def next_usable_tier(current: int) -> int | None:
    """The next tier ABOVE ``current`` whose model is usable, or None if none.

    Skips paid tiers that are not currently usable (opt-in off / over budget).
    Note: tier 0's model is the registered default, so a higher tier whose
    override happens to equal the default is the caller's concern — here we only
    skip UNUSABLE paid tiers (the registry default is not known to this layer;
    the dispatch resolver collapses a same-as-default override harmlessly).
    """
    ladder = model_tier_ladder()
    for t in range(current + 1, len(ladder)):
        model = ladder[t]
        if not model or model in FREE_MODEL_TIERS or paid_tier_usable(model):
            return t
    return None


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
    prior_tier = existing.get("model_tier", 0)
    prior_tier = int(prior_tier) if isinstance(prior_tier, int) and prior_tier >= 0 else 0
    prior_attempts = _nonneg_int(existing.get("total_attempts"))
    rec = {
        "project_id": project_id,
        "ok": bool(ok),
        "reason": reason[:2000],
        "artifacts": list(artifacts),
        "failures": [f[:600] for f in failures][:30],
        "fix_rounds": 0 if ok else prior_rounds + 1,
        # The model tier is owned by the routing layer's escalation/re-plan
        # transitions (bump_model_tier / reset_fix_loop) — record() must NOT
        # clobber it (the project stays on the escalated tier across rounds).
        "model_tier": prior_tier,
        # MONOTONIC churn counters. ``fix_rounds`` is reset by BOTH escalation and
        # re-plan, so it cannot answer "how much compute has this project burned?" —
        # and nothing else could either, which is why the outer re-plan loop ran
        # unbounded. These two survive those resets (cleared only by SUCCESS):
        #   total_attempts — every failed execution ever. The scheduler uses it to
        #     stop a churner from monopolising the matrix (see _order_within_stage).
        #   replan_rounds  — bumped by reset_fix_loop, the re-plan transition itself,
        #     so the routing layer can finally cap the outer loop.
        "total_attempts": 0 if ok else prior_attempts + 1,
        "replan_rounds": 0 if ok else _nonneg_int(existing.get("replan_rounds")),
        "updated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    d = _dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    _path(project_id, repo_root=repo_root).write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8"
    )
    return rec


def bump_model_tier(project_id: str, *, repo_root: Path | None = None) -> int:
    """MODEL ESCALATION: advance to the next USABLE model tier and RESET
    fix_rounds to 0, so the fix-loop retries the full cap with a different
    model. Returns the new tier. Raises if no higher usable tier exists — the
    caller (routing) must instead RE-PLAN (never escalate to a human)."""
    existing = load(project_id, repo_root=repo_root) or {}
    current = existing.get("model_tier", 0)
    current = int(current) if isinstance(current, int) and current >= 0 else 0
    nxt = next_usable_tier(current)
    if nxt is None:
        raise ValueError(
            f"{project_id}: no higher usable model tier above {current} "
            f"(ladder={model_tier_ladder()!r}) — caller must re-plan"
        )
    existing["model_tier"] = nxt
    existing["fix_rounds"] = 0  # fresh full cap at the new tier
    existing["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    existing.setdefault("project_id", project_id)
    d = _dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    _path(project_id, repo_root=repo_root).write_text(
        json.dumps(existing, indent=2) + "\n", encoding="utf-8"
    )
    return nxt


def _nonneg_int(v: Any) -> int:
    """Coerce a persisted counter to a non-negative int (0 for junk/missing)."""
    return v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else 0


def total_attempts(project_id: str, *, repo_root: Path | None = None) -> int:
    """Every failed execution this project has EVER had (cleared only by success).

    ``fix_rounds`` is reset by both escalation and re-plan, so it cannot say how much
    compute a project has burned. This can — and the scheduler uses it to stop a
    hopeless project from monopolising the worker matrix."""
    return _nonneg_int((load(project_id, repo_root=repo_root) or {}).get("total_attempts"))


def replan_rounds(project_id: str, *, repo_root: Path | None = None) -> int:
    """How many times this project has been RE-PLANNED out of the execution loop."""
    return _nonneg_int((load(project_id, repo_root=repo_root) or {}).get("replan_rounds"))


def reset_fix_loop(project_id: str, *, repo_root: Path | None = None) -> None:
    """Reset fix_rounds and model_tier to 0 — called on the RE-PLAN transition so the
    re-planned project starts the execution fix-loop clean (tier 0, round 0).

    BUMPS ``replan_rounds``, which this reset must NOT clear: it is the only memory
    that the project has already been all the way round the ladder. Without it the
    outer loop was UNBOUNDED — a project whose analysis simply cannot run climbed
    every tier, re-planned to a clean slate, and climbed them all again forever."""
    existing = load(project_id, repo_root=repo_root)
    if not existing:
        return
    existing["fix_rounds"] = 0
    existing["model_tier"] = 0
    existing["replan_rounds"] = _nonneg_int(existing.get("replan_rounds")) + 1
    existing["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    d = _dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    _path(project_id, repo_root=repo_root).write_text(
        json.dumps(existing, indent=2) + "\n", encoding="utf-8"
    )


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
    prior_tier = existing.get("model_tier", 0)
    prior_tier = int(prior_tier) if isinstance(prior_tier, int) and prior_tier >= 0 else 0
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
        "model_tier": prior_tier,  # preserved across offload transitions
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
    "EXECUTION_PAID_TIERS_ENV",
    "FREE_MODEL_TIERS",
    "MAX_EXECUTION_FIX_ROUNDS",
    "MAX_REPLAN_ROUNDS",
    "bump_model_tier",
    "clear_offload",
    "execution_model_override",
    "fix_rounds",
    "is_offload_pending",
    "is_ok",
    "load",
    "model_tier",
    "model_tier_ladder",
    "next_usable_tier",
    "offload_state",
    "paid_tier_usable",
    "record",
    "record_offload",
    "replan_rounds",
    "reset_fix_loop",
    "tier_model",
    "total_attempts",
]
