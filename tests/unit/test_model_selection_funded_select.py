"""Spec 027 Task 13: funded (Hugging Face) eligibility in the pure selector.

Every snapshot is a real immutable ``RuntimeSnapshot`` built by
``tests/helpers/funded.py``; ``select`` is pure, so calling it IS the real use.
The snapshot-layer fixes carried from the Task 10 review drive the real
``runtime_snapshot`` with a real ``LKGStore`` under ``tmp_path``.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import replace
from datetime import date, timedelta

import pytest

import llmxive.model_selection.snapshot as snap_mod
from llmxive.model_selection.lkg import LKGEntry, LKGStore
from llmxive.model_selection.policy import LEADERBOARD_MAX_FETCH_AGE_S
from llmxive.model_selection.profiles import build_requirement
from llmxive.model_selection.select import select
from llmxive.model_selection.types import (
    ModelRequirement,
    ModelUnavailable,
    ObservedModel,
    RuntimeSnapshot,
)
from tests.helpers.funded import (
    A2,
    BUDGET,
    CLAUDE,
    FX,
    GEMMA4,
    GLM,
    GPT_OSS,
    NOW,
    QWEN,
    REASONING,
    REPO_B,
    A,
    B,
    C,
    D,
    E,
    ids,
    order,
    sel,
    snapshot,
)

WIDE = {"max_candidates": 99}
SCORED_HF = {A, A2, B, C, E, *FX}


def test_score_track_and_flags_decide_eligibility():
    assert ids(sel("cheap_structured", snapshot(local=False), **WIDE)) == SCORED_HF  # D has no score
    assert ids(sel("deep_code", snapshot(local=False), **WIDE)) == SCORED_HF
    assert ids(sel("vision", snapshot(), **WIDE)) == {C}  # the only image-input model


# Leaderboard freshness follows the 2026-11-23 ruling: fetched within
# LEADERBOARD_MAX_FETCH_AGE_S (24 h), not the catalog's max_catalog_age_s.
@pytest.mark.parametrize("snap_kw", [
    {"sources": {"leaderboard": ("unavailable", 0.0)}},
    {"sources": {"leaderboard": ("last_known_good", LEADERBOARD_MAX_FETCH_AGE_S + 1.0)}},
    {"sources": {"hf_catalog": ("last_known_good", 3601.0)}},
    {"sources": {"hf_catalog": ("unavailable", 0.0)}},
    {"available_usd": None},
])
def test_fail_closed_table(snap_kw):
    with pytest.raises(ModelUnavailable):
        sel("deep_review", snapshot(local=False, **snap_kw))


@pytest.mark.parametrize("snap_kw, needle", [
    ({"sources": {"leaderboard": ("unavailable", 0.0)}}, "leaderboard"),
    ({"sources": {"leaderboard": ("last_known_good", LEADERBOARD_MAX_FETCH_AGE_S + 1.0)}}, "leaderboard"),
    ({"sources": {"hf_catalog": ("last_known_good", 3601.0)}}, "hf_catalog"),
    ({"sources": {"hf_catalog": ("unavailable", 0.0)}}, "hf_catalog"),
    ({"available_usd": None}, "funded"),
    ({"publish_dates": {r: date(2026, 11, 1) for r in (*REASONING, "acme/delta-unscored")}}, "publish date"),
])
def test_the_decision_record_names_the_component_that_blocked_funded(snap_kw, needle):
    snap = snapshot(dartmouth=(GLM,), local=False, **snap_kw)
    chain = sel("deep_review", snap)  # a free candidate keeps the decision alive
    assert [m for m in order(chain)] == [GLM]
    blocked = [e for e in chain.explanation if e.startswith("funded candidates not eligible")]
    assert len(blocked) == 1 and needle in blocked[0]
    with pytest.raises(ModelUnavailable, match=needle):
        sel("deep_review", snapshot(local=False, **snap_kw))


def test_a_missing_funded_component_fails_closed():
    snap = snapshot(local=False)
    for name in ("hf_catalog", "leaderboard"):
        sources = {k: v for k, v in snap.sources.items() if k != name}
        with pytest.raises(ModelUnavailable, match=name):
            select(build_requirement("deep_review", BUDGET), replace(snap, sources=sources))


def test_a_guard_that_is_not_live_fails_closed():
    snap = snapshot(local=False)
    with pytest.raises(ModelUnavailable, match="funded"):
        select(build_requirement("deep_review", BUDGET),
               replace(snap, funded=replace(snap.funded, source="last_known_good")))


def test_a_requirement_without_track_and_level_gets_no_funded_candidate():
    with pytest.raises(ModelUnavailable):
        select(ModelRequirement(capability="deep", call_budget=BUDGET), snapshot(local=False))
    with pytest.raises(ModelUnavailable, match="track"):
        sel("deep_review", snapshot(local=False), strength=None)


def test_stale_publish_date_is_ineligible_and_leaves_the_population():
    got = ids(sel("cheap_structured", snapshot(local=False, publish_dates={REPO_B: date(2026, 11, 15)}), **WIDE))
    assert B not in got and E in got
    with pytest.raises(ModelUnavailable):
        sel("deep_review", snapshot(local=False, publish_dates={r: date(2026, 11, 1) for r in REASONING}))


def test_publish_date_at_exactly_the_limit_is_still_fresh():
    got = ids(sel("cheap_structured", snapshot(local=False, publish_dates={REPO_B: date(2026, 11, 16)}), **WIDE))
    assert B in got


def test_a_publish_date_one_day_ahead_passes_and_two_days_ahead_makes_the_leaderboard_unavailable():
    got = ids(sel("cheap_structured", snapshot(local=False, publish_dates={REPO_B: date(2026, 11, 24)}), **WIDE))
    assert B in got
    snap = snapshot(dartmouth=(GLM,), local=False, publish_dates={REPO_B: date(2026, 11, 25)})
    chain = sel("cheap_structured", snap, **WIDE)
    assert order(chain) == [GLM]                       # no funded candidate at all, not just B dropped
    assert any(e.startswith("funded candidates not eligible") and "more than 1 day(s) after" in e
               for e in chain.explanation)
    with pytest.raises(ModelUnavailable, match="publish date"):
        sel("cheap_structured", snapshot(local=False, publish_dates={REPO_B: date(2026, 11, 25)}))


def test_leaderboard_lkg_at_exactly_the_limit_is_still_fresh():
    at_limit = {"leaderboard": ("last_known_good", float(LEADERBOARD_MAX_FETCH_AGE_S))}
    assert A in ids(sel("deep_review", snapshot(sources=at_limit), **WIDE))
    # the catalog's max_catalog_age_s (3600) does not judge the leaderboard
    past_catalog_limit = {"leaderboard": ("last_known_good", 3601.0)}
    assert A in ids(sel("deep_review", snapshot(sources=past_catalog_limit), **WIDE))


def test_hf_catalog_lkg_at_exactly_the_limit_is_still_fresh():
    assert A in ids(sel("deep_review", snapshot(sources={"hf_catalog": ("last_known_good", 3600.0)}), **WIDE))


def test_unobservable_features_and_context():
    assert ids(sel("deep_review", snapshot(), required_features=frozenset({"reasoning"}), **WIDE)) == {E}
    assert ids(sel("deep_review", snapshot(), required_features=frozenset({"tools"}), **WIDE)) == {A}
    got = ids(sel("deep_review", snapshot(), min_context_tokens=100_000, **WIDE))
    assert A in got and A2 not in got  # same repo, provider B has 32000


def test_an_unknown_context_length_fails_a_stated_minimum():
    snap = snapshot(local=False)
    observed = dict(snap.observed)
    observed[A] = ObservedModel(context_length=None, features=observed[A].features)
    snap = replace(snap, observed=observed)
    assert A in ids(sel("deep_review", snap, **WIDE))  # no minimum stated
    assert A not in ids(sel("deep_review", snap, min_context_tokens=1, **WIDE))


def test_a_model_without_observed_flags_is_ineligible():
    snap = snapshot(local=False)
    snap = replace(snap, observed={k: v for k, v in snap.observed.items() if k != B})
    assert B not in ids(sel("cheap_structured", snap, **WIDE))


def test_an_unknown_price_is_ineligible():
    snap = snapshot(local=False)
    pricing = dict(snap.pricing)
    pricing[B] = replace(pricing[B], output_usd_per_token=None)
    got = ids(sel("cheap_structured", replace(snap, pricing=pricing), **WIDE))
    assert B not in got and E in got


def test_require_paid_excludes_funded_candidates():
    with pytest.raises(ModelUnavailable):
        sel("deep_review", snapshot(local=False), allow_paid=True, require_paid=True)


def test_exclusions_and_required_independence_still_apply_to_funded():
    got = ids(sel("cheap_structured", snapshot(local=False), exclude_models=frozenset({B}), **WIDE))
    assert B not in got and E in got
    got = ids(sel("cheap_structured", snapshot(local=False), exclude_endpoints=frozenset({"prov-z"}), **WIDE))
    assert not set(FX) & got
    from llmxive.model_selection.types import IndependenceBaseline

    req = build_requirement(
        "cheap_structured", BUDGET, independence_against=IndependenceBaseline(families=frozenset({"gpt-oss"})),
        required_independence=frozenset({"family"}), max_candidates=99,
    )
    assert E not in ids(select(req, snapshot(local=False)))


def test_funded_needs_no_opt_in_and_is_funded_class():
    chain = sel("cheap_structured", snapshot(local=False), **WIDE)
    assert all(c.cost_class == "funded" for c in chain.candidates)
    assert all(c.approved_ceiling_credits == pytest.approx(5000.0) for c in chain.candidates)


def test_funded_ignores_allow_paid_and_the_paid_opt_in():
    with_paid = ids(sel("cheap_structured", snapshot(local=False, claude=True, paid_opt_in=True),
                        allow_paid=True, **WIDE))
    assert SCORED_HF <= with_paid and CLAUDE in with_paid
    assert SCORED_HF == ids(sel("cheap_structured", snapshot(local=False, claude=True), **WIDE))


def test_no_hugging_face_models_leaves_existing_behaviour_untouched():
    snap = snapshot(dartmouth=(GLM, QWEN, GEMMA4, GPT_OSS), hf=(), available_usd=None)
    assert order(sel("deep_review", snap)) == [GLM, QWEN, GEMMA4, GPT_OSS]


def test_d_without_a_score_is_never_eligible():
    assert D not in ids(sel("cheap_structured", snapshot(local=False), **WIDE))


# --------------------------------------------------------------------------- #
# Snapshot-layer fixes carried from the Task 10 review.
# --------------------------------------------------------------------------- #


def test_fetch_funded_guard_survives_an_import_failure(monkeypatch, caplog):
    monkeypatch.setitem(sys.modules, "llmxive.backends.hf_budget", None)  # import raises ImportError
    with caplog.at_level(logging.WARNING, logger=snap_mod.__name__):
        assert snap_mod._fetch_funded_guard(now=NOW) is None
    assert "cannot import" in caplog.text and "ModuleNotFoundError" in caplog.text


@pytest.mark.parametrize("exc_name", ["FundedUnavailable", "LedgerError"])
def test_fetch_funded_guard_never_logs_the_exception_message(monkeypatch, caplog, exc_name):
    import llmxive.backends.hf_budget as hf_budget
    from llmxive.model_selection import ledger_transport

    exc_type = getattr(hf_budget, exc_name, None) or getattr(ledger_transport, exc_name)

    def boom(*_a, **_k):
        raise exc_type("https://user:hf_SECRET_TOKEN_VALUE@example.invalid grp-SECRET-BILL-TO")

    monkeypatch.setattr(hf_budget, "funded_guard", boom)
    with caplog.at_level(logging.WARNING, logger=snap_mod.__name__):
        assert snap_mod._fetch_funded_guard(now=NOW) is None
    assert exc_name in caplog.text
    assert "SECRET" not in caplog.text


def test_a_future_stamped_lkg_copy_is_unavailable_not_fresh(monkeypatch, tmp_path):
    store = LKGStore(tmp_path / "lkg.json")
    good = snapshot(hf=(A,))
    hf_data = ([m for m in good.models if m.backend == "huggingface"], dict(good.pricing), dict(good.observed))
    future = NOW + timedelta(hours=2)
    store.record({"hf_catalog": LKGEntry(observed_at=future, payload=snap_mod._hf_catalog_to_payload(hf_data))})
    for name in ("_fetch_dartmouth", "_fetch_local", "_fetch_huggingface", "_fetch_leaderboard"):
        monkeypatch.setattr(snap_mod, name, lambda: None)
    monkeypatch.setattr(snap_mod, "_fetch_credit", lambda *, now: None)
    monkeypatch.setattr(snap_mod, "_fetch_funded_guard", lambda *, now: None)
    s: RuntimeSnapshot = snap_mod.runtime_snapshot(now=NOW, lkg_store=store)
    assert s.sources["hf_catalog"].source == "unavailable"
    assert not [m for m in s.models if m.backend == "huggingface"]
