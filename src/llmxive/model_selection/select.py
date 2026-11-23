"""Pure deterministic selector (spec 026, slice 2, US2 / FR-006 / FR-008 / FR-009).

``select(requirement, snapshot)`` is a PURE function of
``(requirement, runtime_snapshot, selection_policy_version)``: no network, no
environment, no clock. Given the same inputs it returns a **byte-identical**
``ModelChain`` (SC-001). It never re-ranks at execution time — ``execute`` walks
the chain this function produced.

Pipeline:

1. **Eligibility** (a candidate must pass ALL): snapshot freshness for its
   component (a ``last_known_good`` older than ``max_catalog_age_s`` is excluded;
   an ``unavailable`` component contributes no models); capability + features
   attributed by the versioned :class:`CapabilityPolicy` (unknown-to-policy →
   ineligible — the catalog proves presence, NOT competence, FR-006);
   ``min_context_tokens``; the unconditional ``exclude_*`` prohibitions; the
   REQUIRED independence dimensions (differ from the ``independence_against``
   baseline or be excluded — FR-009); and the paid guard (free always ok; unknown
   price NEVER free → excluded; a priced-paid model only if ``allow_paid`` AND the
   credit component is fresh+live AND opt-in AND
   ``worst_case_credits <= effective_per_call_cap``).
2. **Ordering** by the fixed tie-breaks (FR-008): free-before-paid → preferred
   quality tier → preferred independence → (health: inactive in v1) → estimated
   cost → stable canonical model id. Required capabilities/independence are
   eligibility GATES (already applied), so the survivors are ordered by the
   remaining rungs.
3. Truncate to ``max_candidates`` and assemble the ``ModelChain`` (``resolved_at =
   snapshot.observed_at`` — never a clock call). Empty survivor set →
   ``ModelUnavailable`` (fail closed, Constitution V).
"""

from __future__ import annotations

from llmxive.model_selection.policy import CAPABILITY_POLICY, CapabilityPolicy
from llmxive.model_selection.types import (
    FUNDED_BACKENDS,
    Candidate,
    IndependenceDim,
    ModelChain,
    ModelRef,
    ModelRequirement,
    ModelUnavailable,
    RuntimeSnapshot,
    worst_case_credits,
)

_LOCAL_BACKEND = "local"


def _component_of(model: ModelRef) -> str:
    """Which snapshot component a model's provenance/freshness comes from."""
    return "local" if model.backend == _LOCAL_BACKEND else "catalog"


def _differs_from_baseline(model: ModelRef, dim: IndependenceDim, req: ModelRequirement) -> bool:
    """True iff ``model`` DIFFERS from the ``independence_against`` baseline on
    ``dim`` (i.e. independence is satisfied for that dimension)."""
    base = req.independence_against
    if dim == "model":
        return model.model_id not in base.models
    if dim == "family":
        return model.model_family not in base.families
    if dim == "vendor":
        return model.vendor not in base.vendors
    if dim == "serving_endpoint":
        return model.serving_endpoint not in base.endpoints
    return True  # unknown dim: not a constraint we can enforce → treat as satisfied


def _excluded(model: ModelRef, req: ModelRequirement) -> bool:
    """Unconditional ``exclude_*`` prohibitions (independent of the baseline)."""
    return (
        model.model_id in req.exclude_models
        or model.model_family in req.exclude_families
        or model.vendor in req.exclude_vendors
        or model.serving_endpoint in req.exclude_endpoints
    )


def _effective_per_call_cap(req: ModelRequirement, available_headroom: float) -> float:
    """The per-call credit ceiling a paid candidate must fit under (FR-003):
    ``available_headroom`` when ``max_credits`` is None, else the tighter of the
    two."""
    if req.max_credits is None:
        return available_headroom
    return min(float(req.max_credits), available_headroom)


