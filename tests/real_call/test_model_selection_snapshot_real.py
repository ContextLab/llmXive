"""Slice 1 (spec 026) — REAL composite runtime_snapshot against live backends.

Gated by ``LLMXIVE_REAL_TESTS=1`` (Constitution III). Verifies the acquisition
layer assembles a composite snapshot (Dartmouth catalog + local fallback) with
correct canonical identity, USD pricing, and a fraction-aware credit-guard
observation.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="real-call test; set LLMXIVE_REAL_TESTS=1",
)


def test_runtime_snapshot_real_composite() -> None:
    from llmxive.model_selection import runtime_snapshot

    snap = runtime_snapshot()
    backends = {m.backend for m in snap.models}
    assert "dartmouth" in backends, "dartmouth models missing"
    assert "local" in backends, "local fallback missing (composite requirement)"

    byid = {m.model_id: m for m in snap.models}
    # #10: the maintainer-default model MUST be present + free (unconditional — its
    # absence is a real signal the default is down, not a reason to skip).
    assert "qwen.qwen3.5-122b" in byid, "default model qwen.qwen3.5-122b absent from catalog"
    m = byid["qwen.qwen3.5-122b"]
    assert m.vendor == "qwen" and m.model_family == "qwen3.5"
    assert m.serving_endpoint != m.vendor  # vendor is separate from serving endpoint
    assert snap.pricing["qwen.qwen3.5-122b"].is_free  # cost 0
    # the local fallback inventory is loaded into the composite (Qwen2.5-3B)
    assert "Qwen/Qwen2.5-3B-Instruct" in byid, "local fallback model not in composite snapshot"
    assert byid["Qwen/Qwen2.5-3B-Instruct"].backend == "local"

    # credit guard: fraction-aware effective cap, not raw balance-spend
    c = snap.credit
    if c.source == "live":
        assert c.effective_cap == pytest.approx(c.budget_fraction * c.max_budget)
        assert c.available_headroom == max(0.0, c.effective_cap - c.spend)
    assert snap.digest  # non-empty full-snapshot digest

    # every component records provenance (source + true age); a live fetch is age 0
    assert set(snap.sources) == {"catalog", "local", "credit", "hf_catalog", "leaderboard", "funded"}
    for prov in snap.sources.values():
        assert prov.source in ("live", "last_known_good", "unavailable")
        assert prov.age_s >= 0.0
        if prov.source == "live":
            assert prov.age_s == 0.0 and prov.observed_at == snap.observed_at
