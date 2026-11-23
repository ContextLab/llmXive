"""Pure-selector tests (spec 026, slice 2 / US2): eligibility, deterministic
tie-breaks, paid guard, exclude_*, and required/preferred independence.

All fixtures are REAL immutable contract objects and every call to ``select`` is
a pure function call — no mocks, no network (Constitution III): the selector IS
pure, so the "real" test is exercising it against real ``RuntimeSnapshot``s.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from llmxive.model_selection import build_requirement, select
from llmxive.model_selection.snapshot import _family_of, _vendor_of
from llmxive.model_selection.tokens import call_budget_for
from llmxive.model_selection.types import (
    CallBudget,
    CreditGuardSnapshot,
    IndependenceBaseline,
    ModelPricing,
    ModelRef,
    ModelRequirement,
    ModelUnavailable,
    RuntimeSnapshot,
    SnapshotProvenance,
)
from llmxive.state import execution_status

NOW = datetime(2026, 7, 16, 12, 0, 0, tzinfo=UTC)
DARTMOUTH_EP = "https://chat.dartmouth.edu"

QWEN = "qwen.qwen3.5-122b"
GEMMA4 = "google.gemma-4-31B-it"
GPT_OSS = "openai.gpt-oss-120b"
GEMMA3 = "google.gemma-3-27b-it"  # in catalog, NOT in policy (approved correction)
VL = "qwen.qwen3-vl:32b"
CLAUDE = "anthropic.claude-haiku-4-5-20251001"  # paid; dated id → family claude-haiku-4-5
LOCAL = "Qwen/Qwen2.5-3B-Instruct"

FREE_TEXT = [QWEN, GEMMA4, GPT_OSS]


def _ref(mid: str, *, backend: str = "dartmouth", endpoint: str = DARTMOUTH_EP) -> ModelRef:
    vendor = _vendor_of(mid)
    return ModelRef(backend, endpoint, mid, _family_of(mid, vendor), vendor)


def _snapshot(
    *,
    model_ids: list[str] | None = None,
    paid_opt_in: bool = False,
    credit_source: str = "live",
    available_headroom: float = 1400.0,
    catalog_source: str = "live",
    catalog_age_s: float = 0.0,
    credit_age_s: float = 0.0,
    paid_pricing: tuple[float | None, float | None] = (1e-6, 5e-6),
    now: datetime = NOW,
) -> RuntimeSnapshot:
    """Build a fixture snapshot. Defaults: the full free text chain + vision +
    the (policy-absent) gemma-3 + the paid claude + the local fallback."""
    if model_ids is None:
        model_ids = [QWEN, GEMMA4, GPT_OSS, VL, GEMMA3, CLAUDE, LOCAL]

    models: list[ModelRef] = []
    pricing: dict[str, ModelPricing] = {}
    for mid in model_ids:
        backend = "local" if mid == LOCAL else "dartmouth"
        endpoint = "local" if mid == LOCAL else DARTMOUTH_EP
        models.append(_ref(mid, backend=backend, endpoint=endpoint))
        pricing[mid] = ModelPricing(*paid_pricing) if mid == CLAUDE else ModelPricing(0.0, 0.0)

    credit = CreditGuardSnapshot(
        balance=1000.0,
        spend=100.0,
        max_budget=2000.0,
        paid_opt_in=paid_opt_in,
        budget_fraction=0.75,
        effective_cap=1500.0,
        available_headroom=available_headroom,
        budget_reset_at="2026-07-17T03:45:00-04:00",
        observed_at=now,
        source=credit_source,
    )
    sources = {
        "catalog": SnapshotProvenance(catalog_source, now, catalog_age_s),
        "local": SnapshotProvenance("live", now, 0.0),
        "credit": SnapshotProvenance(credit_source, now, credit_age_s),
    }
    return RuntimeSnapshot(
        models=tuple(models),
        pricing=pricing,
        health={m.model_id: "ok" for m in models},
        credit=credit,
        observed_at=now,
        sources=sources,
        digest="TEST-DIGEST",
    )


def _cb() -> CallBudget:
    return call_budget_for([{"role": "user", "content": "summarize this text please"}], 512)


def _ids(chain) -> list[str]:
    return [c.model_ref.model_id for c in chain.candidates]


# --------------------------------------------------------------------------- #
# SC-001: purity + byte-identical determinism
# --------------------------------------------------------------------------- #


def test_select_is_byte_identical_across_calls():
    snap = _snapshot()
    req = build_requirement("deep_review", _cb())
    a = select(req, snap)
    b = select(req, snap)
    assert a == b
    assert repr(a) == repr(b)
    assert _ids(a) == _ids(b)


def test_select_does_not_read_environment(monkeypatch):
    # A pure function must not consult env; poison the keys it would touch if impure.
    for var in ("DARTMOUTH_CHAT_API_KEY", "LLMXIVE_PAID_OPT_IN", "LLMXIVE_PAID_BUDGET_FRACTION"):
        monkeypatch.setenv(var, "POISONED")
    snap = _snapshot(paid_opt_in=True, credit_source="live")
    req = build_requirement("deep_review", _cb(), allow_paid=True)
    # opt-in/headroom come from the SNAPSHOT, not env → paid admitted regardless.
    assert CLAUDE in _ids(select(req, snap))


def test_select_does_not_mutate_snapshot():
    snap = _snapshot()
    before = list(snap.models), dict(snap.pricing)
    select(build_requirement("cheap_structured", _cb()), snap)
    assert (list(snap.models), dict(snap.pricing)) == before


# --------------------------------------------------------------------------- #
# Golden free chain + free-before-paid ordering (US2 scenario 2 / FR-008)
# --------------------------------------------------------------------------- #


def test_deep_review_paid_off_free_chain():
    chain = select(build_requirement("deep_review", _cb()), _snapshot())
    assert _ids(chain) == [QWEN, GEMMA4, GPT_OSS]  # qwen (tier3) → gemma-4 → gpt-oss (alpha)
    assert GEMMA3 not in _ids(chain)  # policy-absent (approved gemma-3→gemma-4 correction)
    assert VL not in _ids(chain)  # vision-only family never intrudes on the text chain


def test_paid_on_appends_guarded_paid_after_all_free():
    snap = _snapshot(paid_opt_in=True, credit_source="live")
    chain = select(build_requirement("deep_review", _cb(), allow_paid=True), snap)
    assert _ids(chain) == [QWEN, GEMMA4, GPT_OSS, CLAUDE]  # free before paid (rung 3)
    assert chain.candidates[-1].model_ref.model_id == CLAUDE


def test_max_candidates_truncates_in_order():
    snap = _snapshot(paid_opt_in=True, credit_source="live")
    req = build_requirement("deep_review", _cb(), allow_paid=True, max_candidates=2)
    assert _ids(select(req, snap)) == [QWEN, GEMMA4]


# --------------------------------------------------------------------------- #
# Paid guard (US2 scenario 4 / FR-003 / FR-007 / SC-003)
# --------------------------------------------------------------------------- #


def test_paid_excluded_when_opt_in_off():
    snap = _snapshot(paid_opt_in=False, credit_source="live")
    chain = select(build_requirement("deep_review", _cb(), allow_paid=True), snap)
    assert CLAUDE not in _ids(chain)
    assert any("paid not admitted" in e for e in chain.explanation)


def test_paid_fails_closed_on_stale_credit_source():
    # C6 / FR-007: paid must fail closed unless the credit component is LIVE.
    snap = _snapshot(paid_opt_in=True, credit_source="last_known_good")
    chain = select(build_requirement("deep_review", _cb(), allow_paid=True), snap)
    assert CLAUDE not in _ids(chain)


def test_paid_excluded_when_cost_exceeds_headroom():
    snap = _snapshot(paid_opt_in=True, credit_source="live", available_headroom=1.0)
    chain = select(build_requirement("deep_review", _cb(), allow_paid=True), snap)
    assert CLAUDE not in _ids(chain)  # worst_case (~2.6 credits) > 1.0 headroom


def test_max_credits_tightens_the_ceiling():
    snap = _snapshot(paid_opt_in=True, credit_source="live", available_headroom=1400.0)
    req = build_requirement("deep_review", _cb(), allow_paid=True, max_credits=1)
    assert CLAUDE not in _ids(select(req, snap))  # min(1, 1400)=1 < ~2.6


def test_unknown_price_is_never_free_and_excluded():
    # SC-003: a model with unknown pricing is neither free nor priceable → excluded.
    snap = _snapshot(paid_opt_in=True, credit_source="live", paid_pricing=(None, None))
    for allow in (False, True):
        chain = select(build_requirement("deep_review", _cb(), allow_paid=allow), snap)
        assert CLAUDE not in _ids(chain)


def test_paid_candidate_carries_pricing_and_ceiling():
    snap = _snapshot(paid_opt_in=True, credit_source="live", available_headroom=500.0)
    chain = select(build_requirement("deep_review", _cb(), allow_paid=True), snap)
    paid = next(c for c in chain.candidates if c.model_ref.model_id == CLAUDE)
    free = next(c for c in chain.candidates if c.model_ref.model_id == QWEN)
    assert paid.worst_case_credits > 0.0
    assert paid.approved_ceiling_credits == 500.0  # effective_per_call_cap at selection
    assert free.worst_case_credits == 0.0
    assert free.approved_ceiling_credits == 0.0


# --------------------------------------------------------------------------- #
# require_paid cost-class escalation (spec 026 slice 6)
# --------------------------------------------------------------------------- #


def test_require_paid_excludes_all_free_and_leads_with_paid():
    # allow_paid + require_paid + live/opted-in credit with headroom → only the
    # paid candidate (claude-haiku) survives; free (qwen/gemma/gpt-oss/local) excluded.
    snap = _snapshot(paid_opt_in=True, credit_source="live")
    req = build_requirement(
        "deep_review", _cb(), allow_paid=True, require_paid=True, max_candidates=8
    )
    chain = select(req, snap)
    ids = _ids(chain)
    assert ids and all("claude" in i for i in ids)  # paid-only; no free ids present
    assert QWEN not in ids
    assert GEMMA4 not in ids
    assert GPT_OSS not in ids
    assert LOCAL not in ids


def test_require_paid_with_allow_paid_false_fails_closed():
    snap = _snapshot(paid_opt_in=True, credit_source="live")
    req = build_requirement("deep_review", _cb(), allow_paid=False, require_paid=True)
    with pytest.raises(ModelUnavailable) as exc:
        select(req, snap)
    assert "require_paid" in str(exc.value).lower()


def test_require_paid_over_ceiling_fails_closed():
    # paid admissible in general, but per-call worst_case > cap → paid excluded,
    # free excluded by require_paid → ModelUnavailable (does NOT fall back to free).
    snap = _snapshot(paid_opt_in=True, credit_source="live", available_headroom=0.0001)
    req = build_requirement(
        "deep_review", _cb(), allow_paid=True, require_paid=True, max_candidates=8
    )
    with pytest.raises(ModelUnavailable):
        select(req, snap)


# --------------------------------------------------------------------------- #
# Capability policy ∩ snapshot (US2 scenario 3 / FR-006 / SC-002)
# --------------------------------------------------------------------------- #


def test_capability_not_attributed_excludes_model():
    # qwen3-vl is present but the policy attributes it ONLY "vision" → excluded
    # from a deep requirement even though it is a live catalog model.
    chain = select(build_requirement("deep_review", _cb()), _snapshot())
    assert VL not in _ids(chain)


def test_vision_requirement_selects_only_vision_family():
    # qwen3.5 (policy v2) leads on quality tier; qwen3-vl remains the peer.
    chain = select(build_requirement("vision", _cb()), _snapshot())
    assert _ids(chain) == [QWEN, VL]


def test_confirmed_absence_excludes_model():
    # SC-002: a model absent from a successfully-fetched catalog is not selected.
    snap = _snapshot(model_ids=[GEMMA4, GPT_OSS, LOCAL])  # qwen absent
    chain = select(build_requirement("deep_review", _cb()), snap)
    assert QWEN not in _ids(chain)
    assert _ids(chain)[0] == GEMMA4


def test_min_context_tokens_gate():
    # 200_000 excludes gemma-4/gpt-oss (128K) and claude(200K passes? no, need >200K),
    # keeps only qwen (256K).
    req = build_requirement("deep_review", _cb(), min_context_tokens=200_001)
    chain = select(req, _snapshot(paid_opt_in=True, credit_source="live", available_headroom=1400.0))
    assert _ids(chain) == [QWEN]


# --------------------------------------------------------------------------- #
# Snapshot freshness (SC-002: outage vs absence)
# --------------------------------------------------------------------------- #


def test_last_known_good_within_age_is_eligible():
    snap = _snapshot(catalog_source="last_known_good", catalog_age_s=100.0)
    req = build_requirement("deep_review", _cb())  # default max_catalog_age_s=3600
    assert _ids(select(req, snap)) == [QWEN, GEMMA4, GPT_OSS]


def test_stale_last_known_good_beyond_age_is_excluded():
    snap = _snapshot(catalog_source="last_known_good", catalog_age_s=5000.0)
    req = build_requirement("deep_review", _cb())  # max_catalog_age_s=3600 < 5000
    with pytest.raises(ModelUnavailable):
        select(req, snap)  # all catalog models too stale; only local remains (no "deep")


def test_cold_start_no_models_raises():
    snap = _snapshot(model_ids=[], catalog_source="unavailable")
    with pytest.raises(ModelUnavailable):
        select(build_requirement("cheap_structured", _cb()), snap)


# --------------------------------------------------------------------------- #
# Fresh-required (judgment) reviews: max_catalog_age_s gates catalog AND
# credit/opt-in (FR-007), failing the WHOLE selection closed — even for free.
# --------------------------------------------------------------------------- #


def test_fresh_required_review_fails_closed_on_stale_credit():
    # independent_review has max_catalog_age_s=900; a credit LKG older than that
    # fails closed even though the resulting model (qwen) is free.
    snap = _snapshot(credit_source="last_known_good", credit_age_s=1000.0)
    with pytest.raises(ModelUnavailable, match="credit"):
        select(build_requirement("independent_review", _cb()), snap)


def test_fresh_required_review_fails_closed_on_unavailable_credit():
    snap = _snapshot(credit_source="unavailable")
    with pytest.raises(ModelUnavailable, match="credit"):
        select(build_requirement("independent_review", _cb()), snap)


def test_fresh_required_review_fails_closed_on_stale_catalog():
    snap = _snapshot(catalog_source="last_known_good", catalog_age_s=1000.0)
    with pytest.raises(ModelUnavailable, match="catalog"):
        select(build_requirement("independent_review", _cb()), snap)


def test_fresh_required_review_succeeds_when_all_components_fresh():
    chain = select(build_requirement("independent_review", _cb()), _snapshot())
    assert _ids(chain) == [QWEN, GEMMA4, GPT_OSS]  # free deep chain, all live


def test_fresh_required_review_allows_lkg_within_age():
    # A credit LKG WITHIN the freshness window is fresh-enough (age-bounded, FR-007).
    snap = _snapshot(credit_source="last_known_good", credit_age_s=100.0)
    chain = select(build_requirement("independent_review", _cb()), snap)
    assert _ids(chain) == [QWEN, GEMMA4, GPT_OSS]


def test_ordinary_review_ignores_credit_freshness():
    # A non-fresh-required call proceeds on free models even when credit is
    # unavailable — no regression for low-risk calls (FR-007).
    snap = _snapshot(credit_source="unavailable")
    chain = select(build_requirement("deep_review", _cb()), snap)
    assert _ids(chain) == [QWEN, GEMMA4, GPT_OSS]


# --------------------------------------------------------------------------- #
# Unconditional exclusions (SC-005)
# --------------------------------------------------------------------------- #


def test_exclude_models():
    req = build_requirement("deep_review", _cb(), exclude_models=frozenset({QWEN}))
    assert QWEN not in _ids(select(req, _snapshot()))


def test_exclude_families():
    req = build_requirement("deep_review", _cb(), exclude_families=frozenset({"gemma-4"}))
    assert GEMMA4 not in _ids(select(req, _snapshot()))


def test_exclude_vendors():
    req = build_requirement("deep_review", _cb(), exclude_vendors=frozenset({"openai"}))
    assert GPT_OSS not in _ids(select(req, _snapshot()))


def test_exclude_endpoints():
    req = build_requirement("cheap_structured", _cb(), exclude_endpoints=frozenset({DARTMOUTH_EP}))
    ids = _ids(select(req, _snapshot()))
    assert ids == [LOCAL]  # only the local-endpoint model survives


# --------------------------------------------------------------------------- #
# Independence (US4 / FR-009 / SC-005)
# --------------------------------------------------------------------------- #


def test_required_family_independence_excludes_baseline_family():
    base = IndependenceBaseline(families=frozenset({"qwen3.5"}))
    req = ModelRequirement(
        capability="deep",
        call_budget=_cb(),
        independence_against=base,
        required_independence=frozenset({"family"}),
    )
    chain = select(req, _snapshot())
    assert QWEN not in _ids(chain)
    assert _ids(chain)[0] == GEMMA4


def test_required_independence_unmet_raises():
    # Baseline covers every eligible deep family → fail closed (ModelUnavailable).
    base = IndependenceBaseline(families=frozenset({"qwen3.5", "gemma-4", "gpt-oss"}))
    req = ModelRequirement(
        capability="deep",
        call_budget=_cb(),
        independence_against=base,
        required_independence=frozenset({"family"}),
    )
    with pytest.raises(ModelUnavailable):
        select(req, _snapshot())


def test_preferred_independence_reorders_within_a_quality_tier():
    # Rung 5 breaks ties AMONG equal-quality-tier candidates: with the baseline
    # family = gemma-4, gpt-oss (differs) is promoted above gemma-4 (matches) —
    # both tier 2 — while qwen3.5 (tier 3) still leads via the higher rung-4.
    base = IndependenceBaseline(families=frozenset({"gemma-4"}))
    req = ModelRequirement(
        capability="deep",
        call_budget=_cb(),
        independence_against=base,
        preferred_independence=frozenset({"family"}),
    )
    chain = select(req, _snapshot())
    assert _ids(chain) == [QWEN, GPT_OSS, GEMMA4]  # gpt-oss jumps gemma-4 (pref met)
    assert not any("preferred_independence" in e for e in chain.explanation)  # someone differs


def test_preferred_independence_does_not_override_quality_tier():
    # FR-008 rung precedence: preferred independence (rung 5) NEVER outranks
    # preferred quality tier (rung 4). Even though the tier-1 local model is the
    # only endpoint-independent option, qwen3.5 (tier 3) still leads.
    base = IndependenceBaseline(endpoints=frozenset({DARTMOUTH_EP}))
    req = ModelRequirement(
        capability="cheap",
        call_budget=_cb(),
        independence_against=base,
        preferred_independence=frozenset({"serving_endpoint"}),
    )
    chain = select(req, _snapshot())
    assert _ids(chain)[0] == QWEN  # quality tier dominates the endpoint preference
    assert LOCAL in _ids(chain)


def test_preferred_independence_unmet_degrades_with_explanation():
    # All eligible deep models are Dartmouth-endpoint; preferring endpoint-diversity
    # cannot be met → proceed + record the unmet preference (FR-009 scenario 3).
    base = IndependenceBaseline(endpoints=frozenset({DARTMOUTH_EP}))
    req = ModelRequirement(
        capability="deep",
        call_budget=_cb(),
        independence_against=base,
        preferred_independence=frozenset({"serving_endpoint"}),
    )
    chain = select(req, _snapshot())
    assert _ids(chain) == [QWEN, GEMMA4, GPT_OSS]  # unchanged; degraded toward baseline
    assert any("preferred_independence 'serving_endpoint' unmet" in e for e in chain.explanation)


def test_exclude_beats_baseline_unconditionally():
    # exclude_* is independent of the baseline: even though qwen is the ONLY
    # family-independent choice here (baseline covers gemma-4/gpt-oss), excluding
    # it removes it — exclusion is unconditional, not a preference.
    base = IndependenceBaseline(families=frozenset({"gemma-4", "gpt-oss"}))
    req = ModelRequirement(
        capability="deep",
        call_budget=_cb(),
        independence_against=base,
        preferred_independence=frozenset({"family"}),
        exclude_models=frozenset({QWEN}),
    )
    chain = select(req, _snapshot())
    assert QWEN not in _ids(chain)
    assert _ids(chain) == [GEMMA4, GPT_OSS]  # remain eligible (preference, not required)


def test_chain_provenance_fields():
    snap = _snapshot()
    cb = _cb()
    chain = select(ModelRequirement(capability="deep", call_budget=cb), snap)
    assert chain.resolved_at == snap.observed_at
    assert chain.snapshot_digest == "TEST-DIGEST"
    assert chain.selection_policy_version == 5
    assert set(chain.snapshot_provenance) == {"catalog", "local", "credit"}
    assert chain.call_budget == cb


# --------------------------------------------------------------------------- #
# SC-007 / US5: golden-chain model-ID PROJECTIONS (behavior preservation).
# The legacy router chain MODEL_FALLBACKS["qwen.qwen3.5-122b"] =
# [gemma-3, gpt-oss, claude(guarded)]. The consolidated policy reproduces it as a
# model-ID projection with the maintainer-approved gemma-3 -> gemma-4 correction.
# (a) paid off  -> free peers qwen -> gemma-4 -> gpt-oss (claude guarded off).
# (b) paid on   -> that sequence + the guarded paid claude tail.
# (c) local backend fallback ordering verified separately (appended last, free).
# --------------------------------------------------------------------------- #

# The Dartmouth text catalog (no local) — the legacy per-backend peer set. gemma-3
# is present in the catalog but absent from the policy (approved correction).
_DARTMOUTH_TEXT = [QWEN, GEMMA4, GPT_OSS, GEMMA3, CLAUDE]


def test_sc007_golden_chain_paid_off():
    chain = select(
        build_requirement("standard_generation", _cb()),
        _snapshot(model_ids=_DARTMOUTH_TEXT, paid_opt_in=False),
    )
    assert _ids(chain) == [QWEN, GEMMA4, GPT_OSS]


def test_sc007_golden_chain_paid_on_with_headroom_appends_guarded_paid_tail():
    chain = select(
        build_requirement("standard_generation", _cb(), allow_paid=True),
        _snapshot(model_ids=_DARTMOUTH_TEXT, paid_opt_in=True, available_headroom=1400.0),
    )
    assert _ids(chain) == [QWEN, GEMMA4, GPT_OSS, CLAUDE]


def test_sc007_gemma3_excluded_even_though_present_in_catalog():
    chain = select(
        build_requirement("standard_generation", _cb()),
        _snapshot(model_ids=_DARTMOUTH_TEXT, paid_opt_in=False),
    )
    assert GEMMA3 not in _ids(chain)


def test_sc007_local_backend_fallback_ordered_last_free():
    chain = select(
        build_requirement("standard_generation", _cb()),
        _snapshot(model_ids=[QWEN, GEMMA4, GPT_OSS, LOCAL], paid_opt_in=False),
    )
    assert _ids(chain) == [QWEN, GEMMA4, GPT_OSS, LOCAL]
    assert chain.candidates[-1].model_ref.backend == "local"


def test_sc007_composite_snapshot_retains_guarded_paid_tail_after_local():
    # Review finding 2: the FULL composite snapshot (dartmouth free + local free +
    # paid claude) produces FOUR free candidates before the guarded paid tail
    # (free-before-paid, FR-008). standard_generation's candidate limit MUST retain
    # claude — a Dartmouth-only snapshot hid this because it had only 3 free. Uses
    # the default composite _snapshot (qwen, gemma-4, gpt-oss, VL, gemma-3, claude,
    # local); VL is vision-only + gemma-3 is policy-absent → both excluded.
    snap = _snapshot(paid_opt_in=True, credit_source="live", available_headroom=1400.0)
    chain = select(build_requirement("standard_generation", _cb(), allow_paid=True), snap)
    assert _ids(chain) == [QWEN, GEMMA4, GPT_OSS, LOCAL, CLAUDE]  # free chain + local, THEN paid
    assert chain.candidates[-1].model_ref.model_id == CLAUDE  # guarded paid tail survives
    assert chain.candidates[-1].model_ref.backend == "dartmouth"


# --------------------------------------------------------------------------- #
# SC-007 / US6: per-tier EXECUTION-LADDER golden model-ID projections.
# These tie the REAL ``execution_status`` escalation ladder to ``select()`` (no
# mocks): each rung's ``TierConstraint.to_overrides()`` is fed straight into a
# ``ModelRequirement`` and run against the SC-007 fixture snapshot, so the
# ladder cannot silently desync from the selector.
#   - tier 1 = free second opinion → ``exclude_leader`` drops whatever ranks
#     FIRST (qwen, resolved by a pure pass-1 ``select()`` call mirroring
#     ``route_chat``'s two-pass translation — spec 026 slice 7) and the leader
#     becomes the policy's next-best free model gemma-4 (the sanctioned
#     gpt-oss → gemma-4 delta, spec.md US6/SC-007).
#   - tier 2 = a THIRD free family → ``exclude_leaders=2`` drops the top two
#     (the third free rung ``main`` added), so gpt-oss leads here.
#   - tier 3 = the single paid rung (require_paid) → paid-only, leader claude.
# --------------------------------------------------------------------------- #

QWEN_DEFAULT = QWEN  # rank-one free model the ladder's tier-1 rung excludes


def test_execution_tier1_golden_leads_with_gemma4(monkeypatch):
    # Hermetic: no paid escalation → tier 1 is the free second-opinion rung.
    monkeypatch.delenv("LLMXIVE_EXECUTION_PAID_ESCALATION", raising=False)

    ov1 = execution_status.tier_constraint(1).to_overrides()
    # The ladder rung really is free-only + drops whatever leads (no model id):
    assert ov1.allow_paid is False
    assert ov1.require_paid is False
    assert ov1.exclude_leader is True
    assert ov1.exclude_models == frozenset()

    base = build_requirement("standard_generation", _cb())
    snap = _snapshot(model_ids=[QWEN, GEMMA4, GPT_OSS, LOCAL], paid_opt_in=False)
    # PASS 1 (mirrors route_chat's two-pass exclude_leader translation): resolve
    # who leads under the base requirement.
    leader_chain = select(base, snap)
    assert leader_chain.candidates[0].model_ref.model_id == QWEN_DEFAULT
    # PASS 2: exclude exactly that leader.
    req = replace(base, exclude_models=base.exclude_models | {QWEN_DEFAULT})
    chain = select(req, snap)

    # qwen excluded across the whole chain; leader is gemma-4 (was pinned gpt-oss),
    # then gpt-oss, then the local fallback last — the sanctioned tier-1 delta.
    assert _ids(chain) == [GEMMA4, GPT_OSS, LOCAL]
    assert _ids(chain)[0] == GEMMA4
    assert QWEN not in _ids(chain)


def test_execution_tier2_golden_leads_with_the_third_free_model(monkeypatch):
    """Tier 2 drives the REAL ``resolve_chain`` (the function ``route_chat`` uses)
    with the rung's own overrides: the two best-ranked candidates are dropped and
    the policy's third-best free model leads — no model id in the ladder."""
    from llmxive.model_selection.route import resolve_chain

    monkeypatch.delenv("LLMXIVE_EXECUTION_PAID_ESCALATION", raising=False)
    ov2 = execution_status.tier_constraint(2).to_overrides()
    assert ov2.allow_paid is False and ov2.require_paid is False
    assert ov2.exclude_leaders == 2 and ov2.exclude_models == frozenset()

    snap = _snapshot(model_ids=[QWEN, GEMMA4, GPT_OSS, LOCAL], paid_opt_in=False)
    requirement, chain = resolve_chain(
        [], profile="standard_generation", max_tokens=1, overrides=ov2, snapshot=snap
    )
    assert requirement.exclude_models == frozenset({QWEN, GEMMA4})
    assert _ids(chain) == [GPT_OSS, LOCAL]

    # The three free rungs lead with three DIFFERENT models, in policy order.
    leaders = [
        _ids(resolve_chain(
            [], profile="standard_generation", max_tokens=1, snapshot=snap,
            overrides=execution_status.tier_constraint(t).to_overrides(),
        )[1])[0]
        for t in range(3)
    ]
    assert leaders == [QWEN, GEMMA4, GPT_OSS]