#: Components a fresh-required (judgment) review must observe fresh-enough (FR-007):
#: the catalog (model presence/pricing) AND the credit/opt-in observation. The local
#: fallback inventory is NOT gated (FR-007 names catalog + credit/opt-in only).
_FRESH_REQUIRED_COMPONENTS = ("catalog", "credit")


def _enforce_fresh_snapshot(requirement: ModelRequirement, snapshot: RuntimeSnapshot) -> None:
    """For a ``require_fresh_snapshot`` (spec-025 judgment) review, FAIL CLOSED
    (``ModelUnavailable``) if the catalog OR the credit/opt-in component is
    unavailable or older than ``max_catalog_age_s`` — the freshness limit applies to
    BOTH components (FR-007), independent of whether the chosen model is free."""
    for comp in _FRESH_REQUIRED_COMPONENTS:
        prov = snapshot.sources.get(comp)
        if prov is None or prov.source == "unavailable":
            src = prov.source if prov is not None else "missing"
            raise ModelUnavailable(
                f"fresh-required review: {comp!r} component is unavailable (source={src!r}) — "
                "a judgment review cannot rest on a stale/absent snapshot (FR-007)"
            )
        if prov.source == "last_known_good" and prov.age_s > requirement.max_catalog_age_s:
            raise ModelUnavailable(
                f"fresh-required review: {comp!r} component is stale (age {prov.age_s:.0f}s > "
                f"max_catalog_age_s {requirement.max_catalog_age_s}s) — FR-007 requires a "
                "fresh-enough catalog AND credit/opt-in observation"
            )


