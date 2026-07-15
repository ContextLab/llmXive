"""D8 — the execution-side data-source DISCOVERY CACHE (issue #1139).

Locks the poison-cache fixes in ``llmxive.execution.data_source``:

- a TRANSIENT discovery error (timeout / connection / 5xx / 429) is NOT persisted
  and the NEXT tick re-discovers (the reproduced ``rediscovery_calls == 0`` bug);
- the cache key is a REAL key (intent + required_fields + plan-hash +
  VERIFIER_VERSION) stored INSIDE the record, so a change to any of those is a
  MISS (no stale reuse);
- ``status == "none"`` has a TTL + bounded retry count; ``verified`` is durable;
- a legacy ``status == "error"`` record (from the old poison writer) is never
  trusted — it is always re-discovered.

Only the actual discovery boundary (``discover_data_source``) and the LLM-distill
boundary (``_distill_data_need``) are stubbed; the cache-key / freshness / TTL
logic under test runs for real.
"""
from __future__ import annotations

import datetime as _dt

import requests
import yaml

import llmxive.execution.data_source as ds
import llmxive.librarian.data_source_discovery as dsd
from llmxive.librarian.data_source_discovery import VerifiedSource


def _fixed_distill(monkeypatch, intent="knot invariants dataset", fields=("crossing_number",)):
    monkeypatch.setattr(ds, "_distill_data_need", lambda raw: (intent, list(fields)))


def _source(ref="database-knotinfo", count=250):
    return VerifiedSource(
        kind="pypi_package", ref=ref,
        access_python="import database_knotinfo; print('RECORDS=%d' % 250)",
        record_count=count, sample_fields=["crossing_number"], field_coverage=1.0,
    )


def _proj(tmp_path, name="PROJ-1"):
    p = tmp_path / "projects" / name
    p.mkdir(parents=True)
    return p


# --- the reproduced poison bug: transient error not cached, and retried --------


def test_transient_error_not_cached_and_retries(tmp_path, monkeypatch):
    proj = _proj(tmp_path)
    _fixed_distill(monkeypatch)
    calls: list[str] = []

    def fake_discover(intent, required_fields=None):
        calls.append(intent)
        if len(calls) == 1:
            raise requests.exceptions.ReadTimeout(
                "HTTPSConnectionPool(host='hf.co'): Read timed out. (transient)"
            )
        return _source()

    monkeypatch.setattr(dsd, "discover_data_source", fake_discover)

    rec1 = ds.ensure_discovered_source(proj)
    assert rec1["status"] == "error"
    assert rec1["transient"] is True
    # The transient error is NOT persisted (so the next tick can retry).
    assert not ds._cache_path(proj).exists()

    rec2 = ds.ensure_discovered_source(proj)
    # rediscovery_calls > 0 after the transient error (the poison bug had 0).
    assert len(calls) == 2
    assert rec2["status"] == "verified"
    assert rec2["ref"] == "database-knotinfo"
    assert ds._cache_path(proj).exists()


def test_non_transient_error_also_not_cached(tmp_path, monkeypatch):
    proj = _proj(tmp_path, "PROJ-1b")
    _fixed_distill(monkeypatch)
    calls: list[int] = []

    def fake_discover(intent, required_fields=None):
        calls.append(1)
        if len(calls) == 1:
            raise ValueError("a real bug, not transient")
        return _source()

    monkeypatch.setattr(dsd, "discover_data_source", fake_discover)

    rec1 = ds.ensure_discovered_source(proj)
    assert rec1["status"] == "error" and rec1["transient"] is False
    assert not ds._cache_path(proj).exists()  # errors of any kind are not cached
    rec2 = ds.ensure_discovered_source(proj)
    assert len(calls) == 2 and rec2["status"] == "verified"


# --- real cache key: invalidate on intent / field / plan change ----------------


def test_cache_key_invalidates_on_intent_change(tmp_path, monkeypatch):
    proj = _proj(tmp_path, "PROJ-2")
    monkeypatch.setattr(
        dsd, "discover_data_source",
        lambda intent, required_fields=None: _source(ref="pkg-" + intent.split()[0]),
    )

    monkeypatch.setattr(ds, "_distill_data_need", lambda raw: ("alpha dataset", ["f1"]))
    rec1 = ds.ensure_discovered_source(proj)
    assert rec1["ref"] == "pkg-alpha"
    key1 = rec1["cache_key"]

    monkeypatch.setattr(ds, "_distill_data_need", lambda raw: ("beta dataset", ["f1"]))
    rec2 = ds.ensure_discovered_source(proj)
    assert rec2["cache_key"] != key1
    assert rec2["ref"] == "pkg-beta"  # re-discovered, not the stale alpha