def test_execution_paid_rung_golden_is_paid_only_leader_claude(monkeypatch):
    # Paid escalation enabled → the ladder gains the single paid rung at tier 3.
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    assert len(execution_status.model_tier_ladder()) == 4  # three free rungs + one paid rung

    ov2 = execution_status.tier_constraint(3).to_overrides()
    assert ov2.allow_paid is True and ov2.require_paid is True

    req = build_requirement(
        "standard_generation",
        _cb(),
        allow_paid=ov2.allow_paid,
        require_paid=ov2.require_paid,
        max_candidates=8,
    )
    # Paid-admissible SC-007 snapshot: live/opted-in credit with headroom.
    snap = _snapshot(paid_opt_in=True, credit_source="live", available_headroom=1400.0)
    chain = select(req, snap)

    # require_paid excludes every free candidate → paid-only chain, leader claude.
    assert _ids(chain) == [CLAUDE]
    assert QWEN not in _ids(chain)
    assert GEMMA4 not in _ids(chain)
    assert GPT_OSS not in _ids(chain)
    assert LOCAL not in _ids(chain)


# --------------------------------------------------------------------------- #
# Policy v3: the glm-5.3 family (``zai-org.glm-5.3``) is the TEXT leader — the
# registry-wide default model on ``main`` when it was merged into spec 026. These
# golden projections use the REAL ``CAPABILITY_POLICY`` (no injected policy).
# --------------------------------------------------------------------------- #
GLM = "zai-org.glm-5.3"
_DARTMOUTH_TEXT_WITH_GLM = [QWEN, GEMMA4, GPT_OSS, GEMMA3, CLAUDE, GLM]


