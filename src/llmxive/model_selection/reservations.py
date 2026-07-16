"""Credit-reservation lifecycle over the strict-CAS ledger (spec 026, slice 1B /
FR-016).

A paid call RESERVES its ``worst_case_credits`` in the authoritative ledger
(:mod:`llmxive.model_selection.ledger_transport`) BEFORE the provider call so that
concurrent paid calls — same-process AND across separate runners — cannot
collectively exceed the fractional cap. The reservation state machine:

    open ──(call returns)──▶ settling ──(charge observed / conservative)──▶ reconciled

- ``open`` and ``settling`` BOTH count against headroom (``counting_reservations``)
  — a reservation is NEVER released at call-return (that would leak headroom during
  Dartmouth's settlement lag); a call that failed *after* reaching the provider
  keeps its worst-case hold until reconciliation.
- The lease is a function of ``ExecutionOptions.deadline_s`` (never a fixed TTL
  that could expire mid-call), refreshed by a background heartbeat owner while the
  blocking call runs, with a separate settlement timeout.
- A crashed in-flight owner (lease expired, no heartbeat) is CONSERVATIVELY
  settled (retained), NOT released.
- Reconciliation is deterministic across Dartmouth's daily reset: each reservation
  records its ``budget_epoch`` (``budget_reset_at``) + ``settlement_baseline``
  (spend at reservation), and a prior-epoch reservation is discarded at reset (not
  carried into the new day's headroom).

The headroom predicate ``spend + counting + worst_case ≤ effective_cap`` lives in
:func:`_admits` here (the ONE home of the reservation formula). Slice 3 wires this
together with the pre-call ``credits.paid_call_allowed`` check (twice-checked
paid, FR-011) — the guard is extended to own it there, not duplicated.
"""

from __future__ import annotations

import itertools
import logging
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from llmxive.model_selection.ledger_transport import (
    LedgerDenied,
    append_event,
    read_events,
)

logger = logging.getLogger(__name__)

STATE_OPEN = "open"
STATE_SETTLING = "settling"
STATE_RECONCILED = "reconciled"
#: open + settling both consume headroom until a charge is observed.
COUNTING_STATES = frozenset({STATE_OPEN, STATE_SETTLING})

#: Lease margin ADDED to the call deadline so a single lease covers the whole call
#: even before the first heartbeat; the heartbeat owner then refreshes it.
DEFAULT_LEASE_MARGIN_S = 60.0
#: How long a ``settling`` reservation waits for its charge to appear before the
#: sweeper conservatively finalizes it (Dartmouth's settlement lag).
DEFAULT_SETTLEMENT_TIMEOUT_S = 3600.0
_DEFAULT_DEADLINE_S = 360.0  # a reasoning call's default wall-clock deadline
_warned_local_reserve = False  # one-shot guard for the remote=None warning (C7)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


@dataclass(frozen=True)
class Reservation:
    """The projected state of one reservation (folded from its events)."""

    reservation_id: str
    worst_case_credits: float
    state: str
    model: str
    budget_epoch: str  # the provider budget_reset_at at reservation time
    settlement_baseline: float  # provider spend observed when reserved
    created_at: str
    lease_expires_at: str
    last_heartbeat_at: str

    @property
    def counts(self) -> bool:
        return self.state in COUNTING_STATES


def lease_duration_for(deadline_s: float | None, *, margin_s: float = DEFAULT_LEASE_MARGIN_S) -> float:
    """Lease length derived from the call deadline (FR-016: never a fixed TTL that
    could expire mid-call). Falls back to the default reasoning deadline."""
    return (deadline_s if deadline_s and deadline_s > 0 else _DEFAULT_DEADLINE_S) + margin_s


# --------------------------------------------------------------------------- #
# Projection: fold the append-only event log into current reservation state.
# --------------------------------------------------------------------------- #


#: Causal precedence for tie-breaking events that share a ``ts`` (e.g. tests that
#: inject one clock, or two events appended in the same instant). ``ts`` dominates
#: (it is monotonic per reservation in production — you cannot settle before you
#: reserve); this only orders genuine ties.
_TYPE_RANK = {STATE_OPEN: 0, "heartbeat": 1, STATE_SETTLING: 2, STATE_RECONCILED: 3}


