"""Funded (Hugging Face) allowance guard — spec 027 section 5.6 and decision 5.9.6.

Turns the funded ledger (``refs/llmxive/funded-ledger``, USD, monthly epoch) into
"how much may this run reserve right now". All dates are UTC: the epoch is the UTC
calendar month (``YYYY-MM``) and "today" is the UTC calendar day.

Pacing: at the start of each UTC day, the money left in the month is spread evenly
over the days left (counting today). A run may spend today's share plus
``BORROW_AHEAD_DAYS`` more days' worth, never past what is left in the month, so an
idle day rolls forward and a heavy day cannot spend the month. When the organisation
credits endpoint is readable it is a cross-check: if the org balance is below the
remaining allowance, the lower number wins. A failed or refused cross-check (the CI
token usually lacks ``org.billing.read``) falls back to the ledger-derived allowance
alone and is recorded as ``org_balance_usd=None`` — never treated as unlimited.

The admission predicate itself is :func:`llmxive.model_selection.reservations.admits`
(``spend + counting + worst_case <= cap``); this module only supplies the
:class:`~llmxive.model_selection.reservations.CreditObservation` it is evaluated
against (:func:`funded_observer`), so concurrent runners are bounded by the same
strict-CAS reserve that guards paid Dartmouth calls.
"""

from __future__ import annotations

import calendar
import logging
import math
import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import httpx

from llmxive.backends.huggingface import BILL_TO_ENV
from llmxive.credentials import load_hf_token

if TYPE_CHECKING:  # model_selection imports stay function-local at runtime
    from llmxive.model_selection.ledger_transport import LedgerConfig
    from llmxive.model_selection.reservations import CreditObservation, Reservation
    from llmxive.model_selection.types import FundedGuardSnapshot

logger = logging.getLogger(__name__)

MONTHLY_USD_ENV = "LLMXIVE_HF_MONTHLY_USD"
DEFAULT_MONTHLY_USD = 50.0
#: Days of allowance a run may borrow beyond today's share (spec 5.9.6).
BORROW_AHEAD_DAYS = 3
ORG_CREDITS_URL = "https://huggingface.co/api/organizations/contextlab/billing/credits"


class FundedUnavailable(RuntimeError):
    """The funded class cannot be used right now (missing bill-to id, token, ledger
    anchor, or ledger sync). Fail closed: no funded call is admitted."""


def _utc(ts: datetime) -> datetime:
    """``ts`` in UTC. A naive datetime is ambiguous for money pacing, so it is refused."""
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise ValueError(f"funded allowance needs a timezone-aware datetime, got naive {ts!r}")
    return ts.astimezone(UTC)


def monthly_allowance_usd() -> float:
    """The monthly allowance from ``LLMXIVE_HF_MONTHLY_USD``. Unset or blank (an unset
    Actions ``vars.*`` expands to ``""``) → :data:`DEFAULT_MONTHLY_USD`. Unparsable,
    negative or non-finite → ``0.0`` with a warning (fail closed: no funded spend)."""
    raw = os.environ.get(MONTHLY_USD_ENV, "").strip()
    if not raw:
        return DEFAULT_MONTHLY_USD
    try:
        value = float(raw)
    except ValueError:
        value = math.nan
    if not math.isfinite(value) or value < 0:
        logger.warning(
            "%s=%r is not a finite non-negative number; funded allowance set to 0 (fail closed)",
            MONTHLY_USD_ENV, raw,
        )
        return 0.0
    return value


def epoch_of(now: datetime) -> str:
    """The funded budget epoch: the UTC calendar month, ``YYYY-MM``."""
    return _utc(now).strftime("%Y-%m")


def days_left_in_month(now: datetime) -> int:
    """Days left in the UTC month, counting today (the last day of a month → 1)."""
    u = _utc(now)
    return calendar.monthrange(u.year, u.month)[1] - u.day + 1


