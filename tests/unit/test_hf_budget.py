"""Funded allowance guard (spec 027 section 5.6 / 5.9.6): pure arithmetic at calendar
edges, the monthly-allowance env, and the org-credits cross-check against a real local
HTTP server (never the live billing endpoint)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from llmxive.backends.hf_budget import (
    DEFAULT_MONTHLY_USD,
    MONTHLY_USD_ENV,
    allowance_cap_usd,
    days_left_in_month,
    epoch_of,
    fetch_org_balance_usd,
    monthly_allowance_usd,
    parse_org_credits,
)
from tests.helpers.replay_server import ReplayServer


def U(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


@pytest.mark.parametrize("monthly,month,before,now,org,expected", [      # Review Focus 2
    (50.0, 12.0, 10.0, U("2026-11-23T12:00:00"), None, 30.0),            # 40 left / 8 days = 5/day; 4 days' worth = 20
    (50.0, 12.0, 10.0, U("2026-11-23T12:00:00"), 3.0, 15.0),             # org balance below remaining → lower wins
    (50.0, 40.0, 40.0, U("2026-11-30T23:59:59"), None, 50.0),            # last day: borrow capped by the month
    (50.0, 0.0, 0.0,  U("2026-12-01T00:00:00"), None, 4 * 50.0 / 31),    # first instant of the next month
    (50.0, 60.0, 60.0, U("2026-11-23T12:00:00"), None, 60.0),            # already over: cap == spend, zero headroom
    (29.0, 0.0, 0.0,  U("2028-02-29T10:00:00"), None, 29.0),             # leap day is the last day
])
def test_allowance_cap_table(monthly, month, before, now, org, expected):
    assert allowance_cap_usd(monthly_usd=monthly, spent_month_usd=month, spent_before_today_usd=before,
                             now=now, org_balance_usd=org) == pytest.approx(expected)


def test_days_left_and_epoch_use_utc():
    assert [days_left_in_month(U(d)) for d in ("2026-11-23T00:00:00", "2026-11-30T12:00:00", "2026-12-01T00:00:00", "2027-02-01T00:00:00")] == [8, 1, 31, 28]
    assert epoch_of(datetime.fromisoformat("2026-11-30T20:00:00-05:00")) == "2026-12"


def test_days_left_converts_offset_times_to_utc():
    # 2026-11-30 20:00 US-Eastern is already 2026-12-01 in UTC: a fresh month.
    assert days_left_in_month(datetime.fromisoformat("2026-11-30T20:00:00-05:00")) == 31


def test_naive_now_is_rejected():
    with pytest.raises(ValueError, match="timezone"):
        epoch_of(datetime(2026, 11, 23, 12, 0, 0))
    with pytest.raises(ValueError, match="timezone"):
        days_left_in_month(datetime(2026, 11, 23, 12, 0, 0))


def test_monthly_allowance_env(monkeypatch):
    monkeypatch.delenv(MONTHLY_USD_ENV, raising=False)
    assert monthly_allowance_usd() == 50.0
    monkeypatch.setenv(MONTHLY_USD_ENV, "20")
    assert monthly_allowance_usd() == 20.0
    for bad in ("abc", "-5", "nan"):
        monkeypatch.setenv(MONTHLY_USD_ENV, bad)
        assert monthly_allowance_usd() == 0.0


def test_monthly_allowance_more_fail_closed_values(monkeypatch):
    for bad in ("inf", "-inf", "1e400"):
        monkeypatch.setenv(MONTHLY_USD_ENV, bad)
        assert monthly_allowance_usd() == 0.0
    monkeypatch.setenv(MONTHLY_USD_ENV, "0")
    assert monthly_allowance_usd() == 0.0
    monkeypatch.setenv(MONTHLY_USD_ENV, "   ")  # an unset Actions `vars.*` expands to ""
    assert monthly_allowance_usd() == DEFAULT_MONTHLY_USD


def test_parse_org_credits():
    assert parse_org_credits({"balanceUsd": 199.99, "balances": []}) == 199.99


@pytest.mark.parametrize("payload", [{}, {"balanceUsd": "199"}, {"balanceUsd": True},
                                     {"balanceUsd": float("nan")}, {"balanceUsd": None}])
def test_parse_org_credits_rejects_malformed(payload):
    with pytest.raises(ValueError):
        parse_org_credits(payload)


_PATH = "/api/organizations/contextlab/billing/credits"


def test_fetch_org_balance_reads_balance_with_bearer_token(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "hf_t")
    with ReplayServer({("GET", _PATH): [(200, {"balanceUsd": 12.5, "balances": []})]}) as srv:
        assert fetch_org_balance_usd(url=srv.base_url + _PATH, timeout=5.0) == 12.5
    assert srv.requests[0]["headers"]["authorization"] == "Bearer hf_t"


@pytest.mark.parametrize("status,body", [
    (403, {"error": "insufficient scope"}),   # the CI token lacks org.billing.read
    (401, {"error": "unauthorized"}),
    (500, {"error": "boom"}),
    (200, b"not json"),
    (200, {"balances": []}),                  # 200 without a balance
])
def test_fetch_org_balance_is_none_on_any_failure(monkeypatch, status, body):
    monkeypatch.setenv("HF_TOKEN", "hf_t")
    with ReplayServer({("GET", _PATH): [(status, body)]}) as srv:
        assert fetch_org_balance_usd(url=srv.base_url + _PATH, timeout=5.0) is None


def test_fetch_org_balance_is_none_when_unreachable(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "hf_t")
    with ReplayServer({}) as srv:
        url = srv.base_url + _PATH
    assert fetch_org_balance_usd(url=url, timeout=2.0) is None  # server already shut down


@pytest.mark.parametrize("bad_url", [
    "https://evil.example/api/organizations/contextlab/billing/credits",
    "http://huggingface.co/api/organizations/contextlab/billing/credits",   # token never over plain http
    "https://huggingface.co.evil.example/x",
    "https://10.0.0.5/x",
])
def test_fetch_org_balance_refuses_to_send_the_token_elsewhere(monkeypatch, bad_url):
    monkeypatch.setenv("HF_TOKEN", "hf_t")
    with pytest.raises(ValueError, match="refusing to send"):
        fetch_org_balance_usd(url=bad_url, timeout=2.0)


def test_fetch_org_balance_non_allowed_host_gets_no_request(monkeypatch):
    # A real server reached through a name that is not on the allow-list: nothing arrives.
    monkeypatch.setenv("HF_TOKEN", "hf_t")
    with ReplayServer({("GET", _PATH): [(200, {"balanceUsd": 1.0})]}) as srv:
        port = srv.base_url.rsplit(":", 1)[1]
        with pytest.raises(ValueError, match="refusing to send"):
            fetch_org_balance_usd(url=f"http://0.0.0.0:{port}{_PATH}", timeout=2.0)
    assert srv.requests == []


def test_fetch_org_balance_accepts_localhost_names(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "hf_t")
    with ReplayServer({("GET", _PATH): [(200, {"balanceUsd": 3.0})]}) as srv:
        port = srv.base_url.rsplit(":", 1)[1]
        assert fetch_org_balance_usd(url=f"http://localhost:{port}{_PATH}", timeout=5.0) == 3.0


def test_fetch_org_balance_without_a_token_makes_no_request(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setenv("PATH", "/nonexistent")  # no Keychain CLI either → no token
    with ReplayServer({("GET", _PATH): [(200, {"balanceUsd": 1.0})]}) as srv:
        assert fetch_org_balance_usd(url=srv.base_url + _PATH, timeout=5.0) is None
    assert srv.requests == []