def select(
    requirement: ModelRequirement,
    snapshot: RuntimeSnapshot,
    *,
    policy: CapabilityPolicy | None = None,
) -> ModelChain:
    """Choose an ordered ``ModelChain`` for ``requirement`` against ``snapshot``.

    Pure and deterministic (SC-001). ``policy`` is injectable for tests; the
    production default is the canonical :data:`CAPABILITY_POLICY`. Raises
    :class:`ModelUnavailable` when no candidate satisfies the requirement.
    """
    pol = policy if policy is not None else CAPABILITY_POLICY

    # FR-007: a judgment review fails closed on a stale/unavailable catalog OR
    # credit/opt-in component BEFORE any per-model work (even for a free result).
    if requirement.require_fresh_snapshot:
        _enforce_fresh_snapshot(requirement, snapshot)

    credit = snapshot.credit
    cap = _effective_per_call_cap(requirement, credit.available_headroom)
    # Paid admission requires a LIVE, opted-in credit observation (FR-007 / C6):
    # a stale (last_known_good/unavailable) or opt-out credit state fails closed
    # for paid — free candidates are unaffected.
    paid_admissible = requirement.allow_paid and credit.source == "live" and credit.paid_opt_in

    explanation: list[str] = []
    eligible: list[tuple[ModelRef, float, bool]] = []  # (ref, worst_case_credits, is_free)

    for model in snapshot.models:
        family = model.model_family

        # Funded (Hugging Face) models are admitted only by the funded selection
        # path (spec 027 section 5.10: leaderboard strength levels + the allowance
        # guard), never by the free/paid family-table walk below, which would
        # price them against the Dartmouth credit guard.
        if model.backend in FUNDED_BACKENDS:
            continue

        # (a) snapshot freshness for this model's component.
        prov = snapshot.sources.get(_component_of(model))
        if prov is None or prov.source == "unavailable":
            continue
        if prov.source == "last_known_good" and prov.age_s > requirement.max_catalog_age_s:
            continue

        # (b) capability + features attributed by the versioned policy.
        entry = pol.entry(family)
        if entry is None:
            continue
        if requirement.capability not in entry.capabilities:
            continue
        if not (requirement.required_features <= entry.features):
            continue

        # (c) minimum context window.
        if requirement.min_context_tokens is not None:
            if entry.max_context_tokens < requirement.min_context_tokens:
                continue

        # (d) unconditional prohibitions.
        if _excluded(model, requirement):
            continue

        # (e) REQUIRED independence (fail closed per-candidate; FR-009).
        if any(
            not _differs_from_baseline(model, dim, requirement)
            for dim in requirement.required_independence
        ):
            continue

        # (f) paid guard. Free always ok; unknown price never free → excluded; a
        # priced-paid model only under a live+opted-in guard within the ceiling.
        pricing = snapshot.pricing.get(model.model_id)
        if pricing is None or not pricing.is_known:
            continue  # no priced cost → cannot admit (unknown is never free)
        is_free = pricing.is_free
        if requirement.require_paid and is_free:
            continue  # require_paid rung: exclude every free candidate (spec 026 slice 6)
        cost = worst_case_credits(pricing, requirement.call_budget)
        if cost is None:
            continue
        if not is_free:
            if not paid_admissible or cost > cap:
                continue

        eligible.append((model, cost, is_free))

    if not eligible:
        raise ModelUnavailable(_no_candidate_reason(requirement, snapshot, pol))

    # Ordering (FR-008). Required capabilities/independence are eligibility gates
    # (already applied), so survivors sort by the remaining rungs. All keys
    # ascending; lower sorts earlier (= preferred).
    pref_dims = tuple(requirement.preferred_independence)

    def sort_key(item: tuple[ModelRef, float, bool]) -> tuple:
        model, cost, is_free = item
        free_rank = 0 if is_free else 1  # rung 3: free before paid
        quality = -pol.quality_tier(model.model_family)  # rung 4: higher tier first
        unmet_pref = sum(  # rung 5: fewer unmet preferred-independence dims first
            0 if _differs_from_baseline(model, dim, requirement) else 1 for dim in pref_dims
        )
        # rung 6 (health) inactive in v1. rung 7: estimated cost. rung 8: model id.
        return (free_rank, quality, unmet_pref, cost, model.model_id)

    eligible.sort(key=sort_key)

    # Record any preferred-independence dimension that NO survivor satisfies
    # (degraded toward the baseline — FR-009 scenario 3).
    for dim in sorted(pref_dims):
        if all(not _differs_from_baseline(m, dim, requirement) for m, _, _ in eligible):
            explanation.append(
                f"preferred_independence '{dim}' unmet: no candidate differs from the baseline"
            )
    if requirement.allow_paid and not paid_admissible:
        explanation.append(
            f"paid not admitted (allow_paid=True, credit.source={credit.source!r}, "
            f"paid_opt_in={credit.paid_opt_in}) — free candidates only"
        )

    chosen = eligible[: requirement.max_candidates]
    candidates = tuple(
        Candidate(
            model_ref=model,
            pricing=snapshot.pricing[model.model_id],
            worst_case_credits=cost,
            approved_ceiling_credits=(0.0 if is_free else cap),
        )
        for model, cost, is_free in chosen
    )
    return ModelChain(
        candidates=candidates,
        resolved_at=snapshot.observed_at,
        call_budget=requirement.call_budget,
        snapshot_digest=snapshot.digest,
        snapshot_provenance=dict(snapshot.sources),
        selection_policy_version=pol.version,
        explanation=tuple(explanation),
    )


def _no_candidate_reason(
    requirement: ModelRequirement, snapshot: RuntimeSnapshot, policy: CapabilityPolicy
) -> str:
    """A human-readable reason for the ``ModelUnavailable`` (fail-fast clarity)."""
    n = len(snapshot.models)
    catalog = snapshot.sources.get("catalog")
    src = catalog.source if catalog is not None else "missing"
    return (
        f"no model satisfies capability={requirement.capability!r} "
        f"(required_features={set(requirement.required_features) or '∅'}, "
        f"allow_paid={requirement.allow_paid}, "
        f"required_independence={set(requirement.required_independence) or '∅'}, "
        f"require_paid={requirement.require_paid}) "
        f"against {n} snapshot model(s); catalog source={src!r}, "
        f"policy_version={policy.version}"
    )
