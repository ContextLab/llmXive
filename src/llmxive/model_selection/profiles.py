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

from llmxive.model_selection.types import (
    CallBudget,
    Capability,
    IndependenceBaseline,
    IndependenceDim,
    ModelRequirement,
)

__all__ = ["PROFILES", "RequirementProfile", "build_requirement", "profile"]


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
        )
        return replace(req, **overrides) if overrides else req


#: The canonical profile presets (single source of truth for call-site intent).
PROFILES: dict[str, RequirementProfile] = {
    "cheap_structured": RequirementProfile(
        name="cheap_structured",
        capability="cheap",
    ),
    "standard_generation": RequirementProfile(
        name="standard_generation",
        capability="standard",
    ),
    "deep_review": RequirementProfile(
        name="deep_review",
        capability="deep",
    ),
    "deep_code": RequirementProfile(
        name="deep_code",
        capability="deep",
    ),
    "vision": RequirementProfile(
        name="vision",
        capability="vision",
    ),
    "independent_review": RequirementProfile(
        name="independent_review",
        capability="deep",
        required_independence=frozenset({"family"}),
        preferred_independence=frozenset({"serving_endpoint"}),
        max_catalog_age_s=900,  # high-stakes: require a fresh-enough snapshot (FR-007)
    ),
}


def profile(name: str) -> RequirementProfile:
    """Look up a canonical profile by name (raises ``KeyError`` if unknown)."""
    return PROFILES[name]


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
