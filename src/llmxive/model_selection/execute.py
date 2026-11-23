"""Execution adapter (spec 026, slice 3, US3 / FR-010 / FR-011 / FR-016).

``execute(chain, messages, *, options, backend_factory)`` walks the ordered
:class:`ModelChain` that ``select`` produced, applying ``ExecutionOptions``
uniformly to every candidate and preserving ALL of the router's existing
safeguards — it NEVER re-ranks. Each candidate is one call to the slice-1A
one-candidate primitive (:func:`router.chat_one_candidate`, which keeps the
per-model breaker + deadline + bounded same-model retry); the per-candidate
TERMINAL outcome is classified by :func:`router.disposition_of` into exactly one
of the three plan outcomes:

- **skip-candidate** (a paid-guard denial, or a candidate we could not safely
  reserve) → advance to the next candidate;
- **retry/advance** (a transient failure / model-down / breaker-open) → advance;
- **abort-chain** (a request-level permanent refusal) → stop and re-raise.

**Fail-fast (FR-010):** before any call, the ACTUAL messages are re-checked
against the chain's ``call_budget`` via :func:`tokens.fits_budget` (the priced
cost bound is otherwise invalid) — using the SAME hard estimator selection
priced against.

**Twice-checked paid (FR-011) + reservation ledger (FR-016):** a paid candidate
is admitted a SECOND time immediately before the call via the extended
:func:`credits.paid_call_allowed` (reusing the ONE ``reservations.admits``
formula and ``reservations.outstanding_headroom_consumption``), fails closed if
the chain's credit snapshot was not ``live`` (C6), then RESERVES
``worst_case_credits x retries`` (the retry envelope — the primitive makes up to
``retries`` provider attempts) in the authoritative strict-CAS ledger under a
background heartbeat lease. The hold is RETAINED (``settle`` → ``settling``) on
return — success OR failure — never released at call-return (the reconciler /
sweeper finalizes it against observed spend). Free candidates touch none of this.

**Funded (spec 027):** a Hugging Face candidate reserves ``worst_case x 1`` (USD) on
the funded ledger, is dispatched once, and is reconciled with its real charge before
``execute`` moves on — see :func:`execute`.
"""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from collections.abc import Callable, Iterable
from contextlib import nullcontext
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path

from llmxive.backends.base import BaseBackend, ChatMessage, ChatResponse
from llmxive.backends.hf_budget import reserve_funded, settle_funded
from llmxive.backends.huggingface import PreInferenceRejection, request_was_sent
from llmxive.backends.router import (
    CandidateDisposition,
    chat_one_candidate,
    disposition_of,
    make_backend,
)
from llmxive.model_selection.attempt_hooks import (
    CandidateOutcome,
    DispatchCompleted,
    DispatchStarted,
    ReservationAuthority,
    ReservationOpened,
    RouteAudit,
    RouteAuditError,
    RouteReplayError,
    emit_audit,
)
from llmxive.model_selection.ledger_transport import (
    LedgerConfig,
    LedgerDenied,
    LedgerError,
    funded_ledger_config_from_env,
    ledger_config_from_env,
)
from llmxive.model_selection.reservations import (
    STATE_OPEN,
    CreditObservation,
    Reservation,
    ReservationLease,
    lease_duration_for,
    outstanding_headroom_consumption,
    reserve,
    settle,
)
from llmxive.model_selection.tokens import fits_budget
from llmxive.model_selection.types import (
    USD_TO_CREDITS,
    Candidate,
    ExecutionOptions,
    FundedGuardSnapshot,
    ModelChain,
    ModelRef,
)

logger = logging.getLogger(__name__)

#: Characters allowed in a ledger reservation id (matches ledger_transport's
#: validation ``^[A-Za-z0-9._-]+$``, C9); model ids carry ``/`` ``:`` ``.`` so
#: they MUST be sanitized before use as an event path component.
_UNSAFE_ID = re.compile(r"[^A-Za-z0-9._-]")


class ChainExhausted(RuntimeError):
    """Every candidate was skipped or advanced without a request-level abort and
    none succeeded — the chain is exhausted (distinct from ``select``'s
    ``ModelUnavailable``, which means nothing was ELIGIBLE)."""


@dataclass(frozen=True)
class ExecutionResult:
    """The outcome of a successful :func:`execute`: the provider ``response``, the
    ``model_ref`` that produced it, the credits ``reserved`` for it (0 for free),
    per-candidate ``notes`` (skips / advances that preceded success), and the
    winning candidate's ledger ``reservation_id`` (``None`` for a free winner —
    FR-033a: the lane attributes settled Attempt cost by this id; a funded winner's
    id names a hold on the funded ledger, not the Dartmouth credit ledger).
    ``reserved_credits`` is always in credits (1 credit = $0.001); for a funded winner
    the hold actually on the funded ledger is in USD and is ``reserved_usd``
    (``None`` otherwise). ``charged_usd`` is the real USD charge settled for a funded
    winner (also set as ``response.cost_estimate_usd``); ``None`` for a free or paid
    winner."""

    response: ChatResponse
    model_ref: ModelRef
    reserved_credits: float
    notes: tuple[str, ...]
    reservation_id: str | None = None
    charged_usd: float | None = None
    reserved_usd: float | None = None


def _sanitize_reservation_id(model_id: str, call_id: str) -> str:
    """A ledger-safe, per-call reservation id derived from the model + a unique
    call token (C9: model ids contain ``/``/``:``/``.``)."""
    return f"{_UNSAFE_ID.sub('-', model_id)}-{_UNSAFE_ID.sub('-', call_id)}"


def _default_credit_observer(
    balance_fetch: Callable[[], object] | None,
) -> Callable[[], CreditObservation]:
    """A fresh, cache-bypassing :class:`CreditObservation` builder for ``reserve``
    (called on every CAS attempt), reusing the canonical credit helpers."""

    def observe() -> CreditObservation:
        from llmxive.backends.credits import budget_fraction, fetch_credit_balance

        bal = (balance_fetch or fetch_credit_balance)()
        return CreditObservation(
            spend=bal.spend,
            effective_cap=budget_fraction() * bal.max_budget,
            budget_epoch=bal.budget_reset_at,
        )

    return observe


