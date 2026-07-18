"""Dartmouth Chat daily-credit accounting + the paid-model guard.

Issue #295 scope item 3 (audit #294 Phase 3): Dartmouth Chat grants each
user a *daily* budget of paid-model credits — measured live on 2026-06-10:

- ``GET {chat base}/api/v1/credits/balance`` returns
  ``{"account": "Personal", "spend": <credits>, "max_budget": 2000.0,
  "budget_duration": "1d", "budget_reset_at": "<iso8601>"}``.
- **1 credit == $0.001 USD-equivalent** (measured: a 12-in/4-out-token
  claude-haiku call with catalog prices $1/M-in $5/M-out moved ``spend`` by
  exactly 0.032 credits — a 1000x credits-per-USD ratio). The full daily
  2000.00 credits therefore correspond to ~$2.00/day of list-price usage.
- The budget renews daily (observed reset 03:45Z = 11:45 PM ET, matching
  the maintainer's report on issue #295).

Because the credits cost the project $0 in actual money and renew daily,
spending them carefully still satisfies Constitution IV (free-first), per
the maintainer's direction on #295: credits must be (a) managed carefully
and (b) never exceeded. This module is that management layer:

- Paid calls are OFF by default. They require BOTH the process-level
  master switch ``LLMXIVE_PAID_OPT_IN=1`` AND headroom under the daily
  budget cap (``LLMXIVE_PAID_BUDGET_FRACTION``, default 0.75 — paid calls
  stop once spend reaches 75% of ``max_budget``, leaving a reserve so
  concurrent runs / accounting lag can never blow the budget).
- FAIL-CLOSED: if the balance endpoint is unreachable or returns
  something unparseable, paid calls are refused (free models are wholly
  unaffected — they never consult this module).
- The balance is cached briefly (``LLMXIVE_CREDIT_BALANCE_TTL_S``,
  default 30s) so bursts of paid calls don't hammer the endpoint; the
  reserve fraction is what makes the short staleness window safe.

Per-agent opt-in remains declared in ``agents/registry.yaml`` via
``paid_opt_in: true`` (the only sanctioned way to *configure* a paid
default model — pinned by tests/unit/test_config_consistency.py); this
module enforces the *runtime* budget side of that contract.
"""

from __future__ import annotations

import logging
import math
import os
import time
from collections.abc import Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

#: Master switch for paid-model calls (process level). Default OFF.
PAID_OPT_IN_ENV = "LLMXIVE_PAID_OPT_IN"

#: Fraction of the daily max_budget paid calls may consume (default 0.75).
BUDGET_FRACTION_ENV = "LLMXIVE_PAID_BUDGET_FRACTION"
DEFAULT_BUDGET_FRACTION = 0.75

#: How long a fetched balance may be reused before re-fetching (seconds).
BALANCE_TTL_ENV = "LLMXIVE_CREDIT_BALANCE_TTL_S"
DEFAULT_BALANCE_TTL_S = 30.0


@dataclass(frozen=True)
class CreditBalance:
    """A point-in-time snapshot of the Dartmouth daily credit budget."""

    account: str
    spend: float
    max_budget: float
    budget_duration: str
    budget_reset_at: str

    @property
    def remaining(self) -> float:
        return max(0.0, self.max_budget - self.spend)

    @property
    def usd_equivalent_spend(self) -> float:
        """Approximate USD value of ``spend`` (1 credit == $0.001)."""
        return self.spend / 1000.0


def _credits_url() -> str:
    """The credit-balance endpoint, derived from the same chat base URL
    (and key) used for completions — see dartmouth._cloud_models_url."""
    try:
        from langchain_dartmouth.definitions import CLOUD_BASE_URL

        base = CLOUD_BASE_URL
    except Exception:
        base = os.environ.get("LCD_CLOUD_BASE_URL", "https://chat.dartmouth.edu/api/")
    return base.rstrip("/") + "/v1/credits/balance"