def test_cache_key_invalidates_on_field_change(tmp_path, monkeypatch):
    proj = _proj(tmp_path, "PROJ-3")
    calls: list[list[str] | None] = []

    def fake_discover(intent, required_fields=None):
        calls.append(required_fields)
        return _source()

    monkeypatch.setattr(dsd, "discover_data_source", fake_discover)

    monkeypatch.setattr(ds, "_distill_data_need", lambda raw: ("ds", ["a"]))
    key1 = ds.ensure_discovered_source(proj)["cache_key"]
    monkeypatch.setattr(ds, "_distill_data_need", lambda raw: ("ds", ["a", "b"]))
    key2 = ds.ensure_discovered_source(proj)["cache_key"]
    assert key1 != key2
    assert len(calls) == 2  # re-discovered on the required-field change


def test_cache_key_invalidates_on_plan_change(tmp_path, monkeypatch):
    proj = _proj(tmp_path, "PROJ-4")
    _fixed_distill(monkeypatch)  # intent held constant
    calls: list[int] = []
    monkeypatch.setattr(
        dsd, "discover_data_source",
        lambda intent, required_fields=None: (calls.append(1), _source())[1],
    )

    monkeypatch.setattr(ds, "_raw_data_sections", lambda pd: "plan version A")
    key1 = ds.ensure_discovered_source(proj)["cache_key"]
    monkeypatch.setattr(ds, "_raw_data_sections", lambda pd: "plan version B — changed")
    key2 = ds.ensure_discovered_source(proj)["cache_key"]
    assert key1 != key2  # a changed plan/spec invalidates
    assert len(calls) == 2


def test_verified_is_durable_no_rediscovery(tmp_path, monkeypatch):
    proj = _proj(tmp_path, "PROJ-5")
    _fixed_distill(monkeypatch)
    calls: list[int] = []
    monkeypatch.setattr(
        dsd, "discover_data_source",
        lambda intent, required_fields=None: (calls.append(1), _source())[1],
    )
    rec1 = ds.ensure_discovered_source(proj)
    rec2 = ds.ensure_discovered_source(proj)
    assert rec1["status"] == rec2["status"] == "verified"
    assert len(calls) == 1  # durable — a same-key verified record is not re-searched


# --- none: TTL + bounded retry -------------------------------------------------


def test_none_status_ttl_and_bounded_retry(tmp_path, monkeypatch):
    proj = _proj(tmp_path, "PROJ-6")
    _fixed_distill(monkeypatch)
    calls: list[int] = []
    monkeypatch.setattr(
        dsd, "discover_data_source",
        lambda intent, required_fields=None: (calls.append(1), None)[1],
    )

    rec1 = ds.ensure_discovered_source(proj)
    assert rec1["status"] == "none" and rec1["retry_count"] == 1
    assert len(calls) == 1

    # Fresh none → reused, NOT re-searched.
    rec2 = ds.ensure_discovered_source(proj)
    assert len(calls) == 1 and rec2["retry_count"] == 1

    # Age the record past the TTL → re-searched, retry_count increments.
    cache = ds._cache_path(proj)
    doc = yaml.safe_load(cache.read_text())
    stale = _dt.datetime.now(_dt.UTC) - _dt.timedelta(days=ds._NONE_TTL_DAYS + 5)
    doc["searched_at"] = stale.isoformat()
    cache.write_text(yaml.safe_dump(doc))
    rec3 = ds.ensure_discovered_source(proj)
    assert len(calls) == 2 and rec3["retry_count"] == 2

    # Exhaust the retry budget → durable none even when stale (no more searches).
    doc = yaml.safe_load(cache.read_text())
    doc["retry_count"] = ds._NONE_MAX_RETRIES
    doc["searched_at"] = (_dt.datetime.now(_dt.UTC) - _dt.timedelta(days=60)).isoformat()
    cache.write_text(yaml.safe_dump(doc))
    calls_before = len(calls)
    rec4 = ds.ensure_discovered_source(proj)
    assert len(calls) == calls_before  # not re-searched — budget spent
    assert rec4["status"] == "none"


# --- legacy poison invalidation ------------------------------------------------


def test_legacy_error_cache_is_treated_as_miss(tmp_path, monkeypatch):
    proj = _proj(tmp_path, "PROJ-7")
    # Seed a legacy poison record exactly as the OLD writer produced it: a
    # ``status: error`` with no cache_key, which used to be returned forever.
    cache = ds._cache_path(proj)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("status: error\nreason: 'HTTPSConnectionPool: Read timed out'\n")

    _fixed_distill(monkeypatch)
    monkeypatch.setattr(
        dsd, "discover_data_source",
        lambda intent, required_fields=None: _source(),
    )
    rec = ds.ensure_discovered_source(proj)
    # The poison error is NOT returned; discovery re-runs and finds the real source.
    assert rec["status"] == "verified"
    assert rec["ref"] == "database-knotinfo"
