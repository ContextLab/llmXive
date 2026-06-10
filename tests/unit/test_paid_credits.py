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