def test_policy_v3_names_glm_as_a_non_vision_reasoning_family():
    from llmxive.model_selection.policy import CAPABILITY_POLICY, SELECTION_POLICY_VERSION
    from llmxive.model_selection.snapshot import _family_of, _vendor_of

    assert SELECTION_POLICY_VERSION == 5 == CAPABILITY_POLICY.version
    family = _family_of(GLM, _vendor_of(GLM))
    assert family == "glm-5.3"
    entry = CAPABILITY_POLICY.entry(family)
    assert entry is not None
    assert entry.capabilities == frozenset({"cheap", "standard", "deep"})  # no vision
    assert entry.features == frozenset({"reasoning", "structured"})
    # Strictly the best tier, so it leads every text chain it is eligible for.
    assert entry.quality_tier > max(
        e.quality_tier for f, e in CAPABILITY_POLICY.entries.items() if f != family
    )
    # Conservative (assumed) window: no larger than its Dartmouth text peers'.
    assert entry.max_context_tokens == min(
        CAPABILITY_POLICY.entry(f).max_context_tokens for f in ("gemma-4", "gpt-oss")
    )


@pytest.mark.parametrize(
    "profile",
    ["cheap_structured", "standard_generation", "deep_review", "deep_code", "independent_review"],
)
def test_glm_leads_every_text_profile_ahead_of_qwen(profile):
    chain = select(
        build_requirement(profile, _cb()),
        _snapshot(model_ids=_DARTMOUTH_TEXT_WITH_GLM, paid_opt_in=False),
    )
    ids = _ids(chain)
    assert ids[0] == GLM
    assert ids.index(GLM) < ids.index(QWEN)


