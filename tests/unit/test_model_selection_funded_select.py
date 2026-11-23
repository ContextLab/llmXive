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
from llmxive.model_selection.policy import FUNDED_POLICY, LEADERBOARD_MAX_FETCH_AGE_S
from llmxive.model_selection.profiles import build_requirement
from llmxive.model_selection.select import select
from llmxive.model_selection.strength import level_qualifiers, repo_of, track_population
from llmxive.model_selection.types import (
    STRENGTH_LEVELS,
    USD_TO_CREDITS,
    IndependenceBaseline,
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
    LOCAL,
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
    policy_with,
    sel,
    snapshot,
)

WIDE = {"max_candidates": 99}
SCORED_HF = {A, A2, B, C, E, *FX}

#: Task 14 puts every funded candidate through the level filter, the allowance,
#: one-per-family and ``max_chain_slots``. The eligibility tests below are about
#: the per-candidate rules UNDER those filters, so they select with a policy in
#: which every scored repo qualifies at every level and the slots are unbounded,
#: and take the union with A2 excluded: A and A2 share a family, so one chain can
#: show only one of them.
OPEN = policy_with(level_top_percent={lvl: 100 for lvl in STRENGTH_LEVELS}, max_chain_slots=99)


def eligible_ids(profile: str, snap: RuntimeSnapshot, **kw) -> set[str]:
    """Every funded/other candidate that passes per-candidate eligibility."""
    return ids(sel(profile, snap, OPEN, **WIDE, **kw)) | ids(
        sel(profile, snap, OPEN, **WIDE, exclude_models=frozenset({A2}), **kw))


def test_score_track_and_flags_decide_eligibility():
    assert eligible_ids("cheap_structured", snapshot(local=False)) == SCORED_HF  # D has no score
    assert eligible_ids("deep_code", snapshot(local=False)) == SCORED_HF
    assert eligible_ids("vision", snapshot()) == {C}  # the only image-input model


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
    assert A in eligible_ids("deep_review", snapshot(sources=at_limit))
    # the catalog's max_catalog_age_s (3600) does not judge the leaderboard
    past_catalog_limit = {"leaderboard": ("last_known_good", 3601.0)}
    assert A in eligible_ids("deep_review", snapshot(sources=past_catalog_limit))


def test_hf_catalog_lkg_at_exactly_the_limit_is_still_fresh():
    assert A in eligible_ids("deep_review", snapshot(sources={"hf_catalog": ("last_known_good", 3600.0)}))


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
    assert A in eligible_ids("deep_review", snap)  # no minimum stated
    assert A not in eligible_ids("deep_review", snap, min_context_tokens=1)


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
    with_paid = eligible_ids("cheap_structured", snapshot(local=False, claude=True, paid_opt_in=True),
                             allow_paid=True)
    assert SCORED_HF <= with_paid and CLAUDE in with_paid
    assert SCORED_HF == eligible_ids("cheap_structured", snapshot(local=False, claude=True))


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


# --------------------------------------------------------------------------- #
# Spec 027 Task 14: level qualification, cheapest-within-level, budget step-down,
# class order free-remote > funded > local > paid, class-aware review freshness.
# --------------------------------------------------------------------------- #

FULL = dict(dartmouth=(GLM, QWEN, GEMMA4, GPT_OSS), claude=True, paid_opt_in=True)


def test_order_is_free_remote_then_funded_then_local_then_paid():
    assert order(sel("cheap_structured", snapshot(**FULL), allow_paid=True)) == [
        GLM, QWEN, GEMMA4, GPT_OSS, B, E, LOCAL, CLAUDE]


def test_funded_slots_never_truncate_local_or_paid():
    chain = sel("standard_generation", snapshot(**FULL), allow_paid=True)
    assert sum(c.cost_class == "funded" for c in chain.candidates) == 2 and order(chain)[-2:] == [LOCAL, CLAUDE]


@pytest.mark.parametrize("profile,want", [
    ("cheap_structured", [B, E, LOCAL]), ("standard_generation", [E, C, LOCAL]),
    ("deep_review", [E, A2]), ("deep_code", [B, A2]), ("vision", [C])])
