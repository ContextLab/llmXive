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
   When the snapshot holds a Hugging Face model, a blocked funded component is
   recorded in the chain's ``explanation``.

   A ``require_fresh_snapshot`` (judgment) review judges each remote class:
   Dartmouth needs ``catalog`` + ``credit`` within ``max_catalog_age_s``; funded
   needs ``hf_catalog`` within ``max_catalog_age_s``, the ``leaderboard`` within
   its OWN limits (``LEADERBOARD_MAX_FETCH_AGE_S`` and the publish age, as for
   every call) and a live guard. It is an outage only when NEITHER class is
   fresh; otherwise the stale class contributes no candidates (local is never
   gated; spec 027 5.9.3).
2. **Funded group** (:func:`_funded_group`, spec 027 5.10): only funded
   candidates whose repo qualifies for the requirement's strength level on its
   track AND whose worst case fits the funded guard's headroom and
   ``max_credits`` (zero headroom admits nothing). The cheapest qualifier leads
   (ties: higher rating, then model id); the rest are the next-cheapest from
   other families, at most ``max_chain_slots``. Under budget pressure a profile
   with ``budget_step_down`` steps down ONE level (recorded in ``explanation``,
   naming the bound that failed: allowance headroom or ``max_credits``);
   otherwise the funded class is an outage. When the ALLOWANCE emptied it,
   paid candidates are dropped too unless ``require_paid`` (Constitution IV);
   when only the caller's ``max_credits`` did, paid stays (that bound already
   applies to paid).
3. **Ordering**: the cost class first — free remote → funded group (its own
   order) → free local → paid — then, within the non-funded classes, the fixed
   tie-breaks (FR-008): preferred quality tier → preferred independence →
   (health: inactive in v1) → estimated cost → stable canonical model id.
   Required capabilities/independence are eligibility GATES (already applied),
   so the survivors are ordered by the remaining rungs.