def test_glm_golden_free_chain_paid_off():
    chain = select(
        build_requirement("standard_generation", _cb()),
        _snapshot(model_ids=_DARTMOUTH_TEXT_WITH_GLM, paid_opt_in=False),
    )
    assert _ids(chain) == [GLM, QWEN, GEMMA4, GPT_OSS]


def test_glm_golden_chain_keeps_the_guarded_paid_tail_last():
    chain = select(
        build_requirement("standard_generation", _cb(), allow_paid=True),
        _snapshot(model_ids=_DARTMOUTH_TEXT_WITH_GLM, paid_opt_in=True, available_headroom=1400.0),
    )
    assert _ids(chain) == [GLM, QWEN, GEMMA4, GPT_OSS, CLAUDE]


def test_glm_is_never_offered_for_vision():
    chain = select(
        build_requirement("vision", _cb()),
        _snapshot(model_ids=[GLM, QWEN, VL, GEMMA4, GPT_OSS], paid_opt_in=False),
    )
    assert GLM not in _ids(chain)
    assert _ids(chain)[0] == QWEN


def test_absent_glm_leaves_the_pre_v3_chain_unchanged():
    """The policy names a family; the catalog decides presence. Without glm in the
    snapshot the chain is exactly the v2 one."""
    chain = select(
        build_requirement("standard_generation", _cb()),
        _snapshot(model_ids=_DARTMOUTH_TEXT, paid_opt_in=False),
    )
    assert _ids(chain) == [QWEN, GEMMA4, GPT_OSS]
