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
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from llmxive.config import repo_root as _repo_root
from llmxive.model_selection.types import RequirementOverrides
from llmxive.state._io import atomic_write_text

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

#: Ordered escalation ladder for the execution fix-loop (autonomous exhaustion
#: handling), expressed as REQUIREMENT CONSTRAINTS — never model-id literals
#: (spec 026 slice 6/7). When the fix-round cap is hit at one tier, the project
#: bumps to the next tier and retries the FULL cap under a stricter constraint;
#: each rung is resolved to a :class:`RequirementOverrides` at dispatch so the
#: unified selector (not this layer) picks the actual model from the live catalog.
#:
#:   tier 0 → the free-only base requirement (no override).
#:   tier 1 → a free "second opinion": ``exclude_leader`` drops whatever
#:            ``select`` ranks FIRST so the policy's next-best FREE model leads
#:            (SSoT — no id hardcoded here, no model id threaded into dispatch).
#:   paid rung → a single OPTIONAL paid escalation, appended only when paid
#:            escalation is enabled (``LLMXIVE_EXECUTION_PAID_ESCALATION``) AND
#:            usable NOW (opt-in + fresh credit headroom); otherwise SKIPPED.
#:
#: This keeps the default behavior FREE-FIRST (tier0 → tier1 → re-plan); paid
#: escalation is enabled later by config, no code change and no model-id pin.

#: Env: enable the single PAID escalation rung (default off). Booleans use the
#: canonical {"1","true","yes","on"} idiom (mirrors backends.credits).
PAID_ESCALATION_ENV = "LLMXIVE_EXECUTION_PAID_ESCALATION"
#: Deprecated: a comma-separated model-id list. Model-ids are NO LONGER honored;
#: any nonempty value collapses to ONE paid rung (with a one-time warning). Removal
#: tracked for slice 8.
_LEGACY_PAID_TIERS_ENV = "LLMXIVE_EXECUTION_PAID_TIERS"
_BOOL_TRUE = {"1", "true", "yes", "on"}
_BOOL_FALSE = {"0", "false", "no", "off"}
_LEGACY_WARNED = False


@dataclass(frozen=True)
class TierConstraint:
    """One escalation rung as REQUIREMENT overrides — never a model id (spec 026
    slice 6; slice 7 removed the last model-id argument)."""

    allow_paid: bool = False
    exclude_leader: bool = False
    require_paid: bool = False
    max_credits: int | None = None

    @property
    def is_paid(self) -> bool:
        return self.allow_paid or self.require_paid

    def to_overrides(self) -> RequirementOverrides:
        return RequirementOverrides(
            allow_paid=self.allow_paid,  # ALWAYS explicit (incl. False)
            require_paid=self.require_paid,
            exclude_leader=self.exclude_leader,
            max_credits=self.max_credits,
        )


#: The free rungs (indices stable): tier 0 = base free; tier 1 = free second opinion
#: (exclude whatever ``select`` ranks first so the policy's next-best free leads).
_FREE_RUNGS: tuple[TierConstraint, ...] = (
    TierConstraint(allow_paid=False),
    TierConstraint(allow_paid=False, exclude_leader=True),
)
#: The single paid rung appended when paid escalation is enabled.
_PAID_RUNG = TierConstraint(allow_paid=True, require_paid=True)


def _paid_escalation_enabled() -> bool:
    """Exact env precedence (spec 026 slice 6, round-2 #4):
    (a) PAID_ESCALATION present → true=on, false/0=off, invalid=warn+off; legacy ignored.
    (b) else legacy PAID_TIERS nonempty → on (one rung) + one-time deprecation warning.
    (c) else off."""
    global _LEGACY_WARNED
    raw = os.environ.get(PAID_ESCALATION_ENV)
    if raw is not None:
        v = raw.strip().lower()
        if v in _BOOL_TRUE:
            return True
        if v in _BOOL_FALSE or v == "":
            return False
        logger.warning(
            "%s=%r is not a recognized boolean — disabling paid escalation (fail closed)",
            PAID_ESCALATION_ENV, raw,
        )
        return False
    legacy = os.environ.get(_LEGACY_PAID_TIERS_ENV, "").strip()
    if legacy:
        if not _LEGACY_WARNED:
            logger.warning(
                "%s is deprecated; model-ids are no longer honored — collapsing to ONE "
                "paid escalation rung. Use %s=1 instead.",
                _LEGACY_PAID_TIERS_ENV, PAID_ESCALATION_ENV,
            )
            _LEGACY_WARNED = True
        return True
    return False


