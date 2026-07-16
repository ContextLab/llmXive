"""Slice 1 (spec 026) — offline tests for the last-known-good store + the
live → last_known_good → unavailable per-component snapshot transitions.

Deterministic; no network; the LKG store is always redirected to ``tmp_path`` so
the real ``state/model_selection/`` is never touched.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import llmxive.model_selection.snapshot as snap_mod
from llmxive.model_selection.lkg import LKG_SCHEMA_VERSION, LKGEntry, LKGStore
from llmxive.model_selection.types import CreditGuardSnapshot, ModelPricing, ModelRef

T0 = datetime(2026, 7, 16, tzinfo=UTC)
_REF = ModelRef("dartmouth", "https://x", "qwen.qwen3.5-122b", "qwen3.5", "qwen")
_PRICE = {"qwen.qwen3.5-122b": ModelPricing(0.0, 0.0)}
_LOCAL_REF = ModelRef("local", "local", "Qwen/Qwen2.5-3B-Instruct", "qwen2.5", "qwen")
_LOCAL_PRICE = {"Qwen/Qwen2.5-3B-Instruct": ModelPricing(0.0, 0.0)}


def _live_credit(now: datetime) -> CreditGuardSnapshot:
    return CreditGuardSnapshot(
        balance=100.0, spend=10.0, max_budget=200.0, paid_opt_in=True,
        budget_fraction=0.75, effective_cap=150.0, available_headroom=140.0,
        budget_reset_at="2026-07-17T03:45:00Z", observed_at=now, source="live",
    )


# --------------------------- LKGStore unit tests --------------------------- #


def test_lkg_record_then_load_roundtrips(tmp_path) -> None:
    store = LKGStore(tmp_path / "lkg.json")
    entry = LKGEntry(observed_at=T0, payload={"refs": [], "pricing": {}})
    store.record({"catalog": entry})
    loaded = store.load()
    assert set(loaded) == {"catalog"}
    assert loaded["catalog"].observed_at == T0
    assert loaded["catalog"].payload == {"refs": [], "pricing": {}}


def test_lkg_record_merges_and_preserves_untouched(tmp_path) -> None:
    store = LKGStore(tmp_path / "lkg.json")
    store.record({"catalog": LKGEntry(T0, {"a": 1})})
    t1 = T0 + timedelta(seconds=60)
    store.record({"local": LKGEntry(t1, {"b": 2})})  # catalog untouched
    loaded = store.load()
    assert set(loaded) == {"catalog", "local"}
    assert loaded["catalog"].observed_at == T0  # preserved
    assert loaded["local"].observed_at == t1


def test_lkg_record_empty_is_noop(tmp_path) -> None:
    path = tmp_path / "lkg.json"
    LKGStore(path).record({})
    assert not path.exists()


def test_lkg_missing_file_is_absent(tmp_path) -> None:
    assert LKGStore(tmp_path / "nope.json").load() == {}


def test_lkg_malformed_json_is_absent(tmp_path) -> None:
    path = tmp_path / "lkg.json"
    path.write_text("{not json", encoding="utf-8")
    assert LKGStore(path).load() == {}


def test_lkg_schema_version_mismatch_is_absent(tmp_path) -> None:
    import json

    store = LKGStore(tmp_path / "lkg.json")
    store.record({"catalog": LKGEntry(T0, {"a": 1})})
    blob = json.loads(store.path.read_text())
    blob["schema_version"] = LKG_SCHEMA_VERSION + 1  # digest still valid; version isn't
    store.path.write_text(json.dumps(blob), encoding="utf-8")
    assert store.load() == {}


def test_lkg_digest_mismatch_is_absent(tmp_path) -> None:
    import json

    store = LKGStore(tmp_path / "lkg.json")
    store.record({"catalog": LKGEntry(T0, {"a": 1})})
    blob = json.loads(store.path.read_text())
    blob["components"]["catalog"]["payload"] = {"a": 999}  # tamper without fixing digest
    store.path.write_text(json.dumps(blob), encoding="utf-8")
    assert store.load() == {}


# ------------------ snapshot per-component LKG transitions ------------------ #


def _patch_fetches(monkeypatch, *, dartmouth, local, credit) -> None:
    monkeypatch.setattr(snap_mod, "_fetch_dartmouth", dartmouth)
    monkeypatch.setattr(snap_mod, "_fetch_local", local)
    monkeypatch.setattr(snap_mod, "_fetch_credit", credit)


def test_live_then_lkg_then_unavailable(monkeypatch, tmp_path) -> None:
    store = LKGStore(tmp_path / "lkg.json")

    # Run 1: catalog live -> records LKG.
    _patch_fetches(
        monkeypatch,
        dartmouth=lambda: ([_REF], _PRICE),
        local=lambda: ([_LOCAL_REF], _LOCAL_PRICE),
        credit=lambda *, now: _live_credit(now),
    )
    s1 = snap_mod.runtime_snapshot(now=T0, lkg_store=store)
    assert s1.sources["catalog"].source == "live"

    # Run 2: catalog fetch FAILS 1h later -> served from LKG with true age; local stays live.
    t1 = T0 + timedelta(seconds=3600)
    _patch_fetches(
        monkeypatch,
        dartmouth=lambda: None,
        local=lambda: ([_LOCAL_REF], _LOCAL_PRICE),
        credit=lambda *, now: _live_credit(now),
    )
    s2 = snap_mod.runtime_snapshot(now=t1, lkg_store=store)
    cat = s2.sources["catalog"]
    assert cat.source == "last_known_good"
    assert cat.observed_at == T0 and cat.age_s == 3600.0
    assert {m.model_id for m in s2.models} == {_REF.model_id, _LOCAL_REF.model_id}  # data preserved
    assert s2.sources["local"].source == "live"

    # Run 3 (fresh store, no LKG): catalog fetch FAILS -> cold start -> unavailable.
    empty = LKGStore(tmp_path / "empty.json")
    s3 = snap_mod.runtime_snapshot(now=t1, lkg_store=empty)
    assert s3.sources["catalog"].source == "unavailable"
    assert not any(m.backend == "dartmouth" for m in s3.models)


def test_cold_start_all_unavailable(monkeypatch, tmp_path) -> None:
    _patch_fetches(
        monkeypatch,
        dartmouth=lambda: None,
        local=lambda: None,
        credit=lambda *, now: None,
    )
    s = snap_mod.runtime_snapshot(now=T0, lkg_store=LKGStore(tmp_path / "lkg.json"))
    assert {p.source for p in s.sources.values()} == {"unavailable"}
    assert s.models == ()
    assert s.credit.source == "unavailable"


def test_corrupt_lkg_falls_through_to_unavailable(monkeypatch, tmp_path) -> None:
    path = tmp_path / "lkg.json"
    path.write_text("garbage{", encoding="utf-8")
    _patch_fetches(
        monkeypatch,
        dartmouth=lambda: None,
        local=lambda: None,
        credit=lambda *, now: None,
    )
    s = snap_mod.runtime_snapshot(now=T0, lkg_store=LKGStore(path))
    assert s.sources["catalog"].source == "unavailable"  # corrupt LKG treated as absent


def test_credit_lkg_fallback_preserves_datum_with_age(monkeypatch, tmp_path) -> None:
    store = LKGStore(tmp_path / "lkg.json")
    _patch_fetches(
        monkeypatch,
        dartmouth=lambda: ([_REF], _PRICE),
        local=lambda: ([], {}),
        credit=lambda *, now: _live_credit(now),
    )
    snap_mod.runtime_snapshot(now=T0, lkg_store=store)  # records credit LKG

    t1 = T0 + timedelta(seconds=120)
    _patch_fetches(
        monkeypatch,
        dartmouth=lambda: ([_REF], _PRICE),
        local=lambda: ([], {}),
        credit=lambda *, now: None,  # credit fetch fails
    )
    s = snap_mod.runtime_snapshot(now=t1, lkg_store=store)
    assert s.credit.source == "last_known_good"
    assert s.credit.available_headroom == 140.0  # datum preserved
    assert s.credit.observed_at == T0
    assert s.sources["credit"].age_s == 120.0
