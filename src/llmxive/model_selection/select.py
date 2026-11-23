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

   A **funded** (Hugging Face) candidate replaces the freshness, family-table and
   paid-guard steps with the spec 027 5.10 rules, all fail closed: the
   ``hf_catalog`` component fresh by ``max_catalog_age_s``; the ``leaderboard``
   fetched within ``LEADERBOARD_MAX_FETCH_AGE_S`` with its newest publish date at
   most ``max_publish_age_days`` old and not more than one day in the future
   (``strength.publish_date_fresh``); a ``live`` funded guard; a requirement naming
   a track and strength level; the candidate's repo in that track's scored
   population; observed flags for vision / ``structured`` / ``tools`` / context
   (other features from the reviewed family entry); a known price; not a
   ``require_paid`` rung. ``allow_paid`` and the paid opt-in are not consulted.
   A blocked funded component is recorded in the chain's ``explanation``.
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

from collections.abc import Mapping

from llmxive.model_selection.policy import (
    CAPABILITY_POLICY,
    FUNDED_POLICY,
    LEADERBOARD_MAX_FETCH_AGE_S,
    CapabilityPolicy,
    FundedPolicy,
    PolicyEntry,
)
from llmxive.model_selection.strength import (
    MAX_FUTURE_PUBLISH_DAYS,
    publish_date_fresh,
    publish_date_invalid,
    repo_of,
    track_population,
)
from llmxive.model_selection.types import (
    FUNDED_BACKENDS,
    USD_TO_CREDITS,
    ArenaScore,
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

#: Features a Hugging Face provider reports itself (``ObservedModel.features``).
#: Any other required feature (e.g. ``reasoning``) is read from the reviewed
#: family entry instead; a model whose family has no entry cannot show it.
_OBSERVABLE_FEATURES = frozenset({"structured", "tools", "vision"})


def _component_of(model: ModelRef) -> str:
    """Which snapshot component a model's provenance/freshness comes from."""
    if model.backend == _LOCAL_BACKEND:
        return "local"
    if model.backend in FUNDED_BACKENDS:
        return "hf_catalog"
    return "catalog"


def _stale_or_unavailable(
    snapshot: RuntimeSnapshot, component: str, max_age_s: float
) -> str | None:
    """Why ``component`` cannot be relied on (missing, ``unavailable``, or a
    ``last_known_good`` copy older than ``max_age_s``), or ``None`` if it can."""
    prov = snapshot.sources.get(component)
    if prov is None or prov.source == "unavailable":
        src = prov.source if prov is not None else "missing"
        return f"{component} is unavailable (source={src!r})"
    if prov.source == "last_known_good" and prov.age_s > max_age_s:
        return f"{component} is stale (last_known_good, age {prov.age_s:.0f}s > {max_age_s:.0f}s)"
    return None


def _funded_block_reason(
    requirement: ModelRequirement, snapshot: RuntimeSnapshot, funded_policy: FundedPolicy
) -> str | None:
    """Why NO funded candidate may serve this call, or ``None`` if funded
    candidates may be considered one by one (spec 027 5.10, fail closed).

    The Hugging Face catalog is judged by ``max_catalog_age_s``; the leaderboard by
    its own limits: fetched within :data:`LEADERBOARD_MAX_FETCH_AGE_S` and its
    newest publish date fresh by the shared rule in
    :func:`~llmxive.model_selection.strength.publish_date_fresh` (at most
    ``max_publish_age_days`` old; more than one day in the future is invalid). The funded guard must
    be present and ``live``; the requirement must name a track and a strength level.
    """
    if requirement.track is None or requirement.strength is None:
        return "the requirement names no track and strength level"
    reason = _stale_or_unavailable(snapshot, "hf_catalog", requirement.max_catalog_age_s)
    if reason is None:
        reason = _stale_or_unavailable(snapshot, "leaderboard", LEADERBOARD_MAX_FETCH_AGE_S)
    if reason is not None:
        return reason
    dates = [
        score.publish_date
        for scores in snapshot.scores.values()
        for score in (scores.reasoning, scores.coding)
        if score is not None
    ]
    if not dates:
        return "leaderboard holds no score for any catalog model"
    newest = max(dates)
    today = snapshot.observed_at.date()
    if publish_date_invalid(newest, today=today):
        return (
            f"leaderboard is unavailable (newest publish date {newest.isoformat()} is more than "
            f"{MAX_FUTURE_PUBLISH_DAYS} day(s) after {today.isoformat()})"
        )
    if not publish_date_fresh(newest, today=today, max_publish_age_days=funded_policy.max_publish_age_days):
        return (
            f"leaderboard is stale (newest publish date {newest.isoformat()} is "
            f"{(today - newest).days} days old > {funded_policy.max_publish_age_days})"
        )
    guard = snapshot.funded
    if guard is None or guard.source != "live":
        src = guard.source if guard is not None else "missing"
        return f"funded guard is unavailable (source={src!r})"
    return None


def _funded_admits(
    model: ModelRef,
    requirement: ModelRequirement,
    snapshot: RuntimeSnapshot,
    entry: PolicyEntry | None,
    population: Mapping[str, ArenaScore],
) -> bool:
    """Per-candidate funded eligibility (the components were already judged by
    :func:`_funded_block_reason`): scored on the requirement's track with a fresh
    publish date, observed flags meet the capability, features and context, and
    the call is not a ``require_paid`` rung. ``allow_paid``, the paid opt-in and
    the reviewed table's ``capabilities``/``quality_tier`` are not consulted."""
    if requirement.require_paid or repo_of(model.model_id) not in population:
        return False
    observed = snapshot.observed.get(model.model_id)
    if observed is None:
        return False  # nothing observed about this provider → nothing can be shown
    if requirement.capability == "vision" and "vision" not in observed.features:
        return False
    for feature in requirement.required_features:
        if feature in _OBSERVABLE_FEATURES:
            if feature not in observed.features:
                return False
        elif entry is None or feature not in entry.features:
            return False
    if requirement.min_context_tokens is not None and (
        observed.context_length is None or observed.context_length < requirement.min_context_tokens
    ):
        return False
    return True


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
    funded_policy: FundedPolicy | None = None,
) -> ModelChain:
    """Choose an ordered ``ModelChain`` for ``requirement`` against ``snapshot``.

    Pure and deterministic (SC-001). ``policy`` / ``funded_policy`` are injectable
    for tests; the production defaults are :data:`CAPABILITY_POLICY` and
    :data:`FUNDED_POLICY`. Raises :class:`ModelUnavailable` when no candidate
    satisfies the requirement.
    """
    pol = policy if policy is not None else CAPABILITY_POLICY
    fpol = funded_policy if funded_policy is not None else FUNDED_POLICY

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

    # Funded (Hugging Face) candidates: the components that decide them are judged
    # ONCE, fail closed (spec 027 5.10); the track's scored population is the
    # day's leaderboard rows with a fresh publish date.
    funded_block = _funded_block_reason(requirement, snapshot, fpol)
    population: Mapping[str, ArenaScore] = {}
    if funded_block is None:
        assert requirement.track is not None  # checked by _funded_block_reason
        population = track_population(
            snapshot.scores,
            requirement.track,
            today=snapshot.observed_at.date(),
            max_publish_age_days=fpol.max_publish_age_days,
        )
    elif requirement.track is not None and requirement.strength is not None:
        explanation.append(f"funded candidates not eligible: {funded_block}")

    for model in snapshot.models:
        family = model.model_family
        is_funded = model.backend in FUNDED_BACKENDS

        if is_funded:
            # Funded eligibility replaces steps (a)-(c) and (f) for this backend.
            if funded_block is not None or not _funded_admits(
                model, requirement, snapshot, pol.entry(family), population
            ):
                continue
        else:
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
        if is_funded:
            # Never free whatever the price; the allowance and max_credits are
            # applied after ranking (spec 027 Task 14), not here.
            cost = worst_case_credits(pricing, requirement.call_budget)
            if cost is not None:
                eligible.append((model, cost, False))
            continue
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
        raise ModelUnavailable(_no_candidate_reason(requirement, snapshot, pol, funded_block))

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

    def ceiling(model: ModelRef, is_free: bool) -> float:
        if model.backend in FUNDED_BACKENDS:
            assert snapshot.funded is not None  # a funded survivor implies a live guard
            return snapshot.funded.available_usd * USD_TO_CREDITS
        return 0.0 if is_free else cap

    candidates = tuple(
        Candidate(
            model_ref=model,
            pricing=snapshot.pricing[model.model_id],
            worst_case_credits=cost,
            approved_ceiling_credits=ceiling(model, is_free),
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
    requirement: ModelRequirement,
    snapshot: RuntimeSnapshot,
    policy: CapabilityPolicy,
    funded_block: str | None,
) -> str:
    """A human-readable reason for the ``ModelUnavailable`` (fail-fast clarity):
    the requirement, each component's source, and why funded candidates were
    blocked (if they were)."""
    n = len(snapshot.models)

    def source(component: str) -> str:
        prov = snapshot.sources.get(component)
        return prov.source if prov is not None else "missing"

    funded = f"; funded candidates not eligible: {funded_block}" if funded_block else ""
    return (
        f"no model satisfies capability={requirement.capability!r} "
        f"(required_features={set(requirement.required_features) or '∅'}, "
        f"allow_paid={requirement.allow_paid}, "
        f"required_independence={set(requirement.required_independence) or '∅'}, "
        f"require_paid={requirement.require_paid}, "
        f"track={requirement.track!r}, strength={requirement.strength!r}) "
        f"against {n} snapshot model(s); catalog source={source('catalog')!r}, "
        f"hf_catalog source={source('hf_catalog')!r}, "
        f"leaderboard source={source('leaderboard')!r}, funded source={source('funded')!r}, "
        f"policy_version={policy.version}{funded}"
    )
