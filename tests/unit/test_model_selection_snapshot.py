"""Slice 1 (spec 026) — offline unit tests for the snapshot contracts + helpers.

Deterministic; no network. The real composite fetch is exercised in
``tests/real_call/test_model_selection_snapshot_real.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from llmxive.model_selection.snapshot import _family_of, _vendor_of
from llmxive.model_selection.types import (
    CallBudget,
    ModelPricing,
    worst_case_credits,
)


@pytest.mark.parametrize(
    "model_id,vendor,family",
    [
        ("qwen.qwen3.5-122b", "qwen", "qwen3.5"),
        ("openai.gpt-oss-120b", "openai", "gpt-oss"),
        ("google.gemma-4-31B-it", "google", "gemma-4"),
        ("google.gemma-3-27b-it", "google", "gemma-3"),
        ("Qwen/Qwen2.5-3B-Instruct", "qwen", "qwen2.5"),
        ("anthropic.claude-haiku-4-5-20251001", "anthropic", "claude-haiku-4-5"),
    ],
)
def test_vendor_and_family_derivation(model_id: str, vendor: str, family: str) -> None:
    assert _vendor_of(model_id) == vendor
    assert _family_of(model_id, vendor) == family


def test_family_derivation_is_deterministic() -> None:
    mid = "google.gemma-4-31B-it"
    assert _family_of(mid, "google") == _family_of(mid, "google")


def test_unknown_price_is_not_free() -> None:
    p = ModelPricing(input_usd_per_token=None, output_usd_per_token=None)
    assert not p.is_free
    assert not p.is_known
    # worst_case_credits refuses to price an unknown model (never free)
    assert worst_case_credits(p, CallBudget(1000, 500)) is None


def test_zero_price_is_free_and_known() -> None:
    p = ModelPricing(input_usd_per_token=0.0, output_usd_per_token=0.0)
    assert p.is_free and p.is_known
    assert worst_case_credits(p, CallBudget(1000, 500)) == 0.0


def test_worst_case_credits_usd_to_credits_conversion() -> None:
    # $1/M-in, $5/M-out  ->  1e-6 / 5e-6 USD per token
    p = ModelPricing(input_usd_per_token=1e-6, output_usd_per_token=5e-6)
    # 1000 in * 1e-6 + 500 out * 5e-6 = 0.001 + 0.0025 = 0.0035 USD -> *1000 = 3.5 credits
    assert worst_case_credits(p, CallBudget(1000, 500)) == pytest.approx(3.5)


def test_input_and_output_rates_applied_separately() -> None:
    p = ModelPricing(input_usd_per_token=2e-6, output_usd_per_token=0.0)
    # only input priced: 1000 * 2e-6 = 0.002 USD -> 2 credits
    assert worst_case_credits(p, CallBudget(1000, 9999)) == pytest.approx(2.0)


def _live_credit(now: datetime):
    from llmxive.model_selection.types import CreditGuardSnapshot

    return CreditGuardSnapshot(
        balance=100.0, spend=10.0, max_budget=200.0, paid_opt_in=True,
        budget_fraction=0.75, effective_cap=150.0, available_headroom=140.0,
        budget_reset_at="2026-07-17T03:45:00Z", observed_at=now, source="live",
    )


def test_runtime_snapshot_is_deterministic_and_provenanced(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Snapshot assembly is deterministic given fixed live fetches (the test seam)
    — no network — and every component carries live provenance (source+age)."""
    import llmxive.model_selection.snapshot as snap_mod
    from llmxive.model_selection.lkg import LKGStore
    from llmxive.model_selection.types import ModelRef

    ref = ModelRef("dartmouth", "https://x", "qwen.qwen3.5-122b", "qwen3.5", "qwen")
    price = {"qwen.qwen3.5-122b": ModelPricing(0.0, 0.0)}
    fixed_now = datetime(2026, 7, 16, tzinfo=UTC)
    monkeypatch.setattr(snap_mod, "_fetch_dartmouth", lambda: ([ref], price))
    monkeypatch.setattr(snap_mod, "_fetch_local", lambda: ([], {}))
    monkeypatch.setattr(snap_mod, "_fetch_credit", lambda *, now: _live_credit(now))

    store = LKGStore(tmp_path / "lkg.json")
    a = snap_mod.runtime_snapshot(now=fixed_now, lkg_store=store)
    b = snap_mod.runtime_snapshot(now=fixed_now, lkg_store=store)
    assert a.digest == b.digest  # same inputs -> same digest
    assert {k: p.source for k, p in a.sources.items()} == {
        "catalog": "live", "local": "live", "credit": "live"
    }
    assert all(p.age_s == 0.0 and p.observed_at == fixed_now for p in a.sources.values())
    assert a.models[0].model_id == "qwen.qwen3.5-122b"
    assert a.credit.source == "live"


def test_digest_reflects_component_source(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Identical model data but a different component source (live vs
    last_known_good) yields a DIFFERENT digest — the source affects what select
    admits (FR-007), so it must bind the decision identity."""
    import llmxive.model_selection.snapshot as snap_mod
    from llmxive.model_selection.lkg import LKGStore
    from llmxive.model_selection.types import ModelRef

    ref = ModelRef("dartmouth", "https://x", "qwen.qwen3.5-122b", "qwen3.5", "qwen")
    price = {"qwen.qwen3.5-122b": ModelPricing(0.0, 0.0)}
    t0 = datetime(2026, 7, 16, tzinfo=UTC)
    monkeypatch.setattr(snap_mod, "_fetch_local", lambda: ([], {}))
    monkeypatch.setattr(snap_mod, "_fetch_credit", lambda *, now: _live_credit(now))

    store = LKGStore(tmp_path / "lkg.json")
    monkeypatch.setattr(snap_mod, "_fetch_dartmouth", lambda: ([ref], price))
    live = snap_mod.runtime_snapshot(now=t0, lkg_store=store)
    # catalog now fails -> served from LKG (same models, source flips to lkg)
    monkeypatch.setattr(snap_mod, "_fetch_dartmouth", lambda: None)
    from_lkg = snap_mod.runtime_snapshot(now=t0, lkg_store=store)
    assert from_lkg.sources["catalog"].source == "last_known_good"
    assert {m.model_id for m in from_lkg.models} == {m.model_id for m in live.models}
    assert live.digest != from_lkg.digest