def project(events: Iterable[dict]) -> dict[str, Reservation]:
    """Fold the event log into ``{reservation_id: Reservation}``. Events are
    applied in (ts, causal-type-rank, event_id) order; ``open`` seeds the record,
    ``heartbeat`` extends the lease, ``settling``/``reconciled`` advance the
    state."""
    ordered = sorted(
        events,
        key=lambda e: (e.get("ts", ""), _TYPE_RANK.get(e.get("type"), 9), e.get("event_id", "")),
    )
    state: dict[str, dict] = {}
    for e in ordered:
        rid = e.get("reservation_id")
        etype = e.get("type")
        if rid is None or etype is None:
            continue
        if etype == STATE_OPEN and rid not in state:
            # CREATE-ONLY (C12): a duplicate `open` (e.g. a cross-runner retry whose
            # local ref was stale when the idempotency pre-check ran) must NOT
            # overwrite an already-advanced reservation — a later-ts open would
            # otherwise regress `settling`→`open` and reset created_at/baseline,
            # corrupting reconciliation attribution.
            state[rid] = {
                "reservation_id": rid,
                "worst_case_credits": float(e.get("worst_case_credits", 0.0)),
                "state": STATE_OPEN,
                "model": str(e.get("model", "")),
                "budget_epoch": str(e.get("budget_epoch", "")),
                "settlement_baseline": float(e.get("settlement_baseline", 0.0)),
                "created_at": str(e.get("created_at", e.get("ts", ""))),
                "lease_expires_at": str(e.get("lease_expires_at", "")),
                "last_heartbeat_at": str(e.get("ts", "")),
            }
        elif rid in state:
            if etype == "heartbeat":
                # keep the LATEST (max) lease + heartbeat timestamp
                new_lease = str(e.get("lease_expires_at", ""))
                if new_lease > state[rid]["lease_expires_at"]:
                    state[rid]["lease_expires_at"] = new_lease
                state[rid]["last_heartbeat_at"] = str(e.get("ts", ""))
            elif etype == STATE_SETTLING and state[rid]["state"] == STATE_OPEN:
                state[rid]["state"] = STATE_SETTLING
            elif etype == STATE_RECONCILED:
                state[rid]["state"] = STATE_RECONCILED
    return {rid: Reservation(**rec) for rid, rec in state.items()}


def counting_total(reservations: Iterable[Reservation], *, epoch: str) -> float:
    """Sum of worst-case credits held by ``open``+``settling`` reservations in the
    CURRENT epoch — the amount bridging Dartmouth's lagged ``spend``. Prior-epoch
    reservations are excluded (discarded at the daily reset)."""
    return sum(r.worst_case_credits for r in reservations if r.counts and r.budget_epoch == epoch)


def _admits(*, effective_cap: float, fresh_spend: float, counting: float, worst_case: float) -> bool:
    """THE reservation headroom formula (FR-011): a new reservation fits iff fresh
    spend + already-counting reservations + this call's worst case stays within the
    fractional cap."""
    return fresh_spend + counting + worst_case <= effective_cap


# --------------------------------------------------------------------------- #
# Mutations — each is one strict-CAS-appended event under an idempotency key.
# --------------------------------------------------------------------------- #


def reserve(
    repo: Path,
    *,
    reservation_id: str,
    worst_case_credits: float,
    model: str,
    effective_cap: float,
    budget_epoch: str,
    fresh_spend_fn: Callable[[], float],
    lease_expires_at: datetime,
    now: datetime | None = None,
    remote: str | None = None,
) -> Reservation:
    """Open a reservation for ``worst_case_credits`` under strict CAS. The headroom
    predicate is re-evaluated against FRESH spend + the freshly-fetched counting
    reservations on every CAS attempt (FR-011/FR-016). Raises
    :class:`ledger_transport.LedgerDenied` if there is no headroom. Idempotent: a
    re-``reserve`` of an already-counting id is admitted without double-counting.
    """
    now = now or _utcnow()
    if remote is None:
        global _warned_local_reserve
        if not _warned_local_reserve:
            _warned_local_reserve = True
            logger.warning(
                "reservation opened with remote=None — LOCAL ledger only, NO cross-runner "
                "headroom protection (C7). Production/slice-3 wiring MUST pass a real remote."
            )
    # Idempotency: a reservation already counting locally is returned as-is (never
    # re-append an `open`, which would regress a `settling` record back to `open`).
    # The CAS predicate below still guards the concurrent same-id case.
    existing = project(read_events(repo)).get(reservation_id)
    if existing is not None and existing.counts:
        return existing
    event = {
        "event_id": f"{reservation_id}-open",
        "reservation_id": reservation_id,
        "type": STATE_OPEN,
        "worst_case_credits": worst_case_credits,
        "model": model,
        "budget_epoch": budget_epoch,
        "settlement_baseline": fresh_spend_fn(),
        "created_at": now.isoformat(),
        "lease_expires_at": lease_expires_at.isoformat(),
        "ts": now.isoformat(),  # explicit logical time (do NOT rely on wall-clock default)
    }

    def predicate(events: list[dict]) -> tuple[bool, str]:
        current = project(events)
        existing = current.get(reservation_id)
        if existing is not None and existing.counts:
            return True, "idempotent: already reserved"
        counting = counting_total(current.values(), epoch=budget_epoch)
        spend = fresh_spend_fn()  # FRESH, cache-bypassing each attempt
        if _admits(
            effective_cap=effective_cap, fresh_spend=spend, counting=counting, worst_case=worst_case_credits
        ):
            return True, "admitted"
        return (
            False,
            f"reservation {reservation_id!r} denied: fresh spend {spend:.2f} + counting "
            f"{counting:.2f} + call {worst_case_credits:.2f} exceeds cap {effective_cap:.2f}",
        )

    append_event(repo, event, remote=remote, predicate=predicate)
    return project(read_events(repo))[reservation_id]


