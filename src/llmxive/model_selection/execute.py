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
"""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Callable, Iterable
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from llmxive.backends.base import BaseBackend, ChatMessage, ChatResponse
from llmxive.backends.router import (
    CandidateDisposition,
    chat_one_candidate,
    disposition_of,
    make_backend,
)
from llmxive.model_selection.ledger_transport import (
    LedgerConfig,
    LedgerError,
    ledger_config_from_env,
)
from llmxive.model_selection.reservations import (
    CreditObservation,
    ReservationLease,
    lease_duration_for,
    outstanding_headroom_consumption,
    reserve,
    settle,
)
from llmxive.model_selection.tokens import fits_budget
from llmxive.model_selection.types import Candidate, ExecutionOptions, ModelChain, ModelRef

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
    FR-033a: the lane attributes settled Attempt cost by this id)."""

    response: ChatResponse
    model_ref: ModelRef
    reserved_credits: float
    notes: tuple[str, ...]
    reservation_id: str | None = None


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
) -> tuple[str | None, float, str | None]:
    """Twice-check + reserve a paid candidate. Returns
    ``(reservation_id, reserved_credits, skip_reason)`` — exactly one of
    ``reservation_id`` / ``skip_reason`` is non-None. A ``skip_reason`` means the
    candidate is fail-closed skipped (advance the chain), never an abort."""
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

    # Atomic reservation (FR-016). ANY LedgerError — no headroom (LedgerDenied),
    # sustained CAS contention (LedgerContention), or an unreachable/unauthorized
    # ledger (LedgerAuthError) — means we cannot SAFELY reserve, so the paid
    # candidate is ineligible at call time → skip-candidate (advance), never an
    # abort (FR-010). A ValueError (e.g. a negative amount = programmer/data bug) is
    # NOT a LedgerError and deliberately surfaces.
    rid = _sanitize_reservation_id(ref.model_id, call_id)
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
        return None, 0.0, f"paid {ref.model_id!r} skipped: could not reserve ({type(exc).__name__}: {exc})"
    return rid, reserve_credits, None


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
) -> ExecutionResult:
    """Execute ``chain`` against ``messages`` and return the first successful
    :class:`ExecutionResult`.

    ``backend_factory`` / ``credit_observer`` / ``balance_fetch`` are the supported
    injection seams (FR-015). Paid candidates require ``ledger_repo``.

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
    call_id = call_id or uuid.uuid4().hex[:12]
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
    ledger_config_error: str | None = None
    if (
        ledger_config is None
        and ledger_repo is not None
        and any(not c.pricing.is_free for c in chain.candidates)
    ):
        try:
            ledger_config = ledger_config_from_env()
        except LedgerError as exc:
            ledger_config_error = str(exc)  # paid candidates fail closed (skip) below

    notes: list[str] = []
    for candidate in chain.candidates:
        ref = candidate.model_ref
        reservation_id: str | None = None
        reserved_credits = 0.0

        if not candidate.pricing.is_free:
            if ledger_config_error is not None:
                notes.append(
                    f"paid {ref.model_id!r} skipped: production ledger not configured "
                    f"({ledger_config_error}) — fail closed"
                )
                continue
            reservation_id, reserved_credits, skip = _open_paid_reservation(
                candidate, chain, options=options, retries=retries,
                ledger_repo=ledger_repo, ledger_config=ledger_config,
                credit_observer=credit_observer, balance_fetch=balance_fetch,
                now=now, call_id=call_id,
            )
            if skip is not None:
                notes.append(skip)
                continue

        lease = (
            ReservationLease(
                ledger_repo,  # type: ignore[arg-type]  # non-None whenever reservation_id is set
                reservation_id,
                interval_s=max(5.0, lease_duration_for(options.deadline_s) / 3.0),
                lease_duration_s=lease_duration_for(options.deadline_s),
                config=ledger_config,
            )
            if reservation_id is not None
            else nullcontext()
        )
        try:
            backend = backend_factory(ref.backend)
            with lease:
                response = chat_one_candidate(
                    backend,
                    msg_list,
                    model=ref.model_id,
                    max_tokens=options.max_tokens,
                    temperature=options.temperature,
                    deadline_s=options.deadline_s,
                    retries=retries,
                )
            return ExecutionResult(
                response=response,
                model_ref=ref,
                reserved_credits=reserved_credits,
                notes=tuple(notes),
                reservation_id=reservation_id,
            )
        except Exception as exc:
            disp = disposition_of(exc)
            if disp is CandidateDisposition.ABORT:
                # Request-level permanent refusal — stop the chain and re-raise.
                raise
            notes.append(f"{ref.model_id!r}: {disp.value}: {type(exc).__name__}: {exc}")
        finally:
            if reservation_id is not None:
                # Retain the hold (settle → settling) on ANY outcome — never
                # release at call-return (FR-016); the reconciler/sweeper finalizes
                # it against observed spend. A settle failure must not mask the call.
                try:
                    settle(ledger_repo, reservation_id, now=now, config=ledger_config)  # type: ignore[arg-type]
                except Exception as exc:  # best-effort; the sweeper backstops a lost settle
                    logger.warning("execute: settle(%s) failed: %s", reservation_id, exc)

    raise ChainExhausted(
        f"execute: chain of {len(chain.candidates)} candidate(s) exhausted without success; "
        f"notes={notes}"
    )


__all__ = ["ChainExhausted", "ExecutionResult", "execute"]
