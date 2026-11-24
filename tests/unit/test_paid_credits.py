"""Unit tests for the credit-managed paid-model guard (issue #295).

Offline: every balance read is supplied by an injected fetch callable
returning a real :class:`CreditBalance` value (no network, no mocks of
our own code). The live endpoint shape these values mirror was measured
on 2026-06-10: ``GET /api/v1/credits/balance`` ->
``{"account": "Personal", "spend": 0.032, "max_budget": 2000.0,
"budget_duration": "1d", "budget_reset_at": "2026-06-11T03:45:00Z"}``
(and 1 credit == $0.001 list-price equivalent, measured via a real
claude-haiku call moving spend by exactly tokens x price x 1000).
"""

from __future__ import annotations

import pytest

from llmxive.backends import credits


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch: pytest.MonkeyPatch):
    """Each test starts with no opt-in, default fraction, empty cache."""
    monkeypatch.delenv(credits.PAID_OPT_IN_ENV, raising=False)
    monkeypatch.delenv(credits.BUDGET_FRACTION_ENV, raising=False)
    monkeypatch.delenv(credits.BALANCE_TTL_ENV, raising=False)
    credits.reset_balance_cache()
    yield
    credits.reset_balance_cache()


def _balance(spend: float = 0.0, max_budget: float = 2000.0) -> credits.CreditBalance:
    return credits.CreditBalance(
        account="Personal",
        spend=spend,
        max_budget=max_budget,
        budget_duration="1d",
        budget_reset_at="2026-06-11T03:45:00Z",
    )


class TestOptInSwitch:
    def test_refused_by_default(self):
        allowed, reason = credits.paid_call_allowed(
            "anthropic.claude-haiku-4-5-20251001", fetch=lambda: _balance()
        )
        assert not allowed
        assert credits.PAID_OPT_IN_ENV in reason

    @pytest.mark.parametrize("value", ["1", "true", "YES", "on"])
    def test_truthy_values_enable(self, monkeypatch, value):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, value)
        assert credits.paid_opt_in_enabled()

    @pytest.mark.parametrize("value", ["", "0", "false", "no", "banana"])
    def test_falsy_values_stay_off(self, monkeypatch, value):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, value)
        assert not credits.paid_opt_in_enabled()