def test_cheapest_qualifier_leads_then_other_families(profile, want):
    assert order(sel(profile, snapshot())) == want


def test_a_statistically_tied_cheaper_model_wins_its_level():  # F04 is "balanced" only by interval overlap
    assert order(sel("standard_generation", snapshot(prices={FX[3]: (1e-8, 1e-8)}))) == [FX[3], E, LOCAL]


def test_population_ignores_call_filters():  # C is "balanced" among all 20, not "strongest" among vision models
    assert order(sel("vision", snapshot())) == [C]
    with pytest.raises(ModelUnavailable):
        sel("vision", snapshot(), strength="strongest")


def test_tracks_are_ranked_separately():
    assert order(sel("deep_code", snapshot()))[0] == B and order(sel("deep_review", snapshot()))[0] == E


def test_level_raise_and_lower_for_one_call():
    assert order(sel("deep_code", snapshot(), strength="strongest")) == [B]
    assert order(sel("cheap_structured", snapshot(), strength="balanced")) == [E, C, LOCAL]


def test_generation_steps_down_one_level_under_budget_pressure():
    chain = sel("standard_generation", snapshot(available_usd=0.003))
    assert order(chain) == [B, LOCAL]
    assert any("stepped down to economy (budget pressure)" in e for e in chain.explanation)


def test_step_down_is_one_level_only():
    with pytest.raises(ModelUnavailable, match="funded allowance exhausted"):
        sel("deep_code", snapshot(available_usd=0.001))  # strong → balanced still does not fit


def test_review_never_steps_down():
    with pytest.raises(ModelUnavailable, match="funded allowance exhausted"):
        sel("deep_review", snapshot(available_usd=0.003))
    assert order(sel("deep_review", snapshot(available_usd=0.004))) == [E]  # A2 (0.018) no longer fits


def test_vision_never_steps_down():
    with pytest.raises(ModelUnavailable, match="funded allowance exhausted"):
        sel("vision", snapshot(available_usd=0.001))  # C costs 0.009


def test_exhausted_allowance_is_outage_not_paid():
    snap = snapshot(claude=True, paid_opt_in=True, available_usd=0.001)
    chain = sel("cheap_structured", snap, allow_paid=True)  # economy cannot step down
    assert order(chain) == [LOCAL] and any("funded allowance exhausted" in e for e in chain.explanation)
    with pytest.raises(ModelUnavailable):
        sel("deep_review", snap, allow_paid=True)
    assert order(sel("deep_review", snap, allow_paid=True, require_paid=True)) == [CLAUDE]


def test_a_stale_funded_class_still_falls_through_to_paid():
    # Only the allowance suppresses paid; staleness is an ordinary fall-through.
    snap = snapshot(claude=True, paid_opt_in=True, sources={"leaderboard": ("unavailable", 0.0)})
    assert order(sel("deep_review", snap, allow_paid=True)) == [CLAUDE]


def test_a_guard_with_zero_headroom_admits_nothing():
    snap = snapshot(available_usd=0.0)
    assert order(sel("cheap_structured", snap)) == [LOCAL]
    free = snapshot(available_usd=0.0, prices={B: (0.0, 0.0)})  # even a zero-priced call
    assert order(sel("cheap_structured", free)) == [LOCAL]


def test_max_credits_bounds_funded_like_the_allowance():
    chain = sel("deep_review", snapshot(), max_credits=10)
    assert order(chain) == [E]  # 0.0036 USD = 3.6 credits; A2 = 18
    assert chain.candidates[0].approved_ceiling_credits == pytest.approx(10.0)


def test_require_paid_excludes_funded():
    assert order(sel("deep_review", snapshot(claude=True, paid_opt_in=True), allow_paid=True,
                     require_paid=True)) == [CLAUDE]


def test_independence_dimensions_work_unchanged():
    base = IndependenceBaseline(families=frozenset({"gpt-oss"}))
    assert order(sel("independent_review", snapshot(), independence_against=base)) == [A2, FX[0]]


