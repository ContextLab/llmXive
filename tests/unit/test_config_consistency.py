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
  2. The versioned capability policy (``model_selection/policy.py``) admits
     no paid family beyond the one sanctioned guarded fallback.
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
both stay defined (Slice 8 owns their deletion) but the free-first / guarded-
paid-fallback guarantee they used to encode is now checked one layer down, at
the capability-policy / selection layer, exactly as production ``route_chat``
resolves it (see ``tests/unit/test_model_selection_select.py`` and
``tests/unit/test_profile_schema.py`` for the complementary coverage).
"""

from __future__ import annotations

from pathlib import Path

from llmxive.agents.registry import load as load_registry
from llmxive.model_selection.policy import CAPABILITY_POLICY
from llmxive.model_selection.profiles import PROFILES, build_requirement
from llmxive.model_selection.select import select
from llmxive.model_selection.types import CallBudget
from tests.unit.test_model_selection_select import _snapshot

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Registry sentinel for scaffolding agents that make no LLM calls (spec 015).
NO_LLM = "deterministic-no-llm"

#: The ONE sanctioned paid family (Constitution IV free-first; guarded
#: fallback governed process-wide by the credit guard, SC-007(b)).
_SANCTIONED_PAID_FAMILY = "claude-haiku-4-5"

#: Every OTHER family the capability policy currently attributes competence
#: to — all unconditionally free. Pinned here directly (not derived from
#: ``KNOWN_FREE_MODELS``, which this file no longer depends on) so a policy
#: edit that quietly adds another paid-looking family fails loudly and must
#: be classified on purpose.
_KNOWN_FREE_POLICY_FAMILIES = frozenset({"qwen3.5", "gemma-4", "gpt-oss", "qwen3-vl", "qwen2.5"})

#: Human-readable display name each "text chain" policy family must appear as
#: verbatim in the README's "Models & cost" prose (issue #294: prose drifted
#: from config — "Gemma 3 27B" vs the real ``google.gemma-4-31B-it``).
#: Re-pointed at ``CAPABILITY_POLICY`` (spec 026 slice 7): the registry no
#: longer names models at all (US5), so this can no longer diff against
#: ``agents/registry.yaml``.
_POLICY_DISPLAY_NAMES = {
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


def test_model_fallback_chains_are_free():
    # The capability policy attributes competence to exactly one PAID family —
    # the sanctioned guarded fallback ``claude-haiku-4-5`` — and every other
    # attributed family is free (Constitution IV free-first). This is the
    # policy-layer analogue of the retired ``MODEL_FALLBACKS``-vs-
    # ``KNOWN_FREE_MODELS`` check.
    families = set(CAPABILITY_POLICY.entries)
    unexpected = families - _KNOWN_FREE_POLICY_FAMILIES - {_SANCTIONED_PAID_FAMILY}
    assert not unexpected, (
        f"CAPABILITY_POLICY attributes competence to unclassified family/families "
        f"{sorted(unexpected)} — classify as free (add to "
        f"_KNOWN_FREE_POLICY_FAMILIES) or as a NEW sanctioned paid fallback with "
        f"written justification (Constitution IV)"
    )
    assert families == _KNOWN_FREE_POLICY_FAMILIES | {_SANCTIONED_PAID_FAMILY}


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
    start = readme.index("## Models & cost")
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
            f"README 'Models & cost' section must name {display!r} (policy family "
            f"{family!r}) verbatim so prose cannot drift from the capability policy "
            f"(issue #294: 'Gemma 3 27B' vs google.gemma-4-31B-it)"
        )
    assert "Gemma 3" not in section, "README still names the retired gemma-3 family"
