"""Config-consistency guard (issue #294 Phase 0; spec 026 slice 7 US5 AC4).

The audit found the repo carrying a parallel, contradictory configuration
universe: a stale ``pipeline_config.yaml`` naming paid frontier models and
numeric review-score gates (both abolished — Constitution IV free-first +
Constitution VI convergence), plus "points threshold" prose surviving in
live website-generation code. These tests pin the reconciled state so the
contradictions cannot silently return:

  1. Every agent carries a canonical capability ``profile``; under a
     paid-opt-in-OFF snapshot every profile's chain is free-only, and under
     opt-in ON with headroom the guarded paid tail is reachable — governed
     by the PROCESS-level credit snapshot alone, never by an agent's own
     ``paid_opt_in`` field (SC-007(b) / D7).
  2. No profile's chain ever surfaces a paid candidate beyond the one
     sanctioned guarded fallback — checked from the runtime SNAPSHOT's own
     pricing (never a hardcoded family allowlist reconstructed in a test;
     US5 AC4).
  3. Every canonical profile resolves to at least 2 candidates against a
     realistic multi-model snapshot (a real fallback, not a single point of
     failure).
  4. The legacy config files stay deleted.
  5. Point-system language stays out of live code and user-facing docs.
  6. README model prose matches the capability policy table (no drift like
     the historical "Gemma 3 27B" vs the real ``google.gemma-4-31B-it``).

Spec 026 US5 (slice 7) retired ``agents/registry.yaml``'s per-agent
``default_model`` field in favor of a named capability ``profile``, so this
file no longer imports/depends on ``KNOWN_FREE_MODELS``
(``backends/dartmouth.py``) or ``MODEL_FALLBACKS`` (``backends/router.py``) —
both were deleted in Slice 8 — the free-first / guarded-paid-fallback
guarantee they used to encode is now checked one layer down, at the
capability-policy / selection layer, exactly as production ``route_chat``
resolves it (see ``tests/unit/test_model_selection_select.py`` and
``tests/unit/test_profile_schema.py`` for the complementary coverage).
"""

from __future__ import annotations

from pathlib import Path