def test_chain_explanation_names_track_level_and_population():
    assert any(e.startswith("funded: reasoning/strong — 3 of 20 models qualify")
               for e in sel("deep_review", snapshot()).explanation)


def test_dartmouth_only_explanations_are_unchanged():
    # No Hugging Face model in the snapshot → no funded line in the decision record.
    snap = snapshot(dartmouth=(GLM,), hf=(), available_usd=None)
    assert not any(e.startswith("funded") for e in sel("deep_review", snap).explanation)
    assert any(e.startswith("funded candidates not eligible")
               for e in sel("deep_review", snapshot(dartmouth=(GLM,), available_usd=None)).explanation)


STALE = ("last_known_good", 901.0)
GONE = ("unavailable", 0.0)


def test_review_is_served_by_funded_when_dartmouth_is_not_fresh():
    assert order(sel("independent_review", snapshot(dartmouth=(QWEN,), sources={"catalog": STALE, "credit": GONE}))) == [E, A2]


def test_review_is_served_by_dartmouth_when_funded_is_not_fresh():
    for bad in ({"leaderboard": STALE}, {"hf_catalog": GONE}):
        assert order(sel("independent_review", snapshot(dartmouth=(QWEN, GEMMA4), sources=bad))) == [QWEN, GEMMA4]
    assert order(sel("independent_review", snapshot(dartmouth=(QWEN, GEMMA4), available_usd=None))) == [QWEN, GEMMA4]


def test_review_is_an_outage_only_when_no_class_is_fresh():
    with pytest.raises(ModelUnavailable, match="fresh"):
        sel("independent_review", snapshot(dartmouth=(QWEN,), sources={"credit": GONE, "leaderboard": STALE}))


def test_select_stays_byte_identical_and_versioned():
    s = snapshot(dartmouth=(QWEN,))
    assert sel("deep_review", s) == sel("deep_review", s)
    assert sel("deep_review", s).selection_policy_version == 4


# Security property (automated review of 2a0d08f): no funded candidate leaves
# ``select`` without passing the level filter AND the allowance/budget fit.
_PROFILES = ("cheap_structured", "standard_generation", "deep_review", "independent_review", "deep_code", "vision")


@pytest.mark.parametrize("profile", _PROFILES)
@pytest.mark.parametrize("strength", [None, *STRENGTH_LEVELS])
@pytest.mark.parametrize("available_usd", [0.0, 0.001, 0.002, 0.003, 0.004, 0.01, 0.02, 5.0])
@pytest.mark.parametrize("max_credits", [None, 2, 10, 50])
def test_every_funded_candidate_passed_the_level_filter_and_the_budget(profile, strength, available_usd, max_credits):
    snap = snapshot(**FULL, available_usd=available_usd)
    kw = {} if strength is None else {"strength": strength}
    req = build_requirement(profile, BUDGET, allow_paid=True, max_credits=max_credits, **kw)
    try:
        chain = select(req, snap)
    except ModelUnavailable:
        return
    funded = [c for c in chain.candidates if c.cost_class == "funded"]
    pop = track_population(snap.scores, req.track, today=NOW.date(), max_publish_age_days=7)
    allowed = {req.strength}
    stepped = any("(budget pressure)" in e for e in chain.explanation)
    if stepped:
        assert req.budget_step_down and req.strength != "economy"
        allowed = {STRENGTH_LEVELS[STRENGTH_LEVELS.index(req.strength) - 1]}
    level_ok = set().union(*(level_qualifiers(pop, lvl, FUNDED_POLICY) for lvl in allowed))
    cap = available_usd * USD_TO_CREDITS if max_credits is None else min(available_usd * USD_TO_CREDITS, max_credits)
    assert len(funded) <= FUNDED_POLICY.max_chain_slots
    assert len({c.model_ref.model_family for c in funded}) == len(funded)
    for c in funded:
        assert repo_of(c.model_ref.model_id) in level_ok
        assert available_usd > 0 and c.worst_case_credits <= cap
        assert c.approved_ceiling_credits == pytest.approx(cap)
    if any("funded allowance exhausted" in e for e in chain.explanation):
        assert not funded and CLAUDE not in order(chain)  # never a licence to fall through to paid