4. Truncate to ``max_candidates`` and assemble the ``ModelChain`` (``resolved_at =
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
    level_qualifiers,
    publish_date_fresh,
    publish_date_invalid,
    repo_of,
    track_population,
)
from llmxive.model_selection.types import (
    FUNDED_BACKENDS,
    STRENGTH_LEVELS,
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

#: Cost classes, the first ordering key (spec 027 5.9.1 / 5.10): free remote
#: (Dartmouth) → funded (Hugging Face) → free local (the last free resort) → paid.
_CLASS_FREE_REMOTE, _CLASS_FUNDED, _CLASS_LOCAL, _CLASS_PAID = 0, 1, 2, 3

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
    candidates may be considered one by one (spec 027 5.10, fail closed): the
    requirement must name a track and a strength level, and the funded components
    must pass :func:`_funded_components_reason`."""
    if requirement.track is None or requirement.strength is None:
        return "the requirement names no track and strength level"
    return _funded_components_reason(snapshot, requirement.max_catalog_age_s, funded_policy)


def _funded_components_reason(
    snapshot: RuntimeSnapshot, max_catalog_age_s: float, funded_policy: FundedPolicy
) -> str | None:
    """Why the funded components cannot be relied on, or ``None`` if they can.
    The ONE freshness rule for the funded class, used by every call and by a
    fresh-required review alike.

    The Hugging Face catalog is judged by ``max_catalog_age_s`` (the requirement's
    limit, tight for a review); the leaderboard ALWAYS by its own limits: fetched
    within :data:`LEADERBOARD_MAX_FETCH_AGE_S` and its newest publish date fresh by
    the shared rule in :func:`~llmxive.model_selection.strength.publish_date_fresh`
    (at most ``max_publish_age_days`` old; more than one day in the future is
    invalid). The snapshot reuses a leaderboard copy for hours with its true age,
    so a review's tight catalog limit must not judge it. The funded guard must be
    present and ``live``.
    """
    reason = _stale_or_unavailable(snapshot, "hf_catalog", max_catalog_age_s)
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


def _funded_group(
    eligible: list[tuple[ModelRef, float]],
    requirement: ModelRequirement,
    snapshot: RuntimeSnapshot,
    population: Mapping[str, ArenaScore],
    funded_policy: FundedPolicy,
) -> tuple[list[tuple[ModelRef, float]], list[str], bool]:
    """The funded slots of the chain (spec 027 5.10): ``(group, notes,
    allowance_removed)``.

    ``eligible`` are the funded ``(model, worst_case_credits)`` pairs that passed
    per-candidate eligibility. Only those whose repo qualifies for the
    requirement's strength level (:func:`level_qualifiers` over the WHOLE track
    population, not just the call's eligible models) AND whose worst case fits
    the budget — the funded guard's headroom, tightened by ``max_credits`` — may
    enter the group; a guard with no headroom admits nothing. The group is the
    cheapest fitting qualifier, then the next-cheapest from OTHER families
    (cost, then higher rating, then model id), at most ``max_chain_slots``.

    Budget pressure: when qualifiers exist at the level but none fits, a
    requirement with ``budget_step_down`` (and above ``economy``) steps down ONE
    level, recorded in ``notes``; otherwise — and when the lower level does not
    fit either — the group is empty. Every note names the bound that actually
    failed: the allowance headroom, or the caller's ``max_credits``.
    ``allowance_removed`` is True only when the ALLOWANCE is what emptied the
    group (the cheapest qualifier exceeds the headroom, or there is none): the
    caller treats that as an outage for the funded class that must not fall
    through to paid (Constitution IV). When only the caller's ``max_credits``
    emptied it, paid candidates stay — the same ``max_credits`` already bounds
    them."""
    assert requirement.track is not None and requirement.strength is not None
    guard = snapshot.funded
    assert guard is not None  # a funded candidate implies a live guard
    available = guard.available_usd * USD_TO_CREDITS
    cap = available if requirement.max_credits is None else min(available, float(requirement.max_credits))
    level = requirement.strength
    notes: list[str] = []

    def failed_bound(pick: float) -> tuple[bool, str]:
        """``(is_allowance, "<bound> (<pick> > <limit>)")`` for the cheapest pick."""
        if available <= 0 or pick > available:
            return True, f"the allowance headroom (${pick / USD_TO_CREDITS:.4f} > ${max(available, 0.0) / USD_TO_CREDITS:.4f})"
        assert requirement.max_credits is not None  # pick <= available, so max_credits bound it
        return False, (
            f"the caller's max_credits (${pick / USD_TO_CREDITS:.4f} > "
            f"${requirement.max_credits / USD_TO_CREDITS:.4f})"
        )

    while True:
        qualifiers = level_qualifiers(population, level, funded_policy)
        at_level = [(m, c) for m, c in eligible if repo_of(m.model_id) in qualifiers]
        fits = [(m, c) for m, c in at_level if available > 0 and c <= cap]
        notes.append(
            f"funded: {requirement.track}/{level} — {len(qualifiers)} of {len(population)} models qualify"
        )
        if fits or not at_level:
            break
        if not requirement.budget_step_down or level == "economy" or level != requirement.strength:
            break  # reviews/vision, economy, and an already-stepped level stop here
        lower = STRENGTH_LEVELS[STRENGTH_LEVELS.index(level) - 1]
        _, bound = failed_bound(min(c for _, c in at_level))
        notes.append(f"funded: {level} pick exceeds {bound} — stepped down to {lower} (budget pressure)")
        level = lower
    if at_level and not fits:
        is_allowance, bound = failed_bound(min(c for _, c in at_level))
        if is_allowance:
            notes.append(
                f"funded allowance exhausted: {level} pick exceeds {bound} — no step-down for this "
                "call; paid not reached (Constitution IV)"
            )
        else:
            notes.append(
                f"funded over the caller's budget: {level} pick exceeds {bound} — no step-down for "
                "this call; paid candidates stay bounded by the same max_credits"
            )
        return [], notes, is_allowance

    def rating(model: ModelRef) -> float:
        return population[repo_of(model.model_id)].rating

    group: list[tuple[ModelRef, float]] = []
    families: set[str] = set()
    for model, cost in sorted(fits, key=lambda mc: (mc[1], -rating(mc[0]), mc[0].model_id)):
        if model.model_family in families:
            continue
        group.append((model, cost))
        families.add(model.model_family)
        if len(group) == funded_policy.max_chain_slots:
            break
    return group, notes, False


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


#: Components a fresh-required (judgment) review must observe fresh-enough, per
#: candidate class (spec 026 FR-007 as amended by spec 027 5.9.3): the Dartmouth
#: catalog (presence/pricing) AND the credit/opt-in observation for Dartmouth
#: candidates (free and paid). The funded class is judged by
#: :func:`_funded_components_reason` (the Hugging Face catalog by
#: ``max_catalog_age_s``; the leaderboard by its own fetch-age and publish-date
#: limits; a ``live`` guard). The local fallback inventory is never gated.
_FRESH_REQUIRED_COMPONENTS = ("catalog", "credit")


def _fresh_classes(
    requirement: ModelRequirement, snapshot: RuntimeSnapshot, funded_policy: FundedPolicy
) -> tuple[str | None, str | None]:
    """For a ``require_fresh_snapshot`` (spec-025 judgment) review, why each
    remote candidate class is NOT fresh enough to serve it: ``(dartmouth_reason,
    funded_reason)``, ``None`` for a class that is fresh. The Dartmouth catalog and
    credit components are judged by ``max_catalog_age_s`` (an
    ``unavailable``/missing component, or a ``last_known_good`` copy older than
    that, is not fresh). The funded class is judged by
    :func:`_funded_components_reason`: its catalog by ``max_catalog_age_s``, the
    leaderboard by its OWN limits (:data:`LEADERBOARD_MAX_FETCH_AGE_S`, publish
    age), and a ``live`` guard.

    FAIL CLOSED (``ModelUnavailable``) only when NEITHER class is fresh (spec 027
    5.9.3); otherwise the caller drops the candidates of the class that is not."""
    age = requirement.max_catalog_age_s
    dartmouth: str | None = None
    for comp in _FRESH_REQUIRED_COMPONENTS:
        dartmouth = _stale_or_unavailable(snapshot, comp, age)
        if dartmouth is not None:
            break
    funded = _funded_components_reason(snapshot, age, funded_policy)
    if dartmouth is not None and funded is not None:
        raise ModelUnavailable(
            "fresh-required review: no candidate class is fresh enough "
            f"(max_catalog_age_s {age}s) — Dartmouth: {dartmouth}; funded: {funded}. "
            "A judgment review cannot rest on a stale/absent snapshot (FR-007, spec 027 5.9.3)"
        )
    return dartmouth, funded


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
    has_hf = any(m.backend in FUNDED_BACKENDS for m in snapshot.models)

    # FR-007 as amended by spec 027 5.9.3: a judgment review fails closed when NO
    # remote candidate class is fresh, BEFORE any per-model work; a class that is
    # not fresh contributes no candidates. The funded class's freshness is the
    # same rule every call applies (_funded_components_reason), so a stale funded
    # class surfaces below as ``funded_block``.
    dartmouth_stale: str | None = None
    if requirement.require_fresh_snapshot:
        dartmouth_stale, _ = _fresh_classes(requirement, snapshot, fpol)

    credit = snapshot.credit
    cap = _effective_per_call_cap(requirement, credit.available_headroom)
    # Paid admission requires a LIVE, opted-in credit observation (FR-007 / C6):
    # a stale (last_known_good/unavailable) or opt-out credit state fails closed
    # for paid — free candidates are unaffected.
    paid_admissible = requirement.allow_paid and credit.source == "live" and credit.paid_opt_in

    explanation: list[str] = []
    eligible: list[tuple[ModelRef, float, bool]] = []  # non-funded: (ref, worst_case_credits, is_free)
    funded_eligible: list[tuple[ModelRef, float]] = []  # (ref, worst_case_credits)
    funded_no_context: list[str] = []  # funded ids whose provider reports no context length
    funded_short_context: list[str] = []  # funded ids whose context cannot hold the call budget
    budget_tokens = requirement.call_budget.max_input_tokens + requirement.call_budget.max_output_tokens

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
    elif has_hf and requirement.track is not None and requirement.strength is not None:
        explanation.append(f"funded candidates not eligible: {funded_block}")
    if dartmouth_stale is not None:
        explanation.append(f"Dartmouth candidates not eligible: fresh-required review: {dartmouth_stale}")

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
            # (a) snapshot freshness for this model's component (and, for a
            # fresh-required review, its candidate class).
            if dartmouth_stale is not None and model.backend != _LOCAL_BACKEND:
                continue
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
        cost = worst_case_credits(pricing, requirement.call_budget)
        if cost is None:
            continue
        if is_funded:
            # The provider's reported context window must hold the whole call
            # budget (input bound + output bound): an over-long request is
            # rejected after the reservation and charged in full.
            context_length = snapshot.observed[model.model_id].context_length
            if context_length is None:
                funded_no_context.append(model.model_id)
                continue
            if context_length < budget_tokens:
                funded_short_context.append(model.model_id)
                continue
            # Never free whatever the price; the level filter, the allowance and
            # max_credits are applied by _funded_group below.
            funded_eligible.append((model, cost))
            continue
        is_free = pricing.is_free
        if requirement.require_paid and is_free:
            continue  # require_paid rung: exclude every free candidate (spec 026 slice 6)
        if not is_free:
            if not paid_admissible or cost > cap:
                continue

        eligible.append((model, cost, is_free))

    # The funded slots (spec 027 5.10): level qualification, cheapest-within-level,
    # allowance/budget fit, one budget step-down where the profile allows it. No
    # funded candidate reaches the chain except through this group.
    funded_group: list[tuple[ModelRef, float]] = []
    if funded_short_context:
        explanation.append(
            f"funded: skipped {len(funded_short_context)} provider(s) whose context length is "
            f"below the call budget's {budget_tokens} tokens: {', '.join(sorted(funded_short_context))}"
        )
    if funded_no_context:
        explanation.append(
            f"funded: skipped {len(funded_no_context)} provider(s) that report no context length: "
            f"{', '.join(sorted(funded_no_context))}"
        )
    if funded_block is None and has_hf:
        funded_group, notes, allowance_removed = _funded_group(
            funded_eligible, requirement, snapshot, population, fpol
        )
        explanation.extend(notes)
        if allowance_removed and not requirement.require_paid:
            # Exhausting the allowance is never a licence to fall through to paid
            # (Constitution IV); an explicit require_paid rung is still paid.
            eligible = [item for item in eligible if item[2]]

    if not eligible and not funded_group:
        raise ModelUnavailable(_no_candidate_reason(requirement, snapshot, pol, explanation))

    # Ordering (FR-008, spec 027 5.5/5.10). The first key is the cost class: free
    # remote → funded → free local → paid. Required capabilities/independence are
    # eligibility gates (already applied), so the non-funded survivors sort by the
    # remaining rungs; the funded group keeps its own order (cheapest qualifier
    # first). All keys ascending; lower sorts earlier (= preferred).
    pref_dims = tuple(requirement.preferred_independence)

    def class_rank(model: ModelRef, is_free: bool) -> int:
        if not is_free:
            return _CLASS_PAID
        return _CLASS_LOCAL if model.backend == _LOCAL_BACKEND else _CLASS_FREE_REMOTE

    def sort_key(item: tuple[ModelRef, float, bool]) -> tuple:
        model, cost, is_free = item
        quality = -pol.quality_tier(model.model_family)  # rung 4: higher tier first
        unmet_pref = sum(  # rung 5: fewer unmet preferred-independence dims first
            0 if _differs_from_baseline(model, dim, requirement) else 1 for dim in pref_dims
        )
        # rung 6 (health) inactive in v1. rung 7: estimated cost. rung 8: model id.
        return (class_rank(model, is_free), quality, unmet_pref, cost, model.model_id)

    eligible.sort(key=sort_key)
    ranked: list[tuple[ModelRef, float, bool]] = [
        item for item in eligible if class_rank(item[0], item[2]) < _CLASS_FUNDED
    ]
    ranked += [(model, cost, False) for model, cost in funded_group]
    ranked += [item for item in eligible if class_rank(item[0], item[2]) > _CLASS_FUNDED]

    # Record any preferred-independence dimension that NO survivor satisfies
    # (degraded toward the baseline — FR-009 scenario 3).
    for dim in sorted(pref_dims):
        if all(not _differs_from_baseline(m, dim, requirement) for m, _, _ in ranked):
            explanation.append(
                f"preferred_independence '{dim}' unmet: no candidate differs from the baseline"
            )
    if requirement.allow_paid and not paid_admissible:
        explanation.append(
            f"paid not admitted (allow_paid=True, credit.source={credit.source!r}, "
            f"paid_opt_in={credit.paid_opt_in}) — free candidates only"
        )

    chosen = ranked[: requirement.max_candidates]

    def ceiling(model: ModelRef, is_free: bool) -> float:
        if model.backend in FUNDED_BACKENDS:
            assert snapshot.funded is not None  # a funded survivor implies a live guard
            return _effective_per_call_cap(requirement, snapshot.funded.available_usd * USD_TO_CREDITS)
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
    explanation: list[str],
) -> str:
    """A human-readable reason for the ``ModelUnavailable`` (fail-fast clarity):
    the requirement, each component's source, and the decision record so far —
    why funded candidates were blocked, the funded level/population lines, any
    budget step-down and an exhausted allowance."""
    n = len(snapshot.models)

    def source(component: str) -> str:
        prov = snapshot.sources.get(component)
        return prov.source if prov is not None else "missing"

    record = "".join(f"; {line}" for line in explanation)
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
        f"policy_version={policy.version}{record}"
    )
