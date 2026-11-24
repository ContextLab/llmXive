"""Spec 027: the ``hf_catalog``, ``leaderboard`` and ``funded`` snapshot components.

Offline and deterministic: the recorded router catalog and the (synthetic-rating)
LMArena fixtures feed the parser; live fetches go to a real local HTTP server; the
LKG store always lives under ``tmp_path``.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import llmxive.model_selection.snapshot as snap_mod
from llmxive.model_selection.leaderboard import TRACK_CATEGORY, join_scores, parse_arena_rows
from llmxive.model_selection.lkg import LKGStore
from llmxive.model_selection.select import select
from llmxive.model_selection.snapshot import _parse_hf_catalog
from llmxive.model_selection.types import (
    CallBudget,
    CreditGuardSnapshot,
    FundedGuardSnapshot,
    ModelPricing,
    ModelRequirement,
    ModelUnavailable,
    ObservedModel,
)
from tests.helpers.replay_server import ReplayServer

_FIX = Path(__file__).parents[1] / "fixtures" / "hf_funded"
_REAL_FETCH_HF = snap_mod._fetch_huggingface  # the real fetch, before any test patches it
T0 = datetime(2026, 11, 23, 12, 0, 0, tzinfo=UTC)


def _load(name):
    return json.loads((_FIX / name).read_text())


CAT = _load("router_models.json")["payload"]
ARENA = {
    t: parse_arena_rows(_load(f"lmarena_text_{c}.json")["payload"]["rows"], category=c)
    for t, c in TRACK_CATEGORY.items()
}


def test_parse_hf_catalog_one_ref_per_live_provider():
    refs, pricing, observed = _parse_hf_catalog(CAT)
    live = [(m["id"], p["provider"]) for m in CAT["data"] for p in m["providers"] if p.get("status") == "live"]
    assert sorted(r.model_id for r in refs) == sorted(f"{i}:{p}" for i, p in live)
    r = refs[0]
    repo, provider = r.model_id.rsplit(":", 1)
    assert (r.backend, r.serving_endpoint) == ("huggingface", provider) and ":" not in r.model_family
    src = next(p for m in CAT["data"] if m["id"] == repo for p in m["providers"] if p["provider"] == provider)
    assert pricing[r.model_id].input_usd_per_token == pytest.approx(src["pricing"]["input"] / 1e6)
    assert observed[r.model_id].context_length == src.get("context_length")


def test_parse_hf_catalog_synthetic_edges():
    raw = {"data": [{"id": "acme/alpha-large", "architecture": {"input_modalities": ["text", "image"]}, "providers": [
        {"provider": "prov-a", "status": "live", "pricing": {"input": 2.0, "output": 8.0}, "context_length": 200000,
         "supports_structured_output": True, "supports_tools": False},
        {"provider": "prov-b", "status": "staging", "pricing": {"input": 1.0, "output": 4.0}},
        {"provider": "prov-c", "status": "live"}]}]}
    refs, pricing, observed = _parse_hf_catalog(raw)
    assert [r.model_id for r in refs] == ["acme/alpha-large:prov-a", "acme/alpha-large:prov-c"]
    assert pricing["acme/alpha-large:prov-a"] == ModelPricing(2e-6, 8e-6)
    assert not pricing["acme/alpha-large:prov-c"].is_known
    assert observed["acme/alpha-large:prov-a"] == ObservedModel(200000, frozenset({"structured", "vision"}))


def test_vision_comes_only_from_the_model_level_input_modalities():
    """The recorded router catalog states image input once per MODEL
    (``architecture.input_modalities``); its provider rows carry no modality or
    image field. So a funded candidate is vision-eligible exactly when its model
    lists ``image`` — the same for every provider of that model — and never
    otherwise. Which providers actually accept an image is not published; a
    provider that refuses one answers 404 and the chain advances."""
    _, _, observed = _parse_hf_catalog(CAT)
    provider_keys = {k for m in CAT["data"] for p in m["providers"] for k in p}
    assert not {k for k in provider_keys if "modal" in k or "image" in k or "vision" in k}
    checked_vision = checked_text = 0
    for m in CAT["data"]:
        image = "image" in (m.get("architecture") or {}).get("input_modalities", [])
        for p in m["providers"]:
            mid = f"{m['id']}:{p['provider']}"
            if mid in observed:
                assert ("vision" in observed[mid].features) is image, mid
                checked_vision += image
                checked_text += not image
    assert checked_vision and checked_text  # the fixture exercises both sides


def test_parse_hf_catalog_family_and_vendor_come_from_the_repo_alone():
    raw = {"data": [{"id": "Acme/Alpha", "providers": [{"provider": "p1", "status": "live",
                                                        "pricing": {"input": 1, "output": 1}}]}]}
    (ref,), _, _ = _parse_hf_catalog(raw)
    assert (ref.model_family, ref.vendor) == ("alpha", "acme")


@pytest.mark.parametrize("pricing", [{"input": "1", "output": 2}, {"input": True, "output": 2},
                                     {"input": -1, "output": 2}, {"input": float("nan"), "output": 2}, None])
def test_parse_hf_catalog_bad_prices_are_unknown_never_free(pricing):
    raw = {"data": [{"id": "acme/a", "providers": [{"provider": "p", "status": "live", "pricing": pricing}]}]}
    _, prices, _ = _parse_hf_catalog(raw)
    assert not prices["acme/a:p"].is_known and not prices["acme/a:p"].is_free


def test_parse_hf_catalog_rejects_a_body_without_a_data_list():
    with pytest.raises(ValueError):
        _parse_hf_catalog({"object": "list"})


def _guard(now, available=5.0, org=None):
    return FundedGuardSnapshot(50.0, 10.0, 10.0, 0.0, org, 30.0, available, "2026-11", now, "live")


def _patch(monkeypatch, *, hf, lb, guard):  # the house seam: tests/unit/test_model_selection_lkg.py
    for name in ("_fetch_dartmouth", "_fetch_local"):
        monkeypatch.setattr(snap_mod, name, lambda: None)
    monkeypatch.setattr(snap_mod, "_fetch_credit", lambda *, now: None)
    monkeypatch.setattr(snap_mod, "_fetch_huggingface", hf)
    monkeypatch.setattr(snap_mod, "_fetch_leaderboard", lb)
    monkeypatch.setattr(snap_mod, "_fetch_funded_guard", guard)


def test_snapshot_joins_scores_per_provider_and_falls_back_to_lkg(monkeypatch, tmp_path):
    store = LKGStore(tmp_path / "lkg.json")
    hf = _parse_hf_catalog(CAT)
    _patch(monkeypatch, hf=lambda: hf, lb=lambda: ARENA, guard=lambda *, now: _guard(now))
    s1 = snap_mod.runtime_snapshot(now=T0, lkg_store=store)
    assert set(s1.sources) == {"catalog", "local", "credit", "hf_catalog", "leaderboard", "funded"}
    assert s1.sources["hf_catalog"].source == s1.sources["leaderboard"].source == s1.sources["funded"].source == "live"
    joined, _ = join_scores({r.model_id.rsplit(":", 1)[0] for r in hf[0]}, ARENA)
    for m in s1.models:
        if m.backend == "huggingface":
            assert s1.scores.get(m.model_id) == joined.get(m.model_id.rsplit(":", 1)[0])
    assert s1.scores and s1.funded == _guard(T0)
    assert dict(s1.observed) == hf[2]
    _patch(monkeypatch, hf=lambda: None, lb=lambda: None, guard=lambda *, now: None)
    s2 = snap_mod.runtime_snapshot(now=T0 + timedelta(seconds=3601), lkg_store=store)
    assert (s2.sources["leaderboard"].source, s2.sources["leaderboard"].age_s) == ("last_known_good", 3601.0)
    assert s2.sources["hf_catalog"].source == "last_known_good"
    assert s2.sources["funded"].source == "unavailable" and s2.funded is None
    assert dict(s2.scores) == dict(s1.scores) and len(s2.models) == len(s1.models) and s1.digest != s2.digest
    assert dict(s2.observed) == dict(s1.observed) and dict(s2.pricing) == dict(s1.pricing)


def test_cold_start_new_components_are_unavailable(monkeypatch, tmp_path):
    _patch(monkeypatch, hf=lambda: None, lb=lambda: None, guard=lambda *, now: None)
    s = snap_mod.runtime_snapshot(now=T0, lkg_store=LKGStore(tmp_path / "lkg.json"))
    assert {s.sources[c].source for c in ("hf_catalog", "leaderboard", "funded")} == {"unavailable"}
    assert s.models == () and not s.scores and not s.observed and s.funded is None


def test_lkg_leaderboard_joins_against_the_live_catalog(monkeypatch, tmp_path):
    store = LKGStore(tmp_path / "lkg.json")
    refs, pricing, observed = _parse_hf_catalog(CAT)
    _patch(monkeypatch, hf=lambda: (refs, pricing, observed), lb=lambda: ARENA, guard=lambda *, now: None)
    gone = next(iter(snap_mod.runtime_snapshot(now=T0, lkg_store=store).scores)).rsplit(":", 1)[0]
    kept = [r for r in refs if not r.model_id.startswith(gone + ":")]
    _patch(monkeypatch, hf=lambda: (kept, pricing, observed), lb=lambda: None, guard=lambda *, now: None)
    s = snap_mod.runtime_snapshot(now=T0 + timedelta(seconds=60), lkg_store=store, refresh=True)
    assert s.sources["hf_catalog"].source == "live"
    assert s.sources["leaderboard"].source == "last_known_good" and s.scores
    assert not any(k.startswith(gone + ":") for k in s.scores)


def test_ambiguous_names_are_logged_without_ratings(monkeypatch, tmp_path, caplog):
    name = next(iter(ARENA["reasoning"]))  # normalised arena name, e.g. "alpaca13b"
    raw = {"data": [{"id": f"{org}/{name}", "providers": [{"provider": "p", "status": "live",
                                                           "pricing": {"input": 1, "output": 1}}]}
                    for org in ("org-a", "org-b")]}
    hf = _parse_hf_catalog(raw)
    _patch(monkeypatch, hf=lambda: hf, lb=lambda: ARENA, guard=lambda *, now: None)
    with caplog.at_level(logging.WARNING, logger=snap_mod.__name__):
        s = snap_mod.runtime_snapshot(now=T0, lkg_store=LKGStore(tmp_path / "lkg.json"))
    assert not s.scores
    msgs = [r.getMessage() for r in caplog.records if r.name == snap_mod.__name__]
    assert any(name in m for m in msgs)
    score = ARENA["reasoning"][name]
    assert not any(str(v) in m for m in msgs for v in (score.rating, score.rating_lower, score.rating_upper))


def test_scores_live_only_in_the_gitignored_lkg_store():
    root = Path(__file__).resolve().parents[2]
    assert subprocess.run(["git", "check-ignore", "-q", "state/model_selection/lkg_snapshot.json"], cwd=root).returncode == 0


def test_digest_changes_when_a_score_or_its_publish_date_changes(monkeypatch, tmp_path):
    hf = _parse_hf_catalog(CAT)
    joined, _ = join_scores({r.model_id.rsplit(":", 1)[0] for r in hf[0]}, ARENA)
    # pick an arena name that actually joins, so the change reaches snapshot.scores
    name = next(n for n in ARENA["reasoning"]
                if any(ms.reasoning is ARENA["reasoning"][n] for ms in joined.values()))
    s = ARENA["reasoning"][name]
    digests = []
    for score in (s, replace(s, rating_upper=s.rating_upper + 1),
                  replace(s, publish_date=s.publish_date - timedelta(days=1)),
                  replace(s, rating_lower=s.rating_lower - 1), replace(s, rating=s.rating + 0.5,
                                                                       rating_upper=s.rating_upper + 1)):
        arena = {**ARENA, "reasoning": {**ARENA["reasoning"], name: score}}
        _patch(monkeypatch, hf=lambda: hf, lb=lambda a=arena: a, guard=lambda *, now: None)
        digests.append(snap_mod.runtime_snapshot(now=T0, lkg_store=LKGStore(tmp_path / f"{len(digests)}.json")).digest)
    assert len(set(digests)) == 5


def test_digest_covers_observed_and_funded(monkeypatch, tmp_path):
    refs, pricing, observed = _parse_hf_catalog(CAT)
    mid = refs[0].model_id
    other = dict(observed)
    other[mid] = ObservedModel(observed[mid].context_length, observed[mid].features ^ {"tools"})
    variants = [
        ((refs, pricing, observed), _guard(T0)),
        ((refs, pricing, other), _guard(T0)),                    # observed flags only
        ((refs, pricing, observed), _guard(T0, available=4.0)),  # funded guard only
        ((refs, pricing, observed), _guard(T0, org=7.0)),        # org cross-check only
    ]
    digests = []
    for i, (hf, g) in enumerate(variants):
        _patch(monkeypatch, hf=lambda h=hf: h, lb=lambda: ARENA, guard=lambda *, now, g=g: g)
        digests.append(snap_mod.runtime_snapshot(now=T0, lkg_store=LKGStore(tmp_path / f"{i}.json")).digest)
    assert len(set(digests)) == len(variants)


def test_fetch_huggingface_reads_the_router_catalog_over_http():
    with ReplayServer({("GET", "/models"): [(200, CAT)]}) as srv:
        refs, pricing, observed = snap_mod._fetch_huggingface(base_url=srv.base_url)
    assert (refs, pricing, observed) == _parse_hf_catalog(CAT)
    with ReplayServer({("GET", "/models"): [(503, {"error": "down"})]}) as srv:
        assert snap_mod._fetch_huggingface(base_url=srv.base_url) is None
    with ReplayServer({("GET", "/models"): [(200, {"object": "list"})]}) as srv:
        assert snap_mod._fetch_huggingface(base_url=srv.base_url) is None  # malformed = live failure


def test_fetch_funded_guard_is_none_when_funded_is_unavailable(monkeypatch):
    monkeypatch.delenv("LLMXIVE_HF_BILL_TO", raising=False)  # FundedUnavailable inside funded_guard
    assert snap_mod._fetch_funded_guard(now=T0) is None


def test_fetch_funded_guard_is_none_when_the_ledger_cannot_sync(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(repo))
    monkeypatch.setenv("LLMXIVE_HF_BILL_TO", "grp-test")
    monkeypatch.setenv("HF_TOKEN", "hf_test")
    monkeypatch.setenv("LLMXIVE_FUNDED_LEDGER_ANCHOR", "0" * 40)  # pinned anchor the repo lacks
    monkeypatch.setenv("LLMXIVE_FUNDED_LEDGER_REMOTE", str(tmp_path / "no-such-remote.git"))
    assert snap_mod._fetch_funded_guard(now=T0) is None


def test_family_table_select_never_admits_a_funded_model(monkeypatch, tmp_path):
    # The router catalog carries repos whose family is in the reviewed family table
    # (e.g. Qwen3.5 → "qwen3.5"); until the funded group exists they must not be
    # admitted as free/paid candidates priced against the Dartmouth credit guard.
    hf = _parse_hf_catalog(CAT)
    assert any(r.model_family == "qwen3.5" for r in hf[0])
    _patch(monkeypatch, hf=lambda: hf, lb=lambda: ARENA, guard=lambda *, now: _guard(now))
    monkeypatch.setattr(snap_mod, "_fetch_credit", lambda *, now: CreditGuardSnapshot(
        1e6, 0.0, 1e6, True, 0.75, 7.5e5, 7.5e5, "r", now, "live"))
    monkeypatch.setattr(snap_mod, "_fetch_dartmouth", lambda: ([], {}))  # every component live
    snap = snap_mod.runtime_snapshot(now=T0, lkg_store=LKGStore(tmp_path / "lkg.json"))
    with pytest.raises(ModelUnavailable):
        select(ModelRequirement(capability="standard", call_budget=CallBudget(1000, 500), allow_paid=True), snap)



def _good_lkg(monkeypatch, store):
    hf = _parse_hf_catalog(CAT)
    _patch(monkeypatch, hf=lambda: hf, lb=lambda: None, guard=lambda *, now: None)
    first = snap_mod.runtime_snapshot(now=T0, lkg_store=store)
    assert first.sources["hf_catalog"].source == "live"
    return first


@pytest.mark.parametrize("body", [
    {"data": []},
    {"data": [{"id": "acme/a", "providers": [{"provider": "p", "status": "staging",
                                               "pricing": {"input": 1, "output": 1}}]}]},
])
def test_an_empty_catalog_is_a_failed_fetch_and_keeps_the_lkg(monkeypatch, tmp_path, body):
    with pytest.raises(ValueError):
        _parse_hf_catalog(body)
    store = LKGStore(tmp_path / "lkg.json")
    first = _good_lkg(monkeypatch, store)
    with ReplayServer({("GET", "/models"): [(200, body)]}) as srv:
        monkeypatch.setattr(snap_mod, "_fetch_huggingface", lambda: _REAL_FETCH_HF(base_url=srv.base_url))
        later = T0 + timedelta(seconds=snap_mod.HF_CATALOG_REFRESH_S + 5)
        s = snap_mod.runtime_snapshot(now=later, lkg_store=store)
        assert len(srv.requests) == 1  # it did fetch (outside the refresh interval)
    prov = s.sources["hf_catalog"]
    assert (prov.source, prov.observed_at, prov.age_s) == ("last_known_good", T0, snap_mod.HF_CATALOG_REFRESH_S + 5)
    assert len(s.models) == len(first.models)
    assert store.load()["hf_catalog"].observed_at == T0  # the good copy was not overwritten


def _serve_both(srv_cat, srv_lb):
    """Real fetch functions pointed at local servers."""
    from llmxive.model_selection.leaderboard import fetch_arena_scores

    return (lambda: _REAL_FETCH_HF(base_url=srv_cat.base_url),
            lambda: fetch_arena_scores(base_url=srv_lb.base_url + "/filter"))


def _lb_route(record):
    cat = record["query"]["where"].split("'")[1]
    rows = _load(f"lmarena_text_{cat}.json")["payload"]["rows"]
    off, n = int(record["query"]["offset"]), int(record["query"]["length"])
    page = rows[off:off + n]
    return 200, {"num_rows_total": len(rows), "partial": False,
                 "rows": [{"row_idx": off + i, "row": r} for i, r in enumerate(page)]}


def test_stored_components_are_reused_within_their_refresh_interval(monkeypatch, tmp_path):
    store = LKGStore(tmp_path / "lkg.json")
    with ReplayServer({("GET", "/models"): [(200, CAT)]}) as cat, \
            ReplayServer({("GET", "/filter"): _lb_route}) as lb:
        hf, board = _serve_both(cat, lb)
        _patch(monkeypatch, hf=hf, lb=board, guard=lambda *, now: None)
        s1 = snap_mod.runtime_snapshot(now=T0, lkg_store=store)
        n_cat, n_lb = len(cat.requests), len(lb.requests)
        assert s1.sources["hf_catalog"].source == s1.sources["leaderboard"].source == "live"
        assert n_cat == 1 and n_lb >= 2

        # inside both intervals: zero requests, original observed time, true age
        t = T0 + timedelta(seconds=snap_mod.HF_CATALOG_REFRESH_S - 1)
        s2 = snap_mod.runtime_snapshot(now=t, lkg_store=store)
        assert (len(cat.requests), len(lb.requests)) == (n_cat, n_lb)
        for c in ("hf_catalog", "leaderboard"):
            assert (s2.sources[c].source, s2.sources[c].observed_at, s2.sources[c].age_s) == \
                ("last_known_good", T0, snap_mod.HF_CATALOG_REFRESH_S - 1)
        assert dict(s2.scores) == dict(s1.scores) and len(s2.models) == len(s1.models)

        # past the catalog interval only: the catalog is refetched, the leaderboard is not
        t = T0 + timedelta(seconds=snap_mod.HF_CATALOG_REFRESH_S + 1)
        s3 = snap_mod.runtime_snapshot(now=t, lkg_store=store)
        assert (len(cat.requests), len(lb.requests)) == (n_cat + 1, n_lb)
        assert s3.sources["hf_catalog"].source == "live"
        assert s3.sources["leaderboard"].source == "last_known_good"

        # refresh=True fetches both even inside the intervals
        s4 = snap_mod.runtime_snapshot(now=t, lkg_store=store, refresh=True)
        assert len(cat.requests) == n_cat + 2 and len(lb.requests) == 2 * n_lb
        assert s4.sources["leaderboard"].source == "live"

        # past the leaderboard interval: refetched
        t2 = t + timedelta(seconds=snap_mod.LEADERBOARD_REFRESH_S + 1)
        s5 = snap_mod.runtime_snapshot(now=t2, lkg_store=store)
        assert len(lb.requests) == 3 * n_lb and s5.sources["leaderboard"].source == "live"
    # servers gone: a failed refetch past the interval still falls back to the LKG
    t3 = t2 + timedelta(seconds=snap_mod.LEADERBOARD_REFRESH_S + 1)
    s6 = snap_mod.runtime_snapshot(now=t3, lkg_store=store)
    for c in ("hf_catalog", "leaderboard"):
        assert (s6.sources[c].source, s6.sources[c].observed_at) == ("last_known_good", t2)
        assert s6.sources[c].age_s == (t3 - t2).total_seconds()
    assert dict(s6.scores) == dict(s5.scores)


def test_fetch_funded_guard_is_total(monkeypatch, caplog):
    import llmxive.backends.hf_budget as hf_budget

    def boom(*_a, **_k):
        raise RuntimeError("hf_SECRET_TOKEN_VALUE")

    monkeypatch.setattr(hf_budget, "funded_guard", boom)
    with caplog.at_level(logging.WARNING, logger=snap_mod.__name__):
        assert snap_mod._fetch_funded_guard(now=T0) is None
    assert "RuntimeError" in caplog.text and "hf_SECRET_TOKEN_VALUE" not in caplog.text