from llmxive.agents.registry import load as load_registry
from llmxive.model_selection.policy import CAPABILITY_POLICY
from llmxive.model_selection.profiles import PROFILES, build_requirement
from llmxive.model_selection.select import select
from llmxive.model_selection.snapshot import _family_of, _vendor_of
from llmxive.model_selection.types import CallBudget
from tests.unit.test_model_selection_select import (
    CLAUDE,
    GPT_OSS,
    LOCAL,
    QWEN,
    VL,
    _ids,
    _snapshot,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Registry sentinel for scaffolding agents that make no LLM calls (spec 015).
NO_LLM = "deterministic-no-llm"

#: The ONE sanctioned paid family (Constitution IV free-first; guarded
#: fallback governed process-wide by the credit guard, SC-007(b)). ``router``
#: no longer carries a dedicated identity pin for it (Slice 8 deleted
#: ``PAID_FALLBACK_MODELS`` once cost/eligibility moved entirely to the
#: capability-policy + snapshot-pricing layer), so this is DERIVED from
#: ``CLAUDE`` — the SAME shared fixture identity ``test_model_selection_select``
#: already uses to construct every realistic composite snapshot in this suite —
#: rather than a second, independently-maintained "sanctioned paid" constant.
#: Cost itself is NEVER asserted from this family name below — only from the
#: runtime snapshot's own PRICING (see
#: ``test_paid_off_chains_contain_only_snapshot_free_candidates`` etc.); this
#: identifier is used solely to name the guarded fallback for the README
#: display-name check and the "exactly this one paid id" membership checks.
_SANCTIONED_PAID_MODEL_ID = CLAUDE
_SANCTIONED_PAID_MODEL_IDS = frozenset({_SANCTIONED_PAID_MODEL_ID})
_SANCTIONED_PAID_FAMILY = _family_of(
    _SANCTIONED_PAID_MODEL_ID, _vendor_of(_SANCTIONED_PAID_MODEL_ID)
)

#: Human-readable display name each "text chain" policy family must appear as
#: verbatim in the README's "Models & cost" prose (issue #294: prose drifted
#: from config — "Gemma 3 27B" vs the real ``google.gemma-4-31B-it``).
#: Re-pointed at ``CAPABILITY_POLICY`` (spec 026 slice 7): the registry no
#: longer names models at all (US5), so this can no longer diff against
#: ``agents/registry.yaml``.
_POLICY_DISPLAY_NAMES = {
    "glm-5.3": "GLM-5.3",
    "qwen3.5": "Qwen 3.5 122B",
    "gemma-4": "Gemma 4 31B",
    "gpt-oss": "GPT-OSS 120B",
    _SANCTIONED_PAID_FAMILY: "Claude Haiku 4.5",
}

#: Phrases of the abolished point system that must not reappear in live
#: code or user-facing text (spec 015 / Constitution VI).
BANNED_PHRASES = (
    "points threshold",
    "Human reviews count double",
    "review_points_threshold",
)

_CB = CallBudget(max_input_tokens=1000, max_output_tokens=500)


def test_registry_models_are_free_unless_paid_opt_in():
    """US5 AC4 (SC-007(b) / D7): every agent's ``profile`` is canonical, and
    the guarded paid tail's reachability is governed EXCLUSIVELY by the
    process-level credit snapshot — never by ``entry.paid_opt_in`` — exactly
    like ``route_chat``, which derives ``allow_paid`` from
    ``snap.credit.paid_opt_in`` when a caller does not pin it. This test
    therefore never reads ``agent.paid_opt_in`` when deciding whether a
    profile's chain may reach a paid candidate."""
    agents = load_registry().agents
    canonical = set(PROFILES) | {NO_LLM}
    for agent in agents:
        assert agent.profile in canonical, (
            f"agent {agent.name!r} carries an uncanonical profile {agent.profile!r}"
        )

    llm_profiles = {a.profile for a in agents if a.profile != NO_LLM}
    assert llm_profiles, "expected at least one LLM-calling profile in the registry"

    off_snap = _snapshot(paid_opt_in=False, credit_source="live")
    on_snap = _snapshot(paid_opt_in=True, credit_source="live")

    reached_paid = False
    for name in sorted(llm_profiles):
        req_off = build_requirement(name, _CB, allow_paid=off_snap.credit.paid_opt_in)
        chain_off = select(req_off, off_snap)
        assert all(c.pricing.is_free for c in chain_off.candidates), (
            f"profile {name!r} reaches a paid candidate with opt-in OFF"
        )

        req_on = build_requirement(name, _CB, allow_paid=on_snap.credit.paid_opt_in)
        chain_on = select(req_on, on_snap)
        if any(not c.pricing.is_free for c in chain_on.candidates):
            reached_paid = True

    assert reached_paid, (
        "no profile's chain reaches the guarded paid tail under opt-in ON + "
        "headroom — the SC-007(b) guaranteed fallback would be unreachable"
    )


def test_paid_off_chains_contain_only_snapshot_free_candidates():
    """US5 AC4: cost is a property of the runtime SNAPSHOT's pricing, never a
    hardcoded model/family allowlist reconstructed in a test — the capability
    policy records COMPETENCE, not cost. Every canonical profile's paid-OFF
    chain (against a realistic composite snapshot) contains only candidates
    the snapshot itself prices at $0, straight from ``Candidate.pricing``."""
    off_snap = _snapshot(paid_opt_in=False, credit_source="live")
    for name in sorted(PROFILES):
        chain = select(build_requirement(name, _CB, allow_paid=False), off_snap)
        assert chain.candidates, f"profile {name!r} resolved to zero candidates"
        assert all(c.pricing.is_free for c in chain.candidates), (
            f"profile {name!r} paid-OFF chain contains a candidate the "
            f"snapshot itself does NOT price at $0"
        )


def test_every_canonical_profile_resolves_under_the_fixed_snapshot():
    """Every one of the six canonical profiles — not merely the ones an
    ``agents/registry.yaml`` entry currently happens to reference — resolves
    against a realistic composite snapshot. ``vision``/``independent_review``
    have no registry agent pinned to them today but must still be usable by
    any direct ``route_chat(profile=...)`` caller."""
    snap = _snapshot(paid_opt_in=True, credit_source="live")
    for name in sorted(PROFILES):
        chain = select(build_requirement(name, _CB, allow_paid=True), snap)
        assert chain.candidates, f"profile {name!r} resolved to zero candidates"


def test_paid_on_text_profiles_reach_the_sanctioned_guarded_tail():
    """Every TEXT profile's (non-vision) paid-ON projection reaches the ONE
    sanctioned guarded paid fallback (``_SANCTIONED_PAID_MODEL_IDS``) —
    identified by SNAPSHOT membership, never by a family name invented in
    this test."""
    on_snap = _snapshot(paid_opt_in=True, credit_source="live")
    text_profiles = [name for name, p in PROFILES.items() if p.capability != "vision"]
    assert text_profiles, "expected at least one non-vision canonical profile"
    for name in sorted(text_profiles):
        chain = select(build_requirement(name, _CB, allow_paid=True), on_snap)
        ids = {c.model_ref.model_id for c in chain.candidates}
        assert ids & _SANCTIONED_PAID_MODEL_IDS, (
            f"profile {name!r} paid-ON projection never reaches the sanctioned "
            f"guarded paid tail {sorted(_SANCTIONED_PAID_MODEL_IDS)}"
        )


def test_no_paid_candidate_outside_the_sanctioned_guarded_tail():
    """Complementary to the check above: the policy/snapshot combination must
    never surface a paid candidate outside the sanctioned set. Every NON-free
    candidate (per snapshot pricing) across every canonical profile's
    paid-ON projection is a member of ``_SANCTIONED_PAID_MODEL_IDS`` —
    preserving the "no paid family beyond the one sanctioned guarded
    fallback" guarantee WITHOUT re-deriving it from a hardcoded family list."""
    on_snap = _snapshot(paid_opt_in=True, credit_source="live")
    for name in sorted(PROFILES):
        chain = select(build_requirement(name, _CB, allow_paid=True), on_snap)
        paid_ids = {c.model_ref.model_id for c in chain.candidates if not c.pricing.is_free}
        assert paid_ids <= _SANCTIONED_PAID_MODEL_IDS, (
            f"profile {name!r} paid-ON projection surfaces an unsanctioned "
            f"paid candidate {sorted(paid_ids - _SANCTIONED_PAID_MODEL_IDS)}"
        )


def test_unknown_priced_candidate_never_qualifies_as_free():
    """FR-006/SC-003: an unknown-priced candidate must NEVER be admitted as
    free — cost authority is the snapshot's own pricing, and 'unknown' is not
    the same as 'proven $0'. Construct a snapshot where the sanctioned paid
    model's price is unknown (``None``) and assert it is excluded from the
    chain regardless of the paid-opt-in switch."""
    snap = _snapshot(paid_opt_in=True, credit_source="live", paid_pricing=(None, None))
    for allow_paid in (False, True):
        chain = select(build_requirement("deep_review", _CB, allow_paid=allow_paid), snap)
        ids = {c.model_ref.model_id for c in chain.candidates}
        assert not (ids & _SANCTIONED_PAID_MODEL_IDS), (
            "an unknown-priced candidate was admitted — unknown pricing must "
            "never qualify as free"
        )


def test_policy_family_absent_from_snapshot_is_never_resurrected():
    """US5 AC2: the capability policy may ATTRIBUTE competence to a family
    (e.g. ``qwen3-vl``) that is simply ABSENT from the live snapshot (a
    catalog fetch that didn't happen to include it — outage, retirement,
    etc.). ``select`` must never resurrect/synthesize a candidate for a
    family the snapshot doesn't actually carry."""
    snap = _snapshot(model_ids=[QWEN, GPT_OSS, LOCAL])  # VL (qwen3-vl) absent
    chain = select(build_requirement("vision", _CB), snap)
    ids = _ids(chain)
    assert ids == [QWEN]
    assert VL not in ids
    assert all(c.model_ref.model_family != "qwen3-vl" for c in chain.candidates)


def test_every_llm_registry_model_has_a_fallback_chain():
    # Every canonical profile resolves to >= 2 candidates against a realistic
    # (multi-model) composite snapshot — a profile that only ever resolves to
    # a SINGLE candidate has no real fallback if that one model flaps, the
    # property the legacy per-model ``MODEL_FALLBACKS`` chains used to
    # guarantee.
    snap = _snapshot(paid_opt_in=True, credit_source="live")
    for name in sorted(PROFILES):
        chain = select(build_requirement(name, _CB, allow_paid=True), snap)
        assert len(chain.candidates) >= 2, (
            f"profile {name!r} resolves to only {len(chain.candidates)} candidate(s) "
            f"against the composite snapshot (a single vLLM outage would strand it)"
        )


def test_legacy_pipeline_config_stays_deleted():
    for name in ("pipeline_config.yaml", "pipeline_schema.json"):
        assert not (REPO_ROOT / name).exists(), (
            f"{name} was deleted in issue #294 Phase 0 (paid models + score "
            f"gates contradicting the constitution); do not resurrect it — "
            f"agents/registry.yaml is the single source of truth"
        )


def test_no_point_system_language_in_live_code_or_docs():
    targets = [
        *sorted((REPO_ROOT / "src" / "llmxive").rglob("*.py")),
        REPO_ROOT / "README.md",
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / "web" / "index.html",
        REPO_ROOT / "web" / "data" / "projects.json",
    ]
    offenders: list[str] = []
    for path in targets:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for phrase in BANNED_PHRASES:
            if phrase in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {phrase!r}")
    assert not offenders, (
        "abolished point-system language found (spec 015 / Constitution VI): "
        + "; ".join(offenders)
    )


def _readme_models_section() -> str:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    # ``main`` rewrote the README; the section is now "Models and compute".
    start = readme.index("## Models and compute")
    end = readme.index("\n## ", start + 1)
    return readme[start:end]


def test_readme_model_names_match_registry():
    # The registry no longer names models at all (US5) — re-pointed at
    # CAPABILITY_POLICY (spec 026 slice 7 AC4) so README prose cannot drift
    # from the reviewed capability table the way it drifted from the old
    # per-agent ``default_model`` field (issue #294).
    section = _readme_models_section()
    for family, display in _POLICY_DISPLAY_NAMES.items():
        assert family in CAPABILITY_POLICY.entries, f"{family!r} missing from CAPABILITY_POLICY"
        assert display in section, (
            f"README 'Models and compute' section must name {display!r} (policy family "
            f"{family!r}) verbatim so prose cannot drift from the capability policy "
            f"(issue #294: 'Gemma 3 27B' vs google.gemma-4-31B-it)"
        )
    assert "Gemma 3" not in section, "README still names the retired gemma-3 family"