def allowance_cap_usd(
    *,
    monthly_usd: float,
    spent_month_usd: float,
    spent_before_today_usd: float,
    now: datetime,
    org_balance_usd: float | None = None,
) -> float:
    """The month-to-date spend ceiling ``reservations.admits`` compares against.

    Today's share is what was left at the start of the UTC day divided by the days
    left; a run may use that share plus :data:`BORROW_AHEAD_DAYS` more, capped at what
    was left in the month. ``org_balance_usd`` (when known) bounds the cap at
    ``spent_month_usd + org_balance_usd`` — the lower number wins."""
    left_at_day_start = max(0.0, monthly_usd - spent_before_today_usd)
    daily = left_at_day_start / days_left_in_month(now)
    today = min(daily * (1 + BORROW_AHEAD_DAYS), left_at_day_start)
    cap = spent_before_today_usd + today
    if org_balance_usd is not None:
        cap = min(cap, spent_month_usd + org_balance_usd)
    return cap


@dataclass(frozen=True)
class FundedSpend:
    """Current-epoch spend folded from the funded ledger (USD)."""

    spent_month_usd: float  # reconciled this month (recorded charge, else the full hold)
    spent_before_today_usd: float  # reservations created before today (UTC), charge or hold
    outstanding_usd: float  # open + settling holds this month


def funded_spend(reservations: Iterable[Reservation], *, now: datetime) -> FundedSpend:
    """Fold projected reservations into this epoch's spend. Reservations from another
    epoch (a prior month's unsettled hold) do not count."""
    from llmxive.model_selection.reservations import STATE_RECONCILED, counting_total

    epoch = epoch_of(now)
    today = _utc(now).date()
    current = [r for r in reservations if r.budget_epoch == epoch]
    spent_month = 0.0
    spent_before_today = 0.0
    for r in current:
        reconciled = r.state == STATE_RECONCILED
        amount = (r.charged if r.charged is not None else r.worst_case_credits) if reconciled \
            else r.worst_case_credits
        if reconciled:
            spent_month += amount
        created = datetime.fromisoformat(r.created_at)
        if created.tzinfo is None:  # the ledger writes aware timestamps; read legacy naive as UTC
            created = created.replace(tzinfo=UTC)
        if created.astimezone(UTC).date() < today:
            spent_before_today += amount
    return FundedSpend(
        spent_month_usd=spent_month,
        spent_before_today_usd=spent_before_today,
        outstanding_usd=counting_total(current, epoch=epoch),
    )


def parse_org_credits(payload: dict) -> float:
    """``payload["balanceUsd"]`` from the org credits endpoint; ``ValueError`` unless it
    is a finite number."""
    value = payload.get("balanceUsd") if isinstance(payload, dict) else None
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f"org credits payload has no finite balanceUsd (got {value!r})")
    return float(value)


#: Hosts the Hugging Face token may be sent to: Hugging Face itself (over https) and
#: loopback (local test servers). Any other host is refused before a request is made.
_TOKEN_HOST = "huggingface.co"
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def _require_token_safe_url(url: str) -> None:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if host == _TOKEN_HOST and parts.scheme == "https":
        return
    if host in _LOOPBACK_HOSTS and parts.scheme in ("http", "https"):
        return
    raise ValueError(
        f"refusing to send the Hugging Face token to {parts.scheme}://{host or '?'}: "
        f"only https://{_TOKEN_HOST} or a loopback address is allowed"
    )


def fetch_org_balance_usd(*, timeout: float = 30.0, url: str = ORG_CREDITS_URL) -> float | None:
    """The organisation's credit balance in USD, or ``None`` on ANY failure: no token,
    a refused scope (403 — the CI token usually lacks ``org.billing.read``), another
    non-200 status, a transport error, or a malformed body. ``None`` means "cross-check
    unavailable"; callers fall back to the ledger-derived allowance alone.

    ``url`` must be ``https://huggingface.co/...`` or a loopback address (tests); any
    other host raises ``ValueError`` before a token is loaded or a request is sent."""
    _require_token_safe_url(url)
    token = load_hf_token()
    if not token:
        logger.info("org credits cross-check unavailable: no Hugging Face token")
        return None
    try:
        resp = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=timeout)
    except httpx.HTTPError as exc:
        logger.warning("org credits cross-check unavailable: %s", type(exc).__name__)
        return None
    if resp.status_code != 200:
        logger.info("org credits cross-check unavailable: HTTP %d", resp.status_code)
        return None
    try:
        return parse_org_credits(resp.json())
    except ValueError as exc:  # json.JSONDecodeError is a ValueError
        logger.warning("org credits cross-check unavailable: malformed body (%s)", type(exc).__name__)
        return None