_HB_SEQ = itertools.count()


def heartbeat(
    repo: Path,
    reservation_id: str,
    *,
    lease_expires_at: datetime,
    now: datetime | None = None,
    remote: str | None = None,
) -> None:
    """Append a heartbeat that extends the reservation's lease (no headroom
    predicate — a heartbeat never changes the reserved amount)."""
    now = now or _utcnow()
    append_event(
        repo,
        {
            "event_id": f"{reservation_id}-hb-{next(_HB_SEQ)}",
            "reservation_id": reservation_id,
            "type": "heartbeat",
            "lease_expires_at": lease_expires_at.isoformat(),
            "ts": now.isoformat(),
        },
        remote=remote,
    )


def settle(
    repo: Path,
    reservation_id: str,
    *,
    now: datetime | None = None,
    remote: str | None = None,
) -> None:
    """Transition ``open → settling`` when the call returns (success OR failure
    after reaching the provider). The hold is RETAINED — never released here."""
    now = now or _utcnow()
    append_event(
        repo,
        {
            "event_id": f"{reservation_id}-settling",
            "reservation_id": reservation_id,
            "type": STATE_SETTLING,
            "ts": now.isoformat(),
        },
        remote=remote,
    )


def _reconcile_one(
    repo: Path, reservation_id: str, *, now: datetime, remote: str | None
) -> None:
    append_event(
        repo,
        {
            "event_id": f"{reservation_id}-reconciled",
            "reservation_id": reservation_id,
            "type": STATE_RECONCILED,
            "ts": now.isoformat(),
        },
        remote=remote,
    )


# --------------------------------------------------------------------------- #
# Heartbeat owner — renews the lease during the blocking provider call.
# --------------------------------------------------------------------------- #


