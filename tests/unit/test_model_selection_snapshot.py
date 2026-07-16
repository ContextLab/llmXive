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


def test_runtime_snapshot_is_injectable_now(monkeypatch: pytest.MonkeyPatch) -> None:
    """Snapshot assembly is deterministic given fixed component fetches (the
    test seam) — no network required."""
    import llmxive.model_selection.snapshot as snap_mod
    from llmxive.model_selection.types import CreditGuardSnapshot, ModelRef

    ref = ModelRef("dartmouth", "https://x", "qwen.qwen3.5-122b", "qwen3.5", "qwen")
    price = {"qwen.qwen3.5-122b": ModelPricing(0.0, 0.0)}
    fixed_now = datetime(2026, 7, 16, tzinfo=UTC)
    monkeypatch.setattr(snap_mod, "_dartmouth_component", lambda: ([ref], price, "live"))
    monkeypatch.setattr(snap_mod, "_local_component", lambda: ([], {}, "unavailable"))
    monkeypatch.setattr(
        snap_mod,
        "_credit_component",
        lambda *, now: CreditGuardSnapshot(
            0.0, 0.0, 0.0, False, 0.75, 0.0, 0.0, "", now, "unavailable"
        ),
    )
    a = snap_mod.runtime_snapshot(now=fixed_now)
    b = snap_mod.runtime_snapshot(now=fixed_now)
    assert a.digest == b.digest  # same inputs -> same digest
    assert a.sources == {"catalog": "live", "local": "unavailable", "credit": "unavailable"}
    assert a.models[0].model_id == "qwen.qwen3.5-122b"