def _require_funded_ref(config: LedgerConfig) -> None:
    from llmxive.model_selection.ledger_transport import FUNDED_LEDGER_REF

    if config.ref != FUNDED_LEDGER_REF:
        raise ValueError(
            f"funded allowance must read the funded ledger {FUNDED_LEDGER_REF}, not {config.ref}"
        )


def _cap_for(spend: FundedSpend, *, monthly_usd: float, now: datetime, org_balance_usd: float | None) -> float:
    return allowance_cap_usd(
        monthly_usd=monthly_usd,
        spent_month_usd=spend.spent_month_usd,
        spent_before_today_usd=spend.spent_before_today_usd,
        now=now,
        org_balance_usd=org_balance_usd,
    )


def funded_observer(
    repo: Path,
    *,
    config: LedgerConfig,
    now_fn: Callable[[], datetime],
    org_balance_usd: float | None = None,
) -> Callable[[], CreditObservation]:
    """A ``credit_observer`` for :func:`reservations.reserve` on the funded ledger.

    Each call reads the LOCAL funded ref — inside ``reserve`` that is the tip
    ``append_event`` has just synced from the authoritative remote on this CAS
    attempt — and returns ``spend`` = month-to-date reconciled spend, ``effective_cap``
    = :func:`allowance_cap_usd`, ``budget_epoch`` = the current UTC month.
    ``org_balance_usd`` is a cross-check value fetched once by the caller (``None`` =
    unavailable; the ledger-derived allowance alone applies).

    ``now_fn`` is REQUIRED and must be the same clock ``reserve`` stamps
    ``created_at`` with; otherwise, at a month boundary, a hold's ``budget_epoch``
    could disagree with its ``created_at``. :func:`reserve_funded` wires one clock to
    both — production callers should use it."""
    from llmxive.model_selection.ledger_transport import read_events
    from llmxive.model_selection.reservations import CreditObservation, project

    _require_funded_ref(config)

    def observe() -> CreditObservation:
        now = now_fn()
        spend = funded_spend(project(read_events(repo, ref=config.ref)).values(), now=now)
        cap = _cap_for(spend, monthly_usd=monthly_allowance_usd(), now=now, org_balance_usd=org_balance_usd)
        return CreditObservation(spend=spend.spent_month_usd, effective_cap=cap, budget_epoch=epoch_of(now))

    return observe


def reserve_funded(
    repo: Path,
    *,
    reservation_id: str,
    worst_case_usd: float,
    model: str,
    lease_expires_at: datetime,
    now: datetime,
    config: LedgerConfig,
    org_balance_usd: float | None = None,
) -> Reservation:
    """Open a funded reservation under strict CAS with ONE clock: the same ``now``
    prices the hold (epoch + cap via :func:`funded_observer`) and stamps its
    ``created_at``, so a hold can never land in a different month than it was priced
    in. Raises ``LedgerDenied`` when the allowance has no headroom."""
    from llmxive.model_selection.reservations import reserve

    return reserve(
        repo,
        reservation_id=reservation_id,
        worst_case_credits=worst_case_usd,
        model=model,
        credit_observer=funded_observer(
            repo, config=config, now_fn=lambda: now, org_balance_usd=org_balance_usd
        ),
        lease_expires_at=lease_expires_at,
        now=now,
        config=config,
    )