class TestBudgetCap:
    def test_allowed_under_cap(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        allowed, reason = credits.paid_call_allowed(
            "anthropic.claude-haiku-4-5-20251001",
            fetch=lambda: _balance(spend=10.0),
        )
        assert allowed
        assert "allowed" in reason

    def test_refused_at_cap(self, monkeypatch):
        # default fraction 0.75 of 2000.0 -> cap 1500.0
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        allowed, reason = credits.paid_call_allowed(
            "anthropic.claude-opus-4-8", fetch=lambda: _balance(spend=1500.0)
        )
        assert not allowed
        assert "cap" in reason

    def test_custom_fraction(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        monkeypatch.setenv(credits.BUDGET_FRACTION_ENV, "0.10")
        # cap = 200.0; spend 250 must refuse
        allowed, _ = credits.paid_call_allowed(
            "anthropic.claude-opus-4-8", fetch=lambda: _balance(spend=250.0)
        )
        assert not allowed

    def test_zero_max_budget_refused(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        allowed, reason = credits.paid_call_allowed(
            "anthropic.claude-opus-4-8",
            fetch=lambda: _balance(spend=0.0, max_budget=0.0),
        )
        assert not allowed
        assert "max_budget" in reason

    def test_bad_fraction_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv(credits.BUDGET_FRACTION_ENV, "not-a-number")
        assert credits.budget_fraction() == credits.DEFAULT_BUDGET_FRACTION

    def test_fraction_clamped(self, monkeypatch):
        monkeypatch.setenv(credits.BUDGET_FRACTION_ENV, "7.5")
        assert credits.budget_fraction() == 1.0
        monkeypatch.setenv(credits.BUDGET_FRACTION_ENV, "-1")
        assert credits.budget_fraction() == 0.0


class TestFailClosed:
    def test_fetch_failure_refuses(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")

        def boom() -> credits.CreditBalance:
            raise ConnectionError("endpoint down")

        allowed, reason = credits.paid_call_allowed(
            "anthropic.claude-opus-4-8", fetch=boom
        )
        assert not allowed
        assert "failing closed" in reason


class TestBalanceCache:
    def test_within_ttl_reuses_fetch(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        calls = []

        def counting_fetch() -> credits.CreditBalance:
            calls.append(1)
            return _balance(spend=1.0)

        for _ in range(3):
            allowed, _ = credits.paid_call_allowed("m", fetch=counting_fetch)
            assert allowed
        assert len(calls) == 1  # cached within the 30s default TTL

    def test_reset_forces_refetch(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        calls = []

        def counting_fetch() -> credits.CreditBalance:
            calls.append(1)
            return _balance(spend=1.0)

        credits.paid_call_allowed("m", fetch=counting_fetch)
        credits.reset_balance_cache()
        credits.paid_call_allowed("m", fetch=counting_fetch)
        assert len(calls) == 2

    def test_zero_ttl_disables_cache(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        monkeypatch.setenv(credits.BALANCE_TTL_ENV, "0")
        calls = []

        def counting_fetch() -> credits.CreditBalance:
            calls.append(1)
            return _balance(spend=1.0)

        credits.paid_call_allowed("m", fetch=counting_fetch)
        credits.paid_call_allowed("m", fetch=counting_fetch)
        assert len(calls) == 2


class TestCreditBalanceValue:
    def test_remaining_and_usd(self):
        b = _balance(spend=500.0)
        assert b.remaining == 1500.0
        assert b.usd_equivalent_spend == pytest.approx(0.5)

    def test_remaining_never_negative(self):
        b = _balance(spend=9999.0)
        assert b.remaining == 0.0


class TestReservationAwareGuard:
    """spec 026 FR-011: the twice-checked paid gate — the guard owns the full
    ``spend + outstanding + estimated_cost ≤ cap`` comparison, reusing the ONE
    canonical ``reservations.admits`` predicate."""

    def test_fits_within_cap(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        # cap = 0.75*2000 = 1500; 100 + 1000 + 300 = 1400 ≤ 1500
        allowed, _ = credits.paid_call_allowed(
            "anthropic.claude-haiku-4-5-20251001",
            fetch=lambda: _balance(spend=100.0),
            estimated_cost_credits=300.0,
            outstanding_reservation_credits=1000.0,
        )
        assert allowed is True

    def test_boundary_equal_cap_admitted(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        # exactly at the cap is admitted (predicate is ≤)
        allowed, _ = credits.paid_call_allowed(
            "m", fetch=lambda: _balance(spend=500.0),
            estimated_cost_credits=500.0, outstanding_reservation_credits=500.0,
        )
        assert allowed is True  # 1500 ≤ 1500

    def test_outstanding_reservations_push_over_cap(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        # the SAME call that passes the plain cap (spend 100 < 1500) is refused once
        # outstanding reservations are counted: 100 + 1000 + 500 = 1600 > 1500.
        allowed, reason = credits.paid_call_allowed(
            "m", fetch=lambda: _balance(spend=100.0),
            estimated_cost_credits=500.0, outstanding_reservation_credits=1000.0,
        )
        assert allowed is False
        assert "outstanding reservations" in reason

    def test_reservation_mode_bypasses_cache(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        calls = {"n": 0}

        def counting_fetch() -> credits.CreditBalance:
            calls["n"] += 1
            return _balance(spend=10.0)

        for _ in range(3):
            credits.paid_call_allowed(
                "m", fetch=counting_fetch, estimated_cost_credits=1.0,
            )
        assert calls["n"] == 3  # fresh read every time (no 30s cache reuse)

    def test_negative_inputs_refused(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        allowed, _ = credits.paid_call_allowed(
            "m", fetch=lambda: _balance(), estimated_cost_credits=-1.0,
        )
        assert allowed is False

    def test_opt_in_off_refuses_in_reservation_mode(self):
        allowed, _ = credits.paid_call_allowed(
            "m", fetch=lambda: _balance(), estimated_cost_credits=1.0,
        )
        assert allowed is False

    def test_fetch_failure_refuses_in_reservation_mode(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")

        def boom() -> credits.CreditBalance:
            raise RuntimeError("balance endpoint down")

        allowed, reason = credits.paid_call_allowed(
            "m", fetch=boom, estimated_cost_credits=1.0,
        )
        assert allowed is False
        assert "failing closed" in reason


class TestFreshPaidHeadroomAvailable:
    """spec 026 Slice 6: the canonical coarse escalation-ladder gate — is paid
    globally enabled AND is there daily headroom RIGHT NOW? All paid-headroom
    arithmetic stays in this module (Constitution I)."""

    def test_headroom_opt_in_off_false(self, monkeypatch):
        monkeypatch.delenv(credits.PAID_OPT_IN_ENV, raising=False)
        ok, reason = credits.fresh_paid_headroom_available(
            fetch=lambda: _balance(spend=0.0, max_budget=1000.0)
        )
        assert ok is False and "opt-in" in reason.lower()

    def test_headroom_positive_true(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        monkeypatch.delenv(credits.BUDGET_FRACTION_ENV, raising=False)  # default 0.75
        ok, _ = credits.fresh_paid_headroom_available(
            fetch=lambda: _balance(spend=100.0, max_budget=1000.0)
        )
        assert ok is True  # cap 750 - spend 100 = 650 > 0

    def test_headroom_exhausted_false(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        ok, _ = credits.fresh_paid_headroom_available(
            fetch=lambda: _balance(spend=800.0, max_budget=1000.0)
        )
        assert ok is False  # cap 750 <= spend 800

    def test_headroom_nonfinite_fails_closed(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        ok, _ = credits.fresh_paid_headroom_available(
            fetch=lambda: _balance(spend=float("nan"), max_budget=1000.0)
        )
        assert ok is False

    def test_headroom_zero_max_budget_fails_closed(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")
        ok, reason = credits.fresh_paid_headroom_available(
            fetch=lambda: _balance(spend=0.0, max_budget=0.0)
        )
        assert ok is False and "max_budget" in reason

    def test_headroom_fetch_error_fails_closed(self, monkeypatch):
        monkeypatch.setenv(credits.PAID_OPT_IN_ENV, "1")

        def boom() -> credits.CreditBalance:
            raise RuntimeError("network")

        ok, reason = credits.fresh_paid_headroom_available(fetch=boom)
        assert ok is False and "failing closed" in reason.lower()