def model_tier_ladder() -> tuple[TierConstraint, ...]:
    """The ordered escalation ladder as constraints (index = tier). Two free rungs,
    plus ONE paid rung when paid escalation is enabled."""
    return (*_FREE_RUNGS, _PAID_RUNG) if _paid_escalation_enabled() else _FREE_RUNGS


def tier_constraint(tier: int) -> TierConstraint:
    """The constraint for ``tier``. Corrupt/out-of-range (incl. bool/float/str) →
    tier-0 FREE-ONLY (NEVER the last/paid rung — invalid state must not broaden
    spending authority)."""
    ladder = model_tier_ladder()
    t = _nonneg_int(tier)
    if t == 0 or t >= len(ladder):
        return ladder[0]
    return ladder[t]


def paid_tier_usable() -> bool:
    """Coarse gate: is paid escalation globally enabled AND is there fresh daily
    headroom NOW? Delegates ALL arithmetic to the canonical credits helper
    (Constitution I). Fails closed on any error."""
    try:
        from llmxive.backends.credits import fresh_paid_headroom_available

        ok, _reason = fresh_paid_headroom_available()
        return bool(ok)
    except Exception as exc:  # never let the guard crash routing
        logger.warning("paid_tier_usable check failed: %s", exc)
        return False


def tier_overrides(project_id: str, *, repo_root: Path | None = None) -> RequirementOverrides:
    """The RequirementOverrides for the project's CURRENT model tier."""
    return tier_constraint(model_tier(project_id, repo_root=repo_root)).to_overrides()


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
    return _nonneg_int(rec.get("fix_rounds"))


def model_tier(project_id: str, *, repo_root: Path | None = None) -> int:
    """Current execution-fix-loop model tier (default 0 = registered default)."""
    rec = load(project_id, repo_root=repo_root) or {}
    return _nonneg_int(rec.get("model_tier"))


def next_usable_tier(current: int, *, free_only: bool = False) -> int | None:
    """The next tier ABOVE ``current`` whose rung is usable, or None. A paid rung
    (``constraint.is_paid``) is skipped when ``free_only`` OR paid is not usable now.

    ``free_only`` refuses to climb onto a PAID rung at all. Used for FABRICATION
    failures: the deterministic fabrication guard fires on the code's OUTPUT
    regardless of which model wrote it, so paying for a stronger model to
    re-attempt fabrication is pure waste (PROJ-284 reached a paid Claude tier still
    generating synthetic brain-imaging data). Free escalation is cheap and can
    occasionally help; paid escalation for fabrication never can.
    """
    ladder = model_tier_ladder()
    for t in range(_nonneg_int(current) + 1, len(ladder)):
        c = ladder[t]
        if not c.is_paid:
            return t
        if free_only:
            continue
        if paid_tier_usable():
            return t
    return None