def _open_paid_reservation(
    candidate: Candidate,
    chain: ModelChain,
    *,
    options: ExecutionOptions,
    retries: int,
    ledger_repo: Path | None,
    ledger_config: LedgerConfig | None,
    credit_observer: Callable[[], CreditObservation] | None,
    balance_fetch: Callable[[], object] | None,
    now: datetime,
    call_id: str,
    reservation_authority: ReservationAuthority | None = None,
) -> tuple[str | None, float, str | None]:
    """Twice-check + reserve a paid candidate. Returns
    ``(reservation_id, reserved_credits, skip_reason)`` — exactly one of
    ``reservation_id`` / ``skip_reason`` is non-None. A ``skip_reason`` means the
    candidate is fail-closed skipped (advance the chain), never an abort.

    ``reservation_authority``, when given, is the Attempt-budget gate (FR-033b)
    consulted BEFORE the 026 daily reserve: its own reserve opens first, and is
    released again on ANY pre-dispatch failure — a 026 ``LedgerError`` (skip) or
    any other exception (re-raised) — so the Attempt reservation never outlives
    a candidate that was never actually dispatched.
    """
    from llmxive.backends.credits import paid_call_allowed

    ref = candidate.model_ref

    # C6 (fail closed): the chain's credit snapshot must have been LIVE at
    # selection — a paid call must never rest on a stale/absent credit observation.
    cprov = chain.snapshot_provenance.get("credit")
    if cprov is None or cprov.source != "live":
        src = cprov.source if cprov is not None else "missing"
        return None, 0.0, f"paid {ref.model_id!r} skipped: credit snapshot source={src!r} != 'live' (C6)"

    if ledger_repo is None:
        return None, 0.0, (
            f"paid {ref.model_id!r} skipped: no reservation ledger configured "
            "(cannot reserve → fail closed)"
        )

    # Retry envelope (#4): the primitive makes up to ``retries`` provider ATTEMPTS,
    # each of which could charge, so a paid candidate reserves worst_case x retries.
    reserve_credits = candidate.worst_case_credits * max(1, retries)
    observer = credit_observer or _default_credit_observer(balance_fetch)
    try:
        epoch = observer().budget_epoch
        outstanding = outstanding_headroom_consumption(ledger_repo, epoch=epoch, config=ledger_config)
    except Exception as exc:  # fresh credit read / ledger sync failed → fail closed
        return None, 0.0, f"paid {ref.model_id!r} skipped: credit/ledger read failed ({type(exc).__name__}: {exc})"

    # Twice-checked paid (FR-011): the SECOND, immediately-pre-call guard owns the
    # full headroom comparison against fresh spend + outstanding reservations.
    allowed, reason = paid_call_allowed(
        ref.model_id,
        estimated_cost_credits=reserve_credits,
        outstanding_reservation_credits=outstanding,
        fetch=balance_fetch,  # type: ignore[arg-type]
    )
    if not allowed:
        return None, 0.0, f"paid {ref.model_id!r} skipped: {reason}"

    rid = _sanitize_reservation_id(ref.model_id, call_id)

    # Attempt-budget authority (FR-033b step i): reserve against the Attempt budget
    # BEFORE the 026 daily reserve. A False means it would exceed
    # attempt_budget_credits → skip the candidate (advance); it is NOT an error and
    # opens no 026 reservation.
    if reservation_authority is not None:
        if not reservation_authority.reserve(reserve_credits, reservation_id=rid, call_id=call_id):
            return None, 0.0, (
                f"paid {ref.model_id!r} skipped: Attempt budget exhausted "
                "(reservation_authority refused)"
            )

    # Atomic reservation (FR-016). ANY LedgerError — no headroom (LedgerDenied),
    # sustained CAS contention (LedgerContention), or an unreachable/unauthorized
    # ledger (LedgerAuthError) — means we cannot SAFELY reserve, so the paid
    # candidate is ineligible at call time → skip-candidate (advance), never an
    # abort (FR-010). A ValueError (e.g. a negative amount = programmer/data bug) is
    # NOT a LedgerError and deliberately surfaces uncaught — but EITHER way (skipped
    # on LedgerError, or re-raised on any other exception) any already-open Attempt
    # reservation is released first (open → released), never left leaking.
    lease_expires = now + timedelta(seconds=lease_duration_for(options.deadline_s))
    try:
        reserve(
            ledger_repo,
            reservation_id=rid,
            worst_case_credits=reserve_credits,
            model=ref.model_id,
            credit_observer=observer,
            lease_expires_at=lease_expires,
            now=now,
            config=ledger_config,
        )
    except LedgerError as exc:
        # 026 reserve refused/errored AFTER the Attempt reserve opened → release it
        # (FR-033b: Attempt reserved but the 026 reserve is refused/errors → release
        # the Attempt reservation, skip candidate). open → released.
        if reservation_authority is not None:
            reservation_authority.release(rid)
        return None, 0.0, f"paid {ref.model_id!r} skipped: could not reserve ({type(exc).__name__}: {exc})"
    except Exception:
        # Any OTHER exception (e.g. a ValueError for a negative amount — a
        # programmer/data bug, deliberately NOT a LedgerError) also occurs AFTER
        # the Attempt reserve opened, so it must release the SAME way before
        # re-raising unchanged — otherwise the Attempt reservation leaks (stuck
        # "open" forever), permanently shrinking the Attempt budget.
        if reservation_authority is not None:
            reservation_authority.release(rid)
        raise
    return rid, reserve_credits, None


def _settle_funded_hold(
    ledger_repo: Path,
    reservation_id: str,
    *,
    charged_usd: float | None,
    now: datetime,
    config: LedgerConfig,
    notes: list[str],
) -> float | None:
    """Reconcile a funded hold (spec 5.9.2) and return the charge the ledger records,
    or ``None`` when settling failed. Never raises: a failed settle must not turn a
    reply into a failed call, so it is logged (exception type only — no ledger or
    remote text that could carry a credential) and noted. The funded ledger has no
    sweep: an unsettled hold keeps counting at its full reservation against the
    month's allowance (``reservations.counting_total`` counts every ``open`` /
    ``settling`` hold of the epoch, whatever its lease) until the month ends."""
    try:
        return settle_funded(ledger_repo, reservation_id, charged_usd=charged_usd, now=now, config=config)
    except Exception as exc:
        msg = (
            f"funded settle_funded({reservation_id}) failed ({type(exc).__name__}); the hold "
            "stays open and counts at its full reservation until the month ends"
        )
        logger.warning("execute: %s", msg)
        notes.append(msg)
        return None


class _Hold(Enum):
    """What the funded ledger shows under this candidate's reservation id once this
    call's reserve attempt has finished (see :func:`_funded_action`)."""

    #: No hold under the id: the reserve was never attempted (a precondition failed) or
    #: was denied before anything was written, and the ledger read confirms no hold.
    ABSENT = "absent"
    #: The reserve succeeded and the hold carries THIS call's owner token.
    OWN = "own"
    #: The reserve raised although this call's ``open`` event landed; the hold has been
    #: released at zero (nothing was sent under it) and cannot be dispatched under.
    OWN_RELEASED = "own-released"
    #: Another call's hold, state ``open`` with an unexpired lease: that call may be
    #: about to dispatch under it, or be dispatching now.
    FOREIGN_LIVE = "foreign-live"
    #: Another call's hold that is ``settling``/``reconciled`` or whose lease expired.
    FOREIGN_ENDED = "foreign-ended"
    #: The reserve raised and ownership cannot be established: the ledger could not be
    #: read, or the hold is not on the local ref (it may have landed remotely).
    UNKNOWN = "unknown"


