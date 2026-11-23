"""Named requirement profiles (spec 026, slice 2, FR-012).

Call sites express INTENT as a named profile, not a model string. A profile is a
frozen preset of every ``ModelRequirement`` field EXCEPT ``call_budget`` (which
depends on the actual messages and is built by ``tokens.call_budget_for`` just
before ``select``) and ``independence_against`` (supplied by the caller — e.g.
spec 025's convergence panel passes the prior reviewers). ``build`` merges a
preset with the per-call ``call_budget`` (+ optional overrides) into a concrete
``ModelRequirement``.

The six required profiles (FR-012): ``cheap_structured``,
``standard_generation``, ``deep_review``, ``deep_code``, ``vision``,
``independent_review``. ``independent_review`` is the spec-025 judgment-review
preset: family diversity REQUIRED (fail closed) + serving-endpoint diversity
PREFERRED (degrade + record), and a tighter ``max_catalog_age_s`` because a
high-stakes review must run on a fresh-enough snapshot (FR-007).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from llmxive.model_selection.policy import SELECTION_POLICY_VERSION
from llmxive.model_selection.types import (
    CallBudget,
    Capability,
    IndependenceBaseline,
    IndependenceDim,
    ModelRequirement,
    RequirementOverrides,
    canonical_overrides,
)

__all__ = [
    "PROFILES",
    "RequirementProfile",
    "build_requirement",
    "profile",
    "selection_identity",
]


@dataclass(frozen=True)
class RequirementProfile:
    """A named ``ModelRequirement`` preset (everything but ``call_budget`` and the
    caller-supplied ``independence_against`` baseline)."""

    name: str
    capability: Capability
    required_features: frozenset[str] = frozenset()
    min_context_tokens: int | None = None
    required_independence: frozenset[IndependenceDim] = frozenset()
    preferred_independence: frozenset[IndependenceDim] = frozenset()
    exclude_models: frozenset[str] = frozenset()
    exclude_families: frozenset[str] = frozenset()
    exclude_vendors: frozenset[str] = frozenset()
    exclude_endpoints: frozenset[str] = frozenset()
    allow_paid: bool = False
    max_credits: int | None = None
    max_catalog_age_s: int = 3600
    max_candidates: int = 4
    require_fresh_snapshot: bool = False

    def build(
        self,
        call_budget: CallBudget,
        *,
        independence_against: IndependenceBaseline | None = None,
        **overrides: object,
    ) -> ModelRequirement:
        """Concrete ``ModelRequirement`` for THIS call: the preset + the per-call
        ``call_budget`` + the caller's independence baseline (+ optional field
        overrides, e.g. ``allow_paid=True`` for an escalated tier)."""
        req = ModelRequirement(
            capability=self.capability,
            call_budget=call_budget,
            required_features=self.required_features,
            min_context_tokens=self.min_context_tokens,
            independence_against=independence_against or IndependenceBaseline(),
            required_independence=self.required_independence,
            preferred_independence=self.preferred_independence,
            exclude_models=self.exclude_models,
            exclude_families=self.exclude_families,
            exclude_vendors=self.exclude_vendors,
            exclude_endpoints=self.exclude_endpoints,
            allow_paid=self.allow_paid,
            max_credits=self.max_credits,
            max_catalog_age_s=self.max_catalog_age_s,
            max_candidates=self.max_candidates,
            require_fresh_snapshot=self.require_fresh_snapshot,
        )
        return replace(req, **overrides) if overrides else req


#: The canonical profile presets (single source of truth for call-site intent).
PROFILES: dict[str, RequirementProfile] = {
    "cheap_structured": RequirementProfile(
        name="cheap_structured",
        capability="cheap",
        # Slice 7 Task 10 (US5 AC1/AC4 test-hardening): against the composite
        # snapshot the "cheap" capability's eligible free set is already FOUR
        # (qwen3.5, gemma-4, gpt-oss, local qwen2.5 all attribute "cheap"), so
        # the default cap of 4 truncated the guarded claude-haiku paid tail
        # (free-before-paid, FR-008) — same shape as the standard_generation
        # finding above. Raised to 8 to match: EVERY caller routed through
        # standard_generation (cap 8) before this slice's per-profile
        # migration, so this preserves that as-built reachability rather than
        # narrowing it now that the profile is actually exercised.
        max_candidates=8,
    ),
    "standard_generation": RequirementProfile(
        name="standard_generation",
        capability="standard",
        # Review finding 2: the general-purpose profile the routing chokepoints use
        # must retain the WHOLE free chain PLUS the guarded paid tail. Against the
        # real COMPOSITE snapshot the eligible free set is already four
        # (qwen3.5 → gemma-4 → gpt-oss → local qwen2.5), so the default cap of 4
        # truncated the paid claude tail (free-before-paid, FR-008). Size the cap
        # above the free chain + the 1-model paid tail (with headroom for catalog
        # growth) so a guarded paid fallback is reachable when all free candidates
        # are down — behavior-preserving vs the legacy qwen→…→claude MODEL_FALLBACKS.
        max_candidates=8,
    ),
    "deep_review": RequirementProfile(
        name="deep_review",
        capability="deep",
        # Slice 7 Task 10: the "deep" eligible set (qwen3.5, gemma-4, gpt-oss,
        # claude-haiku) is exactly 4 today, so cap 4 does not currently truncate
        # it — but raised to 8 anyway for parity with standard_generation /
        # cheap_structured: pre-migration EVERY caller (deep review included)
        # routed through the same standard_generation-shaped chain (cap 8), so
        # this keeps deep_review from being a narrower surface than the
        # behavior it replaced as the policy/catalog grow.
        max_candidates=8,
    ),
    "deep_code": RequirementProfile(
        name="deep_code",
        capability="deep",
        # Same rationale as deep_review immediately above.
        max_candidates=8,
    ),
    "vision": RequirementProfile(
        name="vision",
        capability="vision",
        # Slice 7 Task 10: vision has no paid tail today (claude-haiku-4-5 is
        # not attributed "vision"), so cap 4 is not truncating anything yet —
        # raised to 8 purely for parity with the other profiles ahead of the
        # same catalog-growth headroom, since a caller-agnostic
        # standard_generation cap of 8 was the uniform as-built surface before
        # this slice's per-profile migration.
        max_candidates=8,
    ),
    "independent_review": RequirementProfile(
        name="independent_review",
        capability="deep",
        required_independence=frozenset({"family"}),
        preferred_independence=frozenset({"serving_endpoint"}),
        max_catalog_age_s=900,  # high-stakes: require a fresh-enough snapshot (FR-007)
        require_fresh_snapshot=True,  # gate catalog AND credit/opt-in freshness, fail closed
    ),
}


def profile(name: str) -> RequirementProfile:
    """Look up a canonical profile by name (raises ``KeyError`` if unknown)."""
    return PROFILES[name]


def selection_identity(name: str, overrides: RequirementOverrides | None = None) -> str:
    """A stable string naming WHAT a call asks the selector for: the profile,
    the capability-policy version, and the effective escalation constraints.

    This is the profile-era replacement for "the requested model id" wherever a
    receipt, cache key or retry counter must be bound to the selection a verdict
    was produced under (task-verifier receipts, paper review receipts, the
    task-analysis policy fingerprint). It changes exactly when a deliberate,
    reviewed input to selection changes — a different profile, a
    ``SELECTION_POLICY_VERSION`` bump, or a tier escalation's overrides — so such
    a change invalidates the stored decision instead of silently reusing it. It
    deliberately does NOT bind the live runtime snapshot (catalog flaps are not a
    reviewed decision), matching the convergence review cache's key.
    """
    return (
        f"profile={name}|policy={SELECTION_POLICY_VERSION}|{canonical_overrides(overrides)}"
    )


def build_requirement(
    name: str,
    call_budget: CallBudget,
    *,
    independence_against: IndependenceBaseline | None = None,
    **overrides: object,
) -> ModelRequirement:
    """Convenience: ``PROFILES[name].build(call_budget, ...)``."""
    return PROFILES[name].build(
        call_budget, independence_against=independence_against, **overrides
    )