class ReservationLease:
    """Context manager owning a background daemon-thread heartbeat for the duration
    of a blocking provider call (matching the codebase's ``invoke_with_deadline``
    daemon-thread precedent — a daemon never blocks interpreter exit). It refreshes
    the lease every ``interval_s`` and is torn down on ``__exit__``.
    """

    def __init__(
        self,
        repo: Path,
        reservation_id: str,
        *,
        interval_s: float,
        lease_duration_s: float,
        remote: str | None = None,
        now_fn: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._repo = repo
        self._rid = reservation_id
        self._interval = max(0.1, interval_s)
        self._lease_duration = lease_duration_s
        self._remote = remote
        self._now_fn = now_fn
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _run(self) -> None:
        from datetime import timedelta

        while not self._stop.wait(self._interval):
            try:
                heartbeat(
                    self._repo,
                    self._rid,
                    lease_expires_at=self._now_fn() + timedelta(seconds=self._lease_duration),
                    now=self._now_fn(),
                    remote=self._remote,
                )
            except Exception as exc:  # a heartbeat failure must not crash the call
                logger.warning("reservation %s heartbeat failed: %s", self._rid, exc)

    def __enter__(self) -> ReservationLease:
        self._thread = threading.Thread(target=self._run, name=f"lease-{self._rid}", daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self._interval * 2)


# --------------------------------------------------------------------------- #
# Reconciler / sweeper — the maintenance entry point (CLI + workflow step).
# --------------------------------------------------------------------------- #


def reconcile_settled(
    repo: Path,
    *,
    observed_spend: float,
    epoch: str,
    now: datetime | None = None,
    remote: str | None = None,
) -> list[str]:
    """Attribution-prefix reconciliation (FR-016, rev-3): an observed provider-spend
    delta MUST NOT accidentally reconcile multiple overlapping reservations.

    Order the current-epoch ``settling`` reservations deterministically by
    ``(created_at, reservation_id)`` and reconcile ONLY the PREFIX whose CUMULATIVE
    reserved amount is fully covered by ``(observed_spend - settlement_baseline)``
    (the baseline of the earliest reservation, == the spend before the batch
    charged). Every reservation not fully covered stays ``settling`` (still
    counting) until more spend is observed or the daily reset. A single reservation
    is NEVER partially reconciled. Returns the reconciled ids in order.

    KNOWN BOUND (C1, accepted 2026-07-16): reconciling against LAGGED AGGREGATE
    spend is inherently approximate — two reservations with the SAME baseline are
    indistinguishable by ``(baseline, worst_case)``. When one of them is already
    reconciled, its landed charge inflates ``covered`` for a later batch, so a
    still-``settling`` sibling can be reconciled before ITS charge lands (created_at
    order != charge order). The window is NARROW (shared baseline + a reconciled
    sibling + a slow, not-yet-charged straggler) and BOUNDED by one ``worst_case``;
    it is backstopped by the FRESH-spend re-check at the next ``reserve`` (the
    straggler's charge, once it lands, is reflected in ``spend``) and swept by the
    daily-epoch reset. A stricter fix (discount reconciled ``worst_case`` from
    ``covered``, or all-or-nothing per batch) was considered and deliberately not
    taken — the maintainer accepted the documented bound over the added complexity /
    slower headroom reclaim.
    """
    now = now or _utcnow()
    current = project(read_events(repo))
    batch = sorted(
        (r for r in current.values() if r.state == STATE_SETTLING and r.budget_epoch == epoch),
        key=lambda r: (r.created_at, r.reservation_id),
    )
    if not batch:
        return []
    baseline = min(r.settlement_baseline for r in batch)
    covered = max(0.0, observed_spend - baseline)
    cumulative = 0.0
    reconciled: list[str] = []
    for r in batch:
        cumulative += r.worst_case_credits
        if cumulative <= covered:
            _reconcile_one(repo, r.reservation_id, now=now, remote=remote)
            reconciled.append(r.reservation_id)
        else:
            break  # prefix rule: this + all following stay settling
    return reconciled


def sweep(
    repo: Path,
    *,
    observed_spend: float,
    current_epoch: str,
    now: datetime | None = None,
    remote: str | None = None,
    settlement_timeout_s: float = DEFAULT_SETTLEMENT_TIMEOUT_S,
) -> dict[str, list[str]]:
    """The maintenance sweep (a CLI subcommand + a maintenance-workflow step):

    1. **crashed in-flight** — an ``open`` reservation whose lease has EXPIRED (no
       live owner heartbeating) is CONSERVATIVELY settled (moved to ``settling``,
       retaining the hold), NEVER released.
    2. **daily-epoch reset** — a non-``reconciled`` reservation from a PRIOR epoch
       is discarded (finalized as ``reconciled``) so it no longer counts.
    3. **reconcile** — the current-epoch ``settling`` batch is reconciled against
       the freshly-observed spend via the attribution-prefix rule.

    Returns the ids affected per phase.
    """
    now = now or _utcnow()
    current = project(read_events(repo))

    conservatively_settled: list[str] = []
    for r in current.values():
        if r.state == STATE_OPEN and r.budget_epoch == current_epoch:
            expired = bool(r.lease_expires_at) and _parse(r.lease_expires_at) < now
            if expired:
                settle(repo, r.reservation_id, now=now, remote=remote)
                conservatively_settled.append(r.reservation_id)

    discarded: list[str] = []
    for r in current.values():
        if r.state != STATE_RECONCILED and r.budget_epoch != current_epoch:
            _reconcile_one(repo, r.reservation_id, now=now, remote=remote)
            discarded.append(r.reservation_id)

    reconciled = reconcile_settled(
        repo, observed_spend=observed_spend, epoch=current_epoch, now=now, remote=remote
    )
    return {
        "conservatively_settled": conservatively_settled,
        "discarded_prior_epoch": discarded,
        "reconciled": reconciled,
    }


def outstanding_headroom_consumption(repo: Path, *, epoch: str) -> float:
    """The current counting-reservation total on the authoritative ledger — what
    slice 3's pre-call guard subtracts from the fractional cap."""
    return counting_total(project(read_events(repo)).values(), epoch=epoch)


__all__ = [
    "COUNTING_STATES",
    "DEFAULT_LEASE_MARGIN_S",
    "DEFAULT_SETTLEMENT_TIMEOUT_S",
    "STATE_OPEN",
    "STATE_RECONCILED",
    "STATE_SETTLING",
    "LedgerDenied",
    "Reservation",
    "ReservationLease",
    "counting_total",
    "heartbeat",
    "lease_duration_for",
    "outstanding_headroom_consumption",
    "project",
    "reconcile_settled",
    "reserve",
    "settle",
    "sweep",
]