def funded_guard(
    repo: Path,
    *,
    now: datetime,
    config: LedgerConfig | None = None,
    org_balance_fetch: Callable[[], float | None] = fetch_org_balance_usd,
) -> FundedGuardSnapshot:
    """The funded guard snapshot for the runtime snapshot (spec 027 section 5.6).

    Raises :class:`FundedUnavailable` when the bill-to id (``LLMXIVE_HF_BILL_TO``), the
    Hugging Face token, the pinned funded-ledger anchor (when ``config`` is built from
    the environment) or the authoritative ledger sync is missing.
    ``available_usd = max(0, effective_cap_usd - spent_month_usd - outstanding_usd)``.
    A failed org cross-check is recorded as ``org_balance_usd=None``."""
    from llmxive.model_selection.ledger_transport import (
        LedgerError,
        fetch_ledger,
        funded_ledger_config_from_env,
        read_events,
    )
    from llmxive.model_selection.reservations import project
    from llmxive.model_selection.types import FundedGuardSnapshot

    if not os.environ.get(BILL_TO_ENV, "").strip():
        raise FundedUnavailable(f"funded spend disabled: {BILL_TO_ENV} is not set")
    if not load_hf_token():
        raise FundedUnavailable("funded spend disabled: no Hugging Face token (HF_TOKEN or Keychain)")
    if config is None:
        try:
            config = funded_ledger_config_from_env()
        except LedgerError as exc:
            raise FundedUnavailable(str(exc)) from exc
    _require_funded_ref(config)
    try:
        fetch_ledger(repo, config)
        reservations = project(read_events(repo, ref=config.ref)).values()
    except LedgerError as exc:
        raise FundedUnavailable(f"funded ledger unavailable: {exc}") from exc

    spend = funded_spend(reservations, now=now)
    try:
        org_balance = org_balance_fetch()
    except Exception as exc:  # a failed cross-check falls back to the ledger allowance, never "unlimited"
        logger.warning("org credits cross-check unavailable: %s", type(exc).__name__)
        org_balance = None
    monthly = monthly_allowance_usd()
    cap = _cap_for(spend, monthly_usd=monthly, now=now, org_balance_usd=org_balance)
    return FundedGuardSnapshot(
        monthly_usd=monthly,
        spent_month_usd=spend.spent_month_usd,
        spent_before_today_usd=spend.spent_before_today_usd,
        outstanding_usd=spend.outstanding_usd,
        org_balance_usd=org_balance,
        effective_cap_usd=cap,
        available_usd=max(0.0, cap - spend.spent_month_usd - spend.outstanding_usd),
        epoch=epoch_of(now),
        observed_at=now,
        source="live",
    )


def settle_funded(
    repo: Path, reservation_id: str, *, charged_usd: float | None, now: datetime, config: LedgerConfig
) -> float:
    """Reconcile a funded reservation with its actual charge. ``charged_usd=None`` (a
    call that died without a ``usage`` block) charges the reservation's full amount
    (spec 5.9.2). Returns the charge the ledger now records for it — what this call
    wrote, or, if another writer reconciled first (first writer wins), that value.
    Raises ``LedgerError`` for an id the funded ledger has never seen."""
    from llmxive.model_selection.ledger_transport import LedgerError, fetch_ledger, read_events
    from llmxive.model_selection.reservations import project, reconcile

    _require_funded_ref(config)
    fetch_ledger(repo, config)
    existing = project(read_events(repo, ref=config.ref)).get(reservation_id)
    if existing is None:
        raise LedgerError(f"settle_funded: unknown funded reservation {reservation_id!r}")
    charge = existing.worst_case_credits if charged_usd is None else charged_usd
    reconcile(repo, reservation_id, charged=charge, now=now, config=config)
    recorded = project(read_events(repo, ref=config.ref))[reservation_id]
    return recorded.charged if recorded.charged is not None else recorded.worst_case_credits


__all__ = [
    "BORROW_AHEAD_DAYS",
    "DEFAULT_MONTHLY_USD",
    "MONTHLY_USD_ENV",
    "ORG_CREDITS_URL",
    "FundedSpend",
    "FundedUnavailable",
    "allowance_cap_usd",
    "days_left_in_month",
    "epoch_of",
    "fetch_org_balance_usd",
    "funded_guard",
    "funded_observer",
    "funded_spend",
    "monthly_allowance_usd",
    "parse_org_credits",
    "reserve_funded",
    "settle_funded",
]