class _FundedAction(Enum):
    DISPATCH = "dispatch"  # emit ReservationOpened, claim the boundary, send once, settle
    SKIP = "skip"          # nothing sent; record a skip outcome and try the next candidate
    REPLAY = "replay"      # raise RouteReplayError: nothing sent, no later candidate


def _funded_action(*, audited: bool, derived_id: bool, hold: _Hold, claimed: bool) -> _FundedAction:
    """The decision for a funded candidate: (state) -> (action), for every state it is
    called with; ``test_funded_decision_table`` checks it row by row. :func:`execute`
    calls it once per funded candidate, after the reserve attempt. Three branches are
    decided in :func:`execute` outside this function:

    - a hold this call created (``OWN``, so this returns ``DISPATCH``) whose atomic
      ``claim_dispatch`` is then refused: the hold is released at zero and
      ``RouteReplayError`` is raised;
    - a sink failure (``ReservationOpened`` or ``claim_dispatch`` rejected or raising,
      or ``dispatch_claimed`` raising): ``RouteAuditError``, after releasing this call's
      own hold at zero if it has one;
    - a sink without ``dispatch_claimed``, asked about a candidate that will not be
      dispatched: ``RouteAuditError`` (it cannot tell a replay from a skip).

    - ``audited``: a ``route_audit`` sink was given (the dispatch boundary is gated).
    - ``derived_id``: the call id was derived from the route id (audited, no explicit
      ``call_id``), so the SAME route always names the SAME reservation id — a foreign
      hold under it was opened by this very route. An explicit id, or the fresh random
      one an unaudited call mints, says nothing about the route.
    - ``hold``: the :class:`_Hold` observed after this call's reserve attempt.
    - ``claimed``: this route + candidate's dispatch boundary is already claimed. For
      every state but ``OWN`` it is the sink's read-only ``dispatch_claimed`` (always
      ``False`` without a sink); for ``OWN`` it is the atomic ``claim_dispatch``
      refusing this call's claim.

    Rules, in order:

    1. a claimed boundary is a replay whatever the hold looks like (I4);
    2. only a hold this call created is dispatched under (I1, I2);
    3. audited + derived id + another call's LIVE hold: the original of this route is
       between its reserve and its dispatch claim — abort rather than skip to a later
       candidate, which would be a second dispatch for one route;
    4. anything else is a skip: nothing is sent for this candidate and the chain goes on.

    The action never touches another call's hold; what happens to this call's own hold
    (settled at its real cost, or at zero when nothing was sent) is fixed by
    :func:`execute`."""
    if claimed:
        return _FundedAction.REPLAY
    if hold is _Hold.OWN:
        return _FundedAction.DISPATCH
    if hold is _Hold.FOREIGN_LIVE and audited and derived_id:
        return _FundedAction.REPLAY
    return _FundedAction.SKIP


@dataclass(frozen=True)
class _FundedHold:
    """The outcome of one funded reserve attempt. ``reservation_id`` is the id tried
    (``None`` when no reserve was attempted); it names a hold this call may dispatch
    under and settle ONLY when ``state`` is ``_Hold.OWN``. ``reason`` is the skip note
    for every other state."""

    state: _Hold
    reservation_id: str | None
    reserved_usd: float
    reason: str
    #: The funded allowance refused the hold (``LedgerDenied`` with nothing under the
    #: id): spec 5.10 — paid candidates after it are skipped as well.
    allowance_denied: bool = False


def _foreign_state(hold: Reservation, now: datetime) -> _Hold:
    """``FOREIGN_LIVE`` for another call's ``open`` hold whose lease has not expired at
    ``now``; ``FOREIGN_ENDED`` otherwise. A lease that cannot be parsed or compared
    counts as live (the conservative side: abort rather than risk a second dispatch)."""
    if hold.state != STATE_OPEN:
        return _Hold.FOREIGN_ENDED
    try:
        expired = datetime.fromisoformat(hold.lease_expires_at) <= now
    except (TypeError, ValueError):
        expired = False
    return _Hold.FOREIGN_ENDED if expired else _Hold.FOREIGN_LIVE


def _release_unsent_hold_if_created(
    ledger_repo: Path,
    reservation_id: str,
    *,
    owner: str,
    now: datetime,
    config: LedgerConfig,
    notes: list[str],
    cause: BaseException | None = None,
) -> _Hold:
    """After a reserve that did not return a hold: read the ledger, release (reconcile
    at zero) a hold THIS call opened and never sent, and report what is under the id.
    ``cause`` is the exception that made the reserve fail; only its TYPE is logged.

    Creation is decided from the ledger itself: the hold's ``open`` event carries the
    ``owner`` token of the call that wrote it, so a hold another call opened under the
    same id (a replay, or a caller-supplied ``call_id``) is never touched — its own
    dispatch settles it (``FOREIGN_LIVE`` / ``FOREIGN_ENDED``). A hold that is this
    call's is released at zero (``OWN_RELEASED``). When ownership cannot be established
    — the ledger read fails, or the reserve raised something other than a denial and no
    hold is on the local ref (it may have landed remotely) — the result is ``UNKNOWN``:
    any such hold is left untouched (it counts at its full reservation until the month
    ends; the funded ledger has no sweep), and that
    is logged + noted. A denial (``LedgerDenied``: nothing is written by design) with
    no hold on a readable ledger is ``ABSENT``."""
    from llmxive.model_selection.ledger_transport import read_events
    from llmxive.model_selection.reservations import STATE_RECONCILED, project

    failed = f" after a failed reserve ({type(cause).__name__})" if cause is not None else ""
    try:
        hold = project(read_events(ledger_repo, ref=config.ref)).get(reservation_id)
    except Exception as exc:
        msg = (
            f"funded hold {reservation_id}: ownership unknown{failed} ({type(exc).__name__} reading "
            "the ledger); any hold is left untouched and counts at its full reservation until the month ends"
        )
        logger.warning("execute: %s", msg)
        notes.append(msg)
        return _Hold.UNKNOWN
    if hold is None:
        if isinstance(cause, LedgerDenied):
            return _Hold.ABSENT
        msg = (
            f"funded hold {reservation_id}: ownership unknown{failed} (not on the local ledger "
            "ref); if it landed remotely it is left untouched and counts at its full reservation until "
            "the month ends"
        )
        logger.warning("execute: %s", msg)
        notes.append(msg)
        return _Hold.UNKNOWN
    if hold.owner != owner:
        return _foreign_state(hold, now)
    if hold.state != STATE_RECONCILED:
        _settle_funded_hold(ledger_repo, reservation_id, charged_usd=0.0, now=now, config=config, notes=notes)
    return _Hold.OWN_RELEASED


