"""Escalation ladder as REQUIREMENT constraints, not model-id literals (spec 026
slice 6). Drives the REAL ``execution_status`` tier functions + the REAL
``RequirementOverrides`` value — no mocks (Constitution III)."""

from __future__ import annotations

import pytest

from llmxive.state import execution_status as es


@pytest.fixture(autouse=True)
def _free_first(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    monkeypatch.delenv("LLMXIVE_EXECUTION_PAID_ESCALATION", raising=False)
    monkeypatch.delenv("LLMXIVE_EXECUTION_PAID_TIERS", raising=False)


def test_tier0_is_free_only_even_when_opt_in_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    ov = es.tier_constraint(0).to_overrides()
    assert ov.allow_paid is False and ov.require_paid is False
    assert ov.exclude_leader is False
    assert ov.exclude_models == frozenset()


def test_tier1_free_second_opinion_sets_exclude_leader() -> None:
    ov = es.tier_constraint(1).to_overrides()
    assert ov.allow_paid is False
    assert ov.exclude_leader is True
    assert ov.exclude_models == frozenset()


def test_corrupt_tier_resolves_free_only() -> None:
    for bad in (-1, True, 2.5, "1", 10**9):
        c = es.tier_constraint(bad)  # type: ignore[arg-type]
        assert c.allow_paid is False and c.require_paid is False


def test_corrupt_tier_resolves_free_only_even_with_paid_rung(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The corrupt-tier→free-only invariant is only meaningful when a paid rung
    EXISTS at the end of the ladder — otherwise every rung is free anyway and a
    re-introduced last-rung clamp would go undetected. Lock it WITH the paid
    rung present (real env, no mocks)."""
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")  # ladder gains a paid rung
    assert len(es.model_tier_ladder()) == 3  # two free rungs + one paid rung
    for bad in (-1, True, 2.5, "1", 10**9):
        c = es.tier_constraint(bad)  # type: ignore[arg-type]
        assert c.is_paid is False and c.allow_paid is False  # never the paid rung
    # A stale in-range paid tier index resolves to free once paid is disabled:
    monkeypatch.delenv("LLMXIVE_EXECUTION_PAID_ESCALATION", raising=False)
    assert es.tier_constraint(2).is_paid is False  # 2 >= len(free-only ladder) -> ladder[0]


def test_paid_rung_present_only_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    assert all(not c.is_paid for c in es.model_tier_ladder())  # free-only default
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")
    ladder = es.model_tier_ladder()
    assert sum(c.is_paid for c in ladder) == 1  # exactly one paid rung
    paid = next(c for c in ladder if c.is_paid)
    assert paid.allow_paid is True and paid.require_paid is True


def test_paid_rung_to_overrides_is_require_paid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")
    ov = es.model_tier_ladder()[-1].to_overrides()
    assert ov.allow_paid is True and ov.require_paid is True


def test_env_precedence_new_zero_beats_legacy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_TIERS", "anthropic.claude-haiku")
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "0")
    assert all(not c.is_paid for c in es.model_tier_ladder())  # explicit off wins


def test_env_legacy_only_enables_one_rung_with_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_TIERS", "a.b,c.d,c.d")
    # The one-time deprecation warning fires once per process; reset the latch so
    # this test observes it deterministically regardless of run order.
    monkeypatch.setattr(es, "_LEGACY_WARNED", False)
    import logging

    with caplog.at_level(logging.WARNING):
        ladder = es.model_tier_ladder()
    assert sum(c.is_paid for c in ladder) == 1
    assert sum("deprecated" in r.message.lower() for r in caplog.records) >= 1


def test_env_invalid_new_value_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "banana")
    assert all(not c.is_paid for c in es.model_tier_ladder())  # invalid → off


def test_next_usable_tier_skips_paid_when_opt_in_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")  # ladder has paid rung
    # opt-in OFF → paid unusable
    assert es.next_usable_tier(0) == 1               # free second opinion
    assert es.next_usable_tier(1) is None            # paid skipped (opt-in off)


def test_fabrication_free_only_never_reaches_paid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")
    monkeypatch.setattr(es, "paid_tier_usable", lambda: True)  # opt-in ON, headroom
    assert es.next_usable_tier(1) == 2                       # paid reachable generally
    assert es.next_usable_tier(1, free_only=True) is None    # ...but not free_only
    assert es.next_usable_tier(0, free_only=True) == 1