def record(
    project_id: str,
    *,
    ok: bool,
    reason: str,
    artifacts: list[str],
    failures: list[str],
    failure_class: str | None = None,
    evidence: list[str] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Persist one execution attempt. Bumps ``fix_rounds`` on failure (so the
    bounded auto-fix loop terminates), resets it to 0 on success.

    ``failure_class`` is the durable :class:`llmxive.execution.failure_class.FailureClass`
    value (compute_env / data_unreachable / fabrication / execution_bug /
    unknown) the runner classified this failure as — persisted so downstream
    re-plan feedback and terminal routing branch on the REAL cause instead of
    re-parsing ``reason``/``failures`` strings (issue #1139 P1-2). ``evidence``
    is the short list of matched signature strings that justified the class.
    Both are cleared on success.
    """
    existing = load(project_id, repo_root=repo_root) or {}
    prior_rounds = _nonneg_int(existing.get("fix_rounds"))
    prior_tier = _nonneg_int(existing.get("model_tier"))
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
        # Durable failure classification (issue #1139 P1-2): the runner already
        # knows whether this was a compute-env wall, an unreachable data source,
        # fabrication, or an ordinary code bug — persist it so re-plan feedback
        # and terminal routing branch on the real cause, not a re-parse of
        # `reason`. Cleared on success.
        "failure_class": None if ok else (failure_class or None),
        "evidence": [] if ok else [str(e)[:600] for e in (evidence or [])][:20],
        "updated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    d = _dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        _path(project_id, repo_root=repo_root),
        json.dumps(rec, indent=2) + "\n",
    )
    return rec


def bump_model_tier(
    project_id: str, *, repo_root: Path | None = None, free_only: bool = False
) -> int:
    """MODEL ESCALATION: advance to the next USABLE model tier and RESET
    fix_rounds to 0, so the fix-loop retries the full cap with a different
    model. Returns the new tier. Raises if no higher usable tier exists — the
    caller (routing) must instead RE-PLAN (never escalate to a human).

    ``free_only`` refuses to climb onto a paid tier (see :func:`next_usable_tier`);
    the caller passes it for FABRICATION failures, where a paid model cannot help."""
    existing = load(project_id, repo_root=repo_root) or {}
    current = _nonneg_int(existing.get("model_tier"))
    nxt = next_usable_tier(current, free_only=free_only)
    if nxt is None:
        raise ValueError(
            f"{project_id}: no higher usable model tier above {current} "
            f"(ladder={model_tier_ladder()!r}, free_only={free_only}) — caller must re-plan"
        )
    existing["model_tier"] = nxt
    existing["fix_rounds"] = 0  # fresh full cap at the new tier
    existing["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    existing.setdefault("project_id", project_id)
    d = _dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        _path(project_id, repo_root=repo_root),
        json.dumps(existing, indent=2) + "\n",
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
    atomic_write_text(
        _path(project_id, repo_root=repo_root),
        json.dumps(existing, indent=2) + "\n",
    )


def record_offload(
    project_id: str,
    *,
    status: str,
    kernel_ref: str,
    reason: str | None = None,
    evidence: list[str] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Persist the async GPU-offload tri-state (issue #367) on the record.

    ``status`` is one of ``submitted|running|retrieved|failed``. CRUCIAL: this
    NEVER bumps ``fix_rounds`` — a pending offload is NOT a failure, so the
    bounded auto-fix loop must not advance and the project must not escalate to
    human_input_needed while a kernel is in flight (it stays IN_PROGRESS and
    keeps polling). The rest of the execution record (ok, reason, artifacts,
    failures, fix_rounds) is PRESERVED untouched.

    ``reason``/``evidence`` (issue #1139 residual, AP4): when a completed offload
    bundle FAILS the semantic gate (fabrication/hollow/no-deliverable) — or ends
    in a terminal error — the caller passes the gate's diagnosis so the durable
    offload sub-record carries WHY it failed, not just the bare ``failed``
    status. Only meaningful for ``status='failed'``; omitted for pending/retrieved
    transitions.
    """
    existing = load(project_id, repo_root=repo_root) or {}
    prior_rounds = _nonneg_int(existing.get("fix_rounds"))
    prior_tier = _nonneg_int(existing.get("model_tier"))
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
            # Durable failure diagnosis (issue #1139 AP4): why the bundle failed
            # the semantic gate / how the kernel terminated. Empty for the
            # pending/retrieved transitions that carry no failure.
            "reason": (reason or "") if status == "failed" else "",
            "evidence": (
                [str(e)[:600] for e in (evidence or [])][:20]
                if status == "failed"
                else []
            ),
        },
        "updated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    d = _dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        _path(project_id, repo_root=repo_root),
        json.dumps(rec, indent=2) + "\n",
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
    atomic_write_text(
        _path(project_id, repo_root=repo_root),
        json.dumps(existing, indent=2) + "\n",
    )


__all__ = [
    "MAX_EXECUTION_FIX_ROUNDS",
    "MAX_REPLAN_ROUNDS",
    "PAID_ESCALATION_ENV",
    "TierConstraint",
    "bump_model_tier",
    "clear_offload",
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
    "tier_constraint",
    "tier_overrides",
    "total_attempts",
]