def fetch_credit_balance(*, timeout: float = 30.0) -> CreditBalance:
    """Fetch the live daily-credit balance for the configured chat key.

    Raises on any failure (network, auth, unexpected shape) — callers that
    must not crash use :func:`paid_call_allowed`, which converts every
    failure into a fail-closed refusal.
    """
    from llmxive.backends.dartmouth import _ensure_api_key_env

    _ensure_api_key_env()
    key = os.environ.get("DARTMOUTH_CHAT_API_KEY")
    if not key:
        raise RuntimeError(
            "DARTMOUTH_CHAT_API_KEY is not set (required to read the "
            "credit balance)"
        )
    import requests  # type: ignore[import-untyped]  # no stubs installed

    resp = requests.get(
        _credits_url(),
        headers={"Authorization": f"Bearer {key}"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    return CreditBalance(
        account=str(data["account"]),
        spend=float(data["spend"]),
        max_budget=float(data["max_budget"]),
        budget_duration=str(data.get("budget_duration", "")),
        budget_reset_at=str(data.get("budget_reset_at", "")),
    )


def paid_opt_in_enabled() -> bool:
    """Whether the process-level paid-model master switch is on."""
    return os.environ.get(PAID_OPT_IN_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def budget_fraction() -> float:
    """The fraction of max_budget paid calls may consume (clamped to [0, 1])."""
    raw = os.environ.get(BUDGET_FRACTION_ENV, "").strip()
    try:
        value = float(raw) if raw else DEFAULT_BUDGET_FRACTION
    except ValueError:
        logger.warning(
            "%s=%r is not a number; using default %.2f",
            BUDGET_FRACTION_ENV,
            raw,
            DEFAULT_BUDGET_FRACTION,
        )
        value = DEFAULT_BUDGET_FRACTION
    return min(1.0, max(0.0, value))


_BALANCE_CACHE: tuple[float, CreditBalance] | None = None


def reset_balance_cache() -> None:
    """Drop the cached balance (tests; or after a known large spend)."""
    global _BALANCE_CACHE
    _BALANCE_CACHE = None


def _cached_balance(
    fetch: Callable[[], CreditBalance],
    *,
    now: Callable[[], float] = time.monotonic,
) -> CreditBalance:
    global _BALANCE_CACHE
    raw_ttl = os.environ.get(BALANCE_TTL_ENV, "").strip()
    try:
        ttl = float(raw_ttl) if raw_ttl else DEFAULT_BALANCE_TTL_S
    except ValueError:
        ttl = DEFAULT_BALANCE_TTL_S
    t = now()
    if _BALANCE_CACHE is not None and (t - _BALANCE_CACHE[0]) < ttl:
        return _BALANCE_CACHE[1]
    balance = fetch()
    _BALANCE_CACHE = (t, balance)
    return balance


def paid_call_allowed(
    model: str,
    *,
    fetch: Callable[[], CreditBalance] | None = None,
    estimated_cost_credits: float | None = None,
    outstanding_reservation_credits: float = 0.0,
) -> tuple[bool, str]:
    """Decide whether a paid-model call to ``model`` may proceed right now.

    Returns ``(allowed, reason)``. FAIL-CLOSED: any doubt (opt-in off,
    balance unreachable, budget cap reached, nonsensical budget) refuses.
    Free models never reach this function — the backend consults it only
    after :func:`llmxive.backends.dartmouth.is_free_model` says False.

    **Reservation-aware mode (spec 026 FR-011, the twice-checked paid gate).**
    When ``estimated_cost_credits`` is given, the guard OWNS the full headroom
    comparison ``spend + outstanding_reservation_credits + estimated_cost_credits
    ≤ effective_cap`` — NOT merely "spend below cap" — reusing the ONE canonical
    predicate :func:`llmxive.model_selection.reservations.admits` (Constitution I,
    never re-implemented here). ``outstanding_reservation_credits`` is the caller's
    :func:`reservations.outstanding_headroom_consumption` (the ``open``+``settling``
    holds bridging Dartmouth's settlement lag). In this mode the balance is read
    **fresh, cache-bypassing** (the legacy ~30s cache is used ONLY for the plain
    "spend below cap" mode) so a concurrent burst cannot slip past a stale spend.
    A failed fetch → refuse (a non-live credit observation fails closed, C6).
    """
    if not paid_opt_in_enabled():
        return (
            False,
            f"paid model {model!r} refused: {PAID_OPT_IN_ENV} is not set "
            "(Constitution IV: paid credits are opt-in only)",
        )
    reserving = estimated_cost_credits is not None
    if reserving and (
        estimated_cost_credits < 0 or outstanding_reservation_credits < 0
    ):
        return (
            False,
            f"paid model {model!r} refused: estimated_cost_credits="
            f"{estimated_cost_credits!r} / outstanding_reservation_credits="
            f"{outstanding_reservation_credits!r} must be non-negative",
        )
    try:
        # Reservation-aware mode reads FRESH (cache-bypassing) spend; the plain
        # mode keeps the brief cache to avoid hammering the endpoint on bursts.
        source = fetch or fetch_credit_balance
        balance = source() if reserving else _cached_balance(source)
    except Exception as exc:
        return (
            False,
            f"paid model {model!r} refused: credit balance unavailable "
            f"({type(exc).__name__}: {exc}) — failing closed",
        )
    if balance.max_budget <= 0:
        return (
            False,
            f"paid model {model!r} refused: daily max_budget is "
            f"{balance.max_budget!r} (no paid budget on this account)",
        )
    cap = budget_fraction() * balance.max_budget
    if reserving:
        from llmxive.model_selection.reservations import admits

        if not admits(
            effective_cap=cap,
            fresh_spend=balance.spend,
            counting=outstanding_reservation_credits,
            worst_case=estimated_cost_credits,
        ):
            return (
                False,
                f"paid model {model!r} refused: fresh spend {balance.spend:.2f} + "
                f"outstanding reservations {outstanding_reservation_credits:.2f} + this "
                f"call {estimated_cost_credits:.2f} exceeds cap {cap:.2f} "
                f"(= {budget_fraction():.0%} of max_budget {balance.max_budget:.2f}; "
                f"resets at {balance.budget_reset_at})",
            )
        return (
            True,
            f"paid model {model!r} allowed: fresh spend {balance.spend:.2f} + "
            f"outstanding {outstanding_reservation_credits:.2f} + call "
            f"{estimated_cost_credits:.2f} ≤ cap {cap:.2f} "
            f"(resets at {balance.budget_reset_at})",
        )
    if balance.spend >= cap:
        return (
            False,
            f"paid model {model!r} refused: daily credit spend "
            f"{balance.spend:.2f} has reached the cap {cap:.2f} "
            f"(= {budget_fraction():.0%} of max_budget "
            f"{balance.max_budget:.2f}; resets at {balance.budget_reset_at})",
        )
    return (
        True,
        f"paid model {model!r} allowed: spend {balance.spend:.2f} / cap "
        f"{cap:.2f} credits (resets at {balance.budget_reset_at})",
    )


def fresh_paid_headroom_available(
    *, fetch: Callable[[], CreditBalance] | None = None
) -> tuple[bool, str]:
    """Coarse escalation gate (spec 026 slice 6): is paid globally enabled AND is
    there daily headroom RIGHT NOW? Reads a FRESH, cache-bypassing balance (a
    concurrent burst must not slip past a stale spend), applies the canonical
    budget_fraction, and FAILS CLOSED on any doubt. This is the ONLY paid-headroom
    arithmetic outside select()'s per-call ceiling and execute()'s authoritative
    reservation (Constitution I) — the escalation ladder delegates here rather than
    re-deriving the cap. Returns (allowed, reason)."""
    if not paid_opt_in_enabled():
        return (
            False,
            f"paid escalation refused: paid opt-in ({PAID_OPT_IN_ENV}) is not set",
        )
    try:
        balance = (fetch or fetch_credit_balance)()  # cache-bypassing (fresh)
    except Exception as exc:
        return (False, f"paid escalation refused: balance unavailable "
                       f"({type(exc).__name__}: {exc}) — failing closed")
    frac = budget_fraction()
    if not all(math.isfinite(v) for v in (balance.spend, balance.max_budget, frac)):
        return (False, "paid escalation refused: non-finite spend/max_budget/fraction "
                       "— failing closed")
    if balance.max_budget <= 0:
        return (False, f"paid escalation refused: max_budget={balance.max_budget} "
                       "(no paid budget on this account)")
    cap = frac * balance.max_budget
    headroom = cap - balance.spend
    if not (math.isfinite(cap) and math.isfinite(headroom)):
        return (False, "paid escalation refused: non-finite cap/headroom — failing closed")
    if headroom <= 0:
        return (False, f"paid escalation refused: no headroom "
                       f"(cap {cap:.2f} <= spend {balance.spend:.2f})")
    return (True, f"paid escalation allowed: headroom {headroom:.2f} "
                  f"(cap {cap:.2f}, spend {balance.spend:.2f})")


__all__ = [
    "BALANCE_TTL_ENV",
    "BUDGET_FRACTION_ENV",
    "DEFAULT_BALANCE_TTL_S",
    "DEFAULT_BUDGET_FRACTION",
    "PAID_OPT_IN_ENV",
    "CreditBalance",
    "budget_fraction",
    "fetch_credit_balance",
    "fresh_paid_headroom_available",
    "paid_call_allowed",
    "paid_opt_in_enabled",
    "reset_balance_cache",
]