def _open_funded_reservation(
    candidate: Candidate,
    chain: ModelChain,
    *,
    options: ExecutionOptions,
    ledger_repo: Path | None,
    config: LedgerConfig | None,
    funded_observer: Callable[[], CreditObservation] | None,
    funded_guard: FundedGuardSnapshot | None,
    now: datetime,
    call_id: str,
    owner: str,
    notes: list[str],
) -> _FundedHold:
    """Reserve a funded (Hugging Face) candidate's worst case x 1, in USD, on the funded
    ledger, and report the :class:`_FundedHold` that results. The state is ``OWN`` ONLY
    for a hold THIS call created (its ``owner`` token is on the hold's ``open`` event);
    every other state carries the skip note. This function decides nothing: what to do
    with the state is :func:`_funded_action`'s to say.

    The hold is priced by ``funded_observer`` when one is injected (FR-015 seam),
    else by :func:`hf_budget.reserve_funded` against the runtime snapshot's live
    ``funded_guard`` (one clock for pricing and ``created_at``; refuses a guard that is
    not live or is from another month). ``reservation_authority`` (Dartmouth credits)
    is not consulted. Only ``worst_case x 1`` is held: the candidate is dispatched once.

    A hold found already there under the same id (a replay, a shared ``call_id``, two
    Attempts sharing a route) belongs to the call that created it: it is never settled
    or released here. If the reserve raised, :func:`_release_unsent_hold_if_created`
    reads the ledger and releases the hold at zero only when it is provably this
    call's. Notes carry the failure's exception TYPE only, never its text."""
    ref = candidate.model_ref
    fprov = chain.snapshot_provenance.get("funded")
    if fprov is None or fprov.source != "live":
        src = fprov.source if fprov is not None else "missing"
        return _FundedHold(
            _Hold.ABSENT, None, 0.0, f"funded {ref.model_id!r} skipped: funded guard source={src!r} != 'live'"
        )
    if ledger_repo is None or config is None:
        return _FundedHold(
            _Hold.ABSENT, None, 0.0, f"funded {ref.model_id!r} skipped: no funded ledger configured (fail closed)"
        )
    if funded_observer is None and funded_guard is None:
        return _FundedHold(
            _Hold.ABSENT, None, 0.0,
            f"funded {ref.model_id!r} skipped: no funded guard to price the hold (fail closed)",
        )

    reserve_usd = candidate.worst_case_credits / USD_TO_CREDITS
    rid = _sanitize_reservation_id(ref.model_id, call_id)
    lease_expires = now + timedelta(seconds=lease_duration_for(options.deadline_s))
    try:
        if funded_observer is not None:
            hold = reserve(
                ledger_repo, reservation_id=rid, worst_case_credits=reserve_usd, model=ref.model_id,
                credit_observer=funded_observer, lease_expires_at=lease_expires, now=now, config=config,
                owner=owner,
            )
        else:
            hold = reserve_funded(
                ledger_repo, reservation_id=rid, worst_case_usd=reserve_usd, model=ref.model_id,
                lease_expires_at=lease_expires, now=now, config=config,
                guard=funded_guard,  # type: ignore[arg-type]  # non-None: checked above
                owner=owner,
            )
    except Exception as exc:
        # A denial, a ledger error, a refused guard, an exploding observer: whatever it
        # was, the ledger says what is under the id now (a failed reserve may have met,
        # or — for a hold already reconciled — collided with, another call's hold).
        state = _release_unsent_hold_if_created(
            ledger_repo, rid, owner=owner, now=now, config=config, notes=notes, cause=exc
        )
        if state in (_Hold.FOREIGN_LIVE, _Hold.FOREIGN_ENDED):
            return _FundedHold(state, rid, 0.0, _foreign_skip(ref.model_id, rid))
        denied = isinstance(exc, LedgerDenied)
        verb = "reservation denied" if denied else "could not reserve"
        return _FundedHold(
            state, rid, 0.0, f"funded {ref.model_id!r} skipped: {verb} ({type(exc).__name__})",
            allowance_denied=denied and state is _Hold.ABSENT,
        )
    if hold.owner != owner:
        return _FundedHold(_foreign_state(hold, now), rid, 0.0, _foreign_skip(ref.model_id, rid))
    return _FundedHold(_Hold.OWN, rid, reserve_usd, "")


def _foreign_skip(model_id: str, rid: str) -> str:
    return (
        f"funded {model_id!r} skipped: hold {rid} already exists for another call "
        "(only the call that created a funded hold may send under or settle it)"
    )


def _dispatch_already_claimed(
    route_audit: RouteAudit, route_id: str, candidate_index: int, ref: ModelRef, hold_id: str | None
) -> bool:
    """READ-ONLY: whether this route's dispatch boundary for the candidate is already
    claimed, asked of the sink's ``dispatch_claimed`` before a funded candidate is
    skipped for ANY reason. A sink that cannot answer (no ``dispatch_claimed``) or
    fails to fails CLOSED with ``RouteAuditError`` — a replay must never fall through
    to a later candidate."""
    probe = DispatchStarted(route_id, candidate_index, ref, hold_id)
    check = getattr(route_audit, "dispatch_claimed", None)
    if check is None:
        raise RouteAuditError(
            f"route_audit sink cannot report whether {ref.model_id!r} was already dispatched "
            "(no dispatch_claimed); a funded candidate that will not be dispatched cannot be "
            "told from a replay"
        )
    try:
        return bool(check(probe))
    except RouteAuditError:
        raise
    except Exception as exc:
        raise RouteAuditError(f"dispatch_claimed({ref.model_id!r}) failed: {type(exc).__name__}") from exc


def _provably_no_inference(exc: BaseException, *, sent: bool) -> bool:
    """spec 5.9.2: a funded call is charged zero only when it provably incurred no
    inference — ``execute`` never handed it to the backend (``sent`` False), the
    backend recorded that no HTTP request was or will be sent (circuit breaker open,
    missing token or bill-to: :func:`huggingface.request_was_sent`), or the provider
    definitively rejected it before inference (HTTP 401/402/403,
    ``PreInferenceRejection``). Everything else may have reached inference."""
    return not sent or not request_was_sent(exc) or isinstance(exc, PreInferenceRejection)


def _usage_charge_usd(candidate: Candidate, response: ChatResponse) -> float | None:
    """The real USD cost of a funded reply: ``input_tokens x input rate + output_tokens x
    output rate`` from the catalog price, or ``None`` (charge the full reservation)
    when the reply does not report BOTH counts as non-negative integers."""
    tin, tout = response.input_tokens, response.output_tokens
    p = candidate.pricing
    if not all(isinstance(t, int) and not isinstance(t, bool) and t >= 0 for t in (tin, tout)):
        return None
    if not p.is_known:
        return None
    return tin * p.input_usd_per_token + tout * p.output_usd_per_token  # type: ignore[operator]


def execute(
    chain: ModelChain,
    messages: Iterable[ChatMessage],
    *,
    options: ExecutionOptions,
    backend_factory: Callable[[str], BaseBackend] = make_backend,
    retries: int = 3,
    ledger_repo: Path | None = None,
    ledger_config: LedgerConfig | None = None,
    credit_observer: Callable[[], CreditObservation] | None = None,
    balance_fetch: Callable[[], object] | None = None,
    now: datetime | None = None,
    call_id: str | None = None,
    reservation_authority: ReservationAuthority | None = None,
    route_audit: RouteAudit | None = None,
    route_id: str | None = None,
    funded_ledger_config: LedgerConfig | None = None,
    funded_observer: Callable[[], CreditObservation] | None = None,
    funded_guard: FundedGuardSnapshot | None = None,
) -> ExecutionResult:
    """Execute ``chain`` against ``messages`` and return the first successful
    :class:`ExecutionResult`.

    ``backend_factory`` / ``credit_observer`` / ``balance_fetch`` /
    ``funded_observer`` are the supported injection seams (FR-015). Paid and funded
    candidates require ``ledger_repo``.

    **Funded candidates (spec 027 5.6 / 5.9.2 / 5.9.6).** A candidate whose
    ``cost_class`` is ``"funded"`` (Hugging Face) needs neither ``allow_paid`` nor the
    paid opt-in. It is skipped (advance, nothing sent) unless the chain's ``funded``
    snapshot component was ``live`` at selection AND a hold of ``worst_case x 1`` (USD)
    opens on the funded ledger (``funded_ledger_config``; ``None`` →
    ``funded_ledger_config_from_env()``, failing closed on a missing anchor). The hold
    is priced by ``funded_observer`` when injected, else by
    ``hf_budget.reserve_funded`` against ``funded_guard`` (the runtime snapshot's
    guard; ``route_chat`` passes it). It is dispatched ONCE (``retries=1``) and ALWAYS
    reconciled before ``execute`` leaves the candidate: the charge is ``usage`` x the
    catalog price (capped at the reservation, the excess noted and logged), ``0.0``
    when no inference provably happened (:func:`_provably_no_inference`: never handed
    to the backend, the backend recorded no request sent — breaker open, missing token
    or bill-to — or HTTP 401/402/403), and the full reservation for every other
    failure or a reply without both token counts. A successful reply carries the
    charge as ``response.cost_estimate_usd`` and ``ExecutionResult.charged_usd``; a
    failed settle is logged + noted and never fails the reply.

    Every funded hold carries this call's ``owner`` token, and ONE function,
    :func:`_funded_action`, decides what a funded candidate does from (audited or not,
    call id derived from the route or not, the hold found under the id after this
    call's reserve attempt, the dispatch boundary claimed or not):

    - a hold THIS call created is the only kind dispatched under or settled here; a hold
      found under the same id (a replay, a shared ``call_id``, two Attempts on one
      route) is another call's and is never sent under, settled or released;
    - with a ``route_audit`` sink, before a funded candidate is NOT dispatched for any
      reason (another call's hold, a denied or failed reserve, an unmet precondition)
      the sink's read-only ``dispatch_claimed`` is asked: an already-claimed boundary is
      a replay → ``RouteReplayError`` (nothing sent, no later candidate tried). A sink
      that cannot answer fails closed (``RouteAuditError``);
    - with a call id DERIVED from the route id, another call's hold that is still open
      (lease unexpired) with no claim yet is the original of this same route between
      its reserve and its claim → ``RouteReplayError`` too. Once that hold is settled,
      reconciled or its lease expired, the candidate is skipped instead, so a route
      whose original crashed recovers. With an EXPLICIT ``call_id`` an unclaimed foreign
      hold is always just skipped;
    - otherwise the candidate is skipped and the chain goes on (an exhausted allowance
      or an unreachable ledger with no claim is not a replay). When the skip is the
      allowance denying the hold (``LedgerDenied``, nothing under the id), every later
      PAID candidate is skipped too (spec 5.10); free and local candidates still run;
    - a hold this call created whose atomic ``claim_dispatch`` is refused (``False``) is
      released at zero before ``RouteReplayError``; a claim or ``ReservationOpened`` the
      sink rejects (a conflicting payload — e.g. the same route under a different
      explicit ``call_id`` — or a sink failure) releases it at zero before
      ``RouteAuditError``.

    Skip notes, audit reasons and log lines on this path carry an exception's TYPE,
    never its text.

    **Attempt budget (FR-033b).** An optional ``reservation_authority`` is consulted
    per paid candidate, BEFORE the 026 daily reserve: a refusal (``False``) skips the
    candidate (advance) with no 026 reservation opened; a subsequent 026
    ``LedgerError`` releases the already-open Attempt reservation. A dispatched paid
    candidate's Attempt reservation is marked retained (never released) alongside the
    026 settle. Default ``None`` is a no-op — behavior is unchanged from today.

    **Outbox audit (FR-033a) + atomic dispatch claim (maintainer review fix #5).**
    An optional ``route_audit`` receives the per-candidate outbox lifecycle: a paid
    candidate's opened reservation emits ``ReservationOpened``, then every candidate's
    ``DispatchStarted`` is submitted through ``route_audit.claim_dispatch`` immediately
    before the backend call — both durable and pre-dispatch, so a sink failure there is
    ROUTE-FATAL (raises ``RouteAuditError``; if a reservation had opened it is released
    + settled first, and the chain does NOT advance). ``claim_dispatch`` ATOMICALLY
    claims the dispatch boundary for that ``(route_id, candidate_index)``: the FIRST
    claim (``True``) dispatches as usual; a REPLAY (``False`` — this candidate already
    crossed the boundary, e.g. a retried logical call with the same ``route_id``) does
    NOT invoke the backend a second time — the reservation is RETAINED (never released;
    the original dispatch owns it) and ``RouteReplayError`` is raised, never a
    ``CandidateOutcome`` (the original run already emitted one for this event_id). A
    successful dispatch emits ``DispatchCompleted`` then ``CandidateOutcome("success",
    ...)``; a sink failure on either fails the call CLOSED (raises ``RouteAuditError``)
    with the reservation left RETAINED — the existing ``finally`` still settles + marks
    it. Skip/advance/abort dispositions each emit their own ``CandidateOutcome``.
    Default ``None`` is a no-op — zero audit calls, ``claimed`` is always ``True``, and
    behavior is byte-for-byte unchanged (no idempotency without a sink). ``route_id``
    identifies the logical call for correlation (spec-025 maintainer review F1):
    ``route_chat`` generates one and threads it through; a direct caller of ``execute``
    gets a fresh ``uuid.uuid4().hex`` when omitted. ``call_id`` (the reservation-id
    token) is
    DISTINCT from ``route_id`` (maintainer review finding #3) — it preserves the
    prior 12-hex-char ``_sanitize_reservation_id`` suffix format. When omitted its
    derivation is CONDITIONAL on whether the dispatch-idempotency gate is active
    (slice-0 audit fix #6, HIGH finding #1):

    - with a ``route_audit`` sink, the atomic ``claim_dispatch`` boundary gates the
      real backend dispatch, so ``call_id`` is DERIVED from ``route_id`` via a
      truncated SHA-256 — a retried logical route (same injected ``route_id``)
      reuses the SAME ``call_id`` → the SAME paid ``reservation_id``, the 026
      ledger's idempotent ``reserve()`` no-ops the retry, and the claim rejects the
      second dispatch;
    - WITHOUT a ``route_audit`` sink there is NO dispatch-idempotency gate
      (``claimed`` is unconditionally ``True``), so a stable ``reservation_id``
      would be actively unsafe — two same-route calls would share one reserved
      envelope yet BOTH invoke the backend (a double charge). ``call_id`` is minted
      FRESH per call so each no-audit call opens its OWN conservative envelope and
      is independently budgeted.

    A caller MAY still override with an explicit ``call_id``; supplying one WITHOUT
    a ``route_audit`` sink is advanced/unsafe use — it pins the ``reservation_id``
    but does NOT confer dispatch idempotency (the caller owns dedup).

    **Ledger config resolution (R5-1 / finding-3).** ``ledger_config`` defaults to
    ``None`` = the PRODUCTION config, resolved via
    ``ledger_transport.ledger_config_from_env()`` (the single sanctioned source of
    the authoritative remote + pinned bootstrap anchor) the first time a paid
    reservation is needed. It FAILS CLOSED — if the anchor is not pinned, every paid
    candidate is skipped (never a silent LOCAL-only reservation). A caller opts into
    local/single-runner/test mode by passing an EXPLICIT ``LedgerConfig`` (e.g.
    ``LedgerConfig(remote=None)``). Free-only chains never touch the env or the
    ledger. Without a ``ledger_repo`` (or when the config/ledger read fails) paid
    candidates are skipped (fail closed). Raises :class:`ChainExhausted` if no
    candidate succeeds, or re-raises a request-level permanent refusal (abort)
    unchanged; raises ``ValueError`` on the fail-fast budget check before any call.
    """
    now = now or datetime.now(UTC)
    route_id = route_id or uuid.uuid4().hex
    # call_id is the reservation-id token — DISTINCT from route_id (maintainer
    # review finding #3): route_id is the (potentially long-lived, caller-injected)
    # event-correlation id, while call_id preserves the prior 12-hex-char reservation
    # suffix format that `_sanitize_reservation_id` bakes into every persisted
    # reservation id.
    #
    # Slice-0 audit fix #6 (HIGH finding #1): the call_id derivation is CONDITIONAL
    # on whether the dispatch-idempotency gate (the atomic claim_dispatch below) is
    # active — i.e. on whether a route_audit sink was injected.
    # Funded holds record this per-call token as their `owner`, so this call can tell
    # a hold it opened from one another call opened under the same reservation id.
    funded_owner = uuid.uuid4().hex
    # A call id DERIVED from the route id makes one route always name the same funded
    # reservation id, so another call's hold under it is this route's own original
    # (see `_funded_action`). An explicit id, or the unaudited fresh one, is not that.
    call_id_derived = call_id is None and route_audit is not None
    if call_id is None:
        if route_audit is not None:
            # AUDITED path: claim_dispatch() gates the real backend dispatch, so a
            # retried logical route (same injected route_id) is SAFE to — and MUST
            # — derive the SAME reservation_id: the 026 reserve() no-ops the retry
            # (idempotent on a matching (model, worst_case_credits, budget_epoch)
            # identity under a given reservation_id, reservations.py ~239-255) AND
            # the claim rejects the second dispatch. Hashing route_id keeps the
            # 12-hex-char suffix format (a naive `route_id[:12]` would widen it to
            # the 32-char route_id and could collide on a common prefix) while
            # making it retry-stable.
            call_id = hashlib.sha256(route_id.encode()).hexdigest()[:12]
        else:
            # COMPAT path (no audit sink → NO dispatch-idempotency gate; `claimed`
            # is unconditionally True below). A stable route_id-derived call_id is
            # ACTIVELY UNSAFE here: two same-route calls would derive the SAME
            # reservation_id, the 026 ledger would no-op the second reserve() as
            # idempotent, yet the backend would STILL be invoked a second time — up
            # to 2x retries paid attempts charged under ONE reserved envelope. Mint a
            # FRESH random call_id so each no-audit call opens its OWN conservative
            # envelope and is independently budgeted (without a sink there is no
            # replay detection, so each call is a fully independent logical call).
            call_id = uuid.uuid4().hex[:12]
    msg_list = list(messages)

    if not chain.candidates:
        raise ChainExhausted("execute: empty ModelChain (no candidates)")

    # Fail-fast (FR-010): the ACTUAL messages must fit the priced budget.
    ok, reason = fits_budget(msg_list, options.max_tokens, chain.call_budget)
    if not ok:
        raise ValueError(f"execute: fail-fast budget check failed — {reason}")

    # Resolve the effective ledger config ONCE, up front, so reserve / lease / settle
    # all use the SAME config. Default (None) → the PRODUCTION config (fail-closed on
    # a missing anchor); an explicit LedgerConfig (incl. remote=None) is the opt-in
    # local/test mode. Only touched when the chain actually contains a paid candidate
    # (a free-only chain never reads the env and never fails closed on the anchor).
    # The funded ledger is resolved the same way, on its own ref/anchor, only when a
    # funded candidate is present.
    ledger_config_error: str | None = None
    if (
        ledger_config is None
        and ledger_repo is not None
        and any(c.cost_class == "paid" for c in chain.candidates)
    ):
        try:
            ledger_config = ledger_config_from_env()
        except LedgerError as exc:
            ledger_config_error = str(exc)  # paid candidates fail closed (skip) below
    funded_config_error: str | None = None
    if (
        funded_ledger_config is None
        and ledger_repo is not None
        and any(c.cost_class == "funded" for c in chain.candidates)
    ):
        try:
            funded_ledger_config = funded_ledger_config_from_env()
        except LedgerError as exc:
            funded_config_error = str(exc)  # funded candidates fail closed (skip) below

    notes: list[str] = []
    allowance_denied = False  # a funded hold was refused by the allowance (see paid below)
    for candidate_index, candidate in enumerate(chain.candidates):
        ref = candidate.model_ref
        reservation_id: str | None = None
        reserved_credits = 0.0
        funded = candidate.cost_class == "funded"
        reserved_usd = 0.0

        if funded:
            if funded_config_error is not None:
                # `funded_config_error` is this project's own LedgerError from
                # `_config_from_env`: its text is built from constant env-var NAMES and
                # a command name, never from a value, so it is safe to carry.
                held = _FundedHold(
                    _Hold.ABSENT, None, 0.0,
                    f"funded {ref.model_id!r} skipped: funded ledger not configured ({funded_config_error}) — fail closed",
                )
            else:
                held = _open_funded_reservation(
                    candidate, chain, options=options, ledger_repo=ledger_repo,
                    config=funded_ledger_config, funded_observer=funded_observer,
                    funded_guard=funded_guard, now=now, call_id=call_id,
                    owner=funded_owner, notes=notes,
                )
            # Before a funded candidate is NOT dispatched for any reason, ask the sink
            # (read-only) whether this route already claimed its dispatch boundary: a
            # replay must not be mistaken for a candidate to skip past (I4). For a hold
            # this call created, the atomic claim_dispatch below answers instead.
            boundary_claimed = (
                held.state is not _Hold.OWN
                and route_audit is not None
                and _dispatch_already_claimed(route_audit, route_id, candidate_index, ref, held.reservation_id)
            )
            action = _funded_action(
                audited=route_audit is not None, derived_id=call_id_derived,
                hold=held.state, claimed=boundary_claimed,
            )
            if action is _FundedAction.REPLAY:
                # Nothing sent, nothing settled or released that is not this call's own,
                # no later candidate tried, and no CandidateOutcome (it would collide
                # with the original's).
                why = (
                    "already dispatched" if boundary_claimed
                    else f"its funded hold {held.reservation_id} is open under the original call, which has not "
                         "yet claimed the dispatch"
                )
                raise RouteReplayError(
                    f"route {route_id!r} candidate {candidate_index} ({ref.model_id!r}) {why} — not "
                    "dispatching and not trying a later candidate (replay); the funded hold belongs to "
                    "the original dispatch"
                )
            if action is _FundedAction.SKIP:
                notes.append(held.reason)
                emit_audit(route_audit, CandidateOutcome(route_id, candidate_index, ref, "skip", held.reason))
                allowance_denied = allowance_denied or held.allowance_denied
                continue
            # DISPATCH. Invariant: `reservation_id` is set for a funded candidate only
            # here, so it always names a hold THIS call created — every settle/release
            # of it on any path below is this call's own.
            reservation_id, reserved_usd = held.reservation_id, held.reserved_usd
            reserved_credits = candidate.worst_case_credits
        elif candidate.cost_class == "paid":
            if allowance_denied:
                # Spec 5.10: when the funded allowance removed the funded class, paid
                # is not reached. ``select`` applies this at selection time; this is
                # the same rule for an allowance exhausted between the snapshot and
                # the call. (A ``require_paid`` chain never carries a funded candidate,
                # so this never fires on one.) Free and local candidates still run.
                reason = (
                    f"paid {ref.model_id!r} skipped: the funded allowance denied a reservation "
                    "for this call — paid not reached (Constitution IV)"
                )
                notes.append(reason)
                emit_audit(route_audit, CandidateOutcome(route_id, candidate_index, ref, "skip", reason))
                continue
            if ledger_config_error is not None:
                notes.append(
                    f"paid {ref.model_id!r} skipped: production ledger not configured "
                    f"({ledger_config_error}) — fail closed"
                )
                emit_audit(
                    route_audit,
                    CandidateOutcome(route_id, candidate_index, ref, "skip", "production ledger not configured"),
                )
                continue
            reservation_id, reserved_credits, skip = _open_paid_reservation(
                candidate, chain, options=options, retries=retries,
                ledger_repo=ledger_repo, ledger_config=ledger_config,
                credit_observer=credit_observer, balance_fetch=balance_fetch,
                now=now, call_id=call_id, reservation_authority=reservation_authority,
            )
            if skip is not None:
                notes.append(skip)
                emit_audit(route_audit, CandidateOutcome(route_id, candidate_index, ref, "skip", skip))
                continue

        # Pre-dispatch: emit ReservationOpened, then ATOMICALLY claim the dispatch
        # boundary (spec-025 maintainer review fix #5 — making the audit EVENTS
        # idempotent, round 4, did not make the backend-dispatch SIDE EFFECT
        # idempotent; a replayed execute() call for the same route_id would still
        # invoke the backend a second time). A failure of EITHER ReservationOpened
        # OR the claim itself is ROUTE-FATAL: do NOT advance. If a reservation
        # opened, release it (definitively did not dispatch) and settle the 026
        # hold, then re-raise. All of this is inside ONE try so neither failure can
        # leak the reservation.
        try:
            if reservation_id is not None:
                emit_audit(
                    route_audit,
                    ReservationOpened(
                        route_id, candidate_index, ref, reservation_id, reserved_credits,
                        reserved_usd=reserved_usd if funded else None,
                    ),
                )
            if route_audit is not None:
                try:
                    claimed = route_audit.claim_dispatch(
                        DispatchStarted(route_id, candidate_index, ref, reservation_id)
                    )
                except RouteAuditError:
                    raise
                except Exception as exc:  # sink infra failure → route-fatal, distinct from a replay
                    raise RouteAuditError(
                        f"claim_dispatch({ref.model_id!r}) failed: {type(exc).__name__}"
                    ) from exc
            else:
                claimed = True  # no audit sink → no idempotency (compat path, unchanged behavior)
        except RouteAuditError:
            if reservation_id is not None and funded:
                # Not dispatched: release this call's own hold (the only kind a funded
                # reservation_id can name — see the invariant above) at zero.
                _settle_funded_hold(
                    ledger_repo, reservation_id, charged_usd=0.0, now=now,  # type: ignore[arg-type]
                    config=funded_ledger_config, notes=notes,  # type: ignore[arg-type]
                )
            elif reservation_id is not None:
                # F3: run BOTH cleanups independently — a failing release() must not
                # suppress settle(), and neither must mask the primary RouteAuditError.
                if reservation_authority is not None:
                    try:
                        reservation_authority.release(reservation_id)
                    except Exception as exc:  # best-effort; log, never mask the audit error
                        logger.warning("execute: release(%s) after audit-abort failed: %s", reservation_id, exc)
                try:
                    settle(ledger_repo, reservation_id, now=now, config=ledger_config)  # type: ignore[arg-type]
                except Exception as exc:  # best-effort; the sweeper backstops a lost settle
                    logger.warning("execute: settle(%s) after audit-abort failed: %s", reservation_id, exc)
            raise

        if not claimed:
            # REPLAY (fix #5): a DispatchStarted with this event_id was ALREADY
            # durably recorded — the ORIGINAL dispatch owns any reservation. Do NOT
            # invoke the backend a second time; RETAIN (never release) the
            # reservation, and let the caller/lane reconcile from durable events
            # (e.g. a DispatchStarted with no DispatchCompleted → DispatchUnknown).
            # No CandidateOutcome is emitted here — the original run already
            # emitted the outcome for this event_id; a differing outcome would
            # collide under F2's collision semantics. A FUNDED reservation_id here
            # is always a hold THIS call created (a foreign hold never gets this far),
            # and nothing was sent under it, so it is released at zero below.
            if reservation_id is not None and funded:
                _settle_funded_hold(
                    ledger_repo, reservation_id, charged_usd=0.0, now=now,  # type: ignore[arg-type]
                    config=funded_ledger_config, notes=notes,  # type: ignore[arg-type]
                )
            elif reservation_id is not None:
                try:
                    settle(ledger_repo, reservation_id, now=now, config=ledger_config)  # type: ignore[arg-type]
                except Exception as exc:
                    logger.warning("execute: settle(%s) on replay failed: %s", reservation_id, exc)
                if reservation_authority is not None:
                    try:
                        reservation_authority.mark_retained(reservation_id)
                    except Exception as exc:
                        logger.warning("execute: mark_retained(%s) on replay failed: %s", reservation_id, exc)
            raise RouteReplayError(
                f"route {route_id!r} candidate {candidate_index} ({ref.model_id!r}) already dispatched "
                "— not re-dispatching (replay); reservation retained, reconcile from durable events"
            )

        lease = (
            ReservationLease(
                ledger_repo,  # type: ignore[arg-type]  # non-None whenever reservation_id is set
                reservation_id,
                interval_s=max(5.0, lease_duration_for(options.deadline_s) / 3.0),
                lease_duration_s=lease_duration_for(options.deadline_s),
                config=funded_ledger_config if funded else ledger_config,
            )
            if reservation_id is not None
            else nullcontext()
        )
        # Funded settlement state: ``sent`` flips just before the request can leave;
        # ``funded_settled`` guarantees exactly one reconcile per hold (the finally
        # settles anything a path below did not).
        sent = False
        funded_settled = False
        charged_usd: float | None = None
        try:
            backend = backend_factory(ref.backend)
            with lease:
                sent = True
                response = chat_one_candidate(
                    backend,
                    msg_list,
                    model=ref.model_id,
                    max_tokens=options.max_tokens,
                    temperature=options.temperature,
                    deadline_s=options.deadline_s,
                    # A funded hold covers ONE call's worst case: never retry under it.
                    retries=1 if funded else retries,
                )
            if funded and reservation_id is not None:
                usage_usd = _usage_charge_usd(candidate, response)
                charge = usage_usd
                if usage_usd is not None and usage_usd > reserved_usd:
                    msg = (
                        f"funded {ref.model_id!r}: usage cost ${usage_usd:.6f} exceeds its reservation "
                        f"${reserved_usd:.6f}; charged the reservation"
                    )
                    logger.warning("execute: %s", msg)
                    notes.append(msg)
                    charge = reserved_usd
                funded_settled = True
                recorded = _settle_funded_hold(
                    ledger_repo, reservation_id, charged_usd=charge, now=now,  # type: ignore[arg-type]
                    config=funded_ledger_config, notes=notes,  # type: ignore[arg-type]
                )
                charged_usd = recorded if recorded is not None else (charge if charge is not None else reserved_usd)
                response = replace(response, cost_estimate_usd=charged_usd)
            # Post-dispatch (FR-033a/F2): a failure here fails the call CLOSED, but the
            # reservation stays RETAINED (the finally settles/marks it) — the backend
            # already ran, so we never advance.
            emit_audit(route_audit, DispatchCompleted(route_id, candidate_index, ref, reservation_id))
            emit_audit(route_audit, CandidateOutcome(route_id, candidate_index, ref, "success", "ok"))
            return ExecutionResult(
                response=response,
                model_ref=ref,
                reserved_credits=reserved_credits,
                notes=tuple(notes),
                reserved_usd=reserved_usd if funded else None,
                reservation_id=reservation_id,
                charged_usd=charged_usd,
            )
        except RouteAuditError:
            raise  # route-fatal — never a candidate disposition
        except Exception as exc:
            if funded and reservation_id is not None and not funded_settled:
                # spec 5.9.2: a request never sent, or a definitive pre-inference
                # rejection (HTTP 401/402/403), charges zero; anything else that may
                # have reached inference (timeout, 5xx, malformed 200, ...) charges the
                # full reservation.
                funded_settled = True
                _settle_funded_hold(
                    ledger_repo, reservation_id,  # type: ignore[arg-type]
                    charged_usd=0.0 if _provably_no_inference(exc, sent=sent) else None,
                    now=now, config=funded_ledger_config, notes=notes,  # type: ignore[arg-type]
                )
            disp = disposition_of(exc)
            if disp is CandidateDisposition.ABORT:
                # Request-level permanent refusal — stop the chain and re-raise.
                emit_audit(
                    route_audit,
                    CandidateOutcome(route_id, candidate_index, ref, "abort", f"{type(exc).__name__}: {exc}"),
                )
                raise
            notes.append(f"{ref.model_id!r}: {disp.value}: {type(exc).__name__}: {exc}")
            emit_audit(
                route_audit,
                CandidateOutcome(route_id, candidate_index, ref, "advance", f"{disp.value}: {type(exc).__name__}"),
            )
        finally:
            if reservation_id is not None and funded:
                if not funded_settled:
                    # A path above left the hold open (e.g. a BaseException such as
                    # KeyboardInterrupt): reconcile it here — zero if nothing was sent,
                    # else the full reservation.
                    _settle_funded_hold(
                        ledger_repo, reservation_id,  # type: ignore[arg-type]
                        charged_usd=None if sent else 0.0, now=now,
                        config=funded_ledger_config, notes=notes,  # type: ignore[arg-type]
                    )
            elif reservation_id is not None:
                # Retain the hold (settle → settling) on ANY outcome — never
                # release at call-return (FR-016); the reconciler/sweeper finalizes
                # it against observed spend. A settle failure must not mask the call.
                try:
                    settle(ledger_repo, reservation_id, now=now, config=ledger_config)  # type: ignore[arg-type]
                except Exception as exc:  # best-effort; the sweeper backstops a lost settle
                    logger.warning("execute: settle(%s) failed: %s", reservation_id, exc)
                if reservation_authority is not None:
                    # Dispatched (success OR advance) → reconciliation-pending, never
                    # released (mirrors the 026 settle → settling transition). Best-effort,
                    # like the settle() call above: this finally runs AFTER a successful
                    # candidate's ExecutionResult is already built, so a raising
                    # mark_retained must never discard an already-charged, already-returned
                    # response — log and continue (the sweeper backstops reconciliation).
                    try:
                        reservation_authority.mark_retained(reservation_id)
                    except Exception as exc:  # best-effort; never discard a built result
                        logger.warning(
                            "execute: mark_retained(%s) failed: %s", reservation_id, exc
                        )

    raise ChainExhausted(
        f"execute: chain of {len(chain.candidates)} candidate(s) exhausted without success; "
        f"notes={notes}"
    )


__all__ = ["ChainExhausted", "ExecutionResult", "execute"]
