"""Immutable typed contracts for requirement-driven model selection (spec 026).

Units are explicit: catalog pricing is **USD per token**; credits are the
Dartmouth daily-budget unit (1 credit = $0.001). Cost comparisons happen in
credits (see ``worst_case_credits``).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from datetime import date, datetime
from math import isfinite
from types import MappingProxyType
from typing import Literal

Capability = Literal["cheap", "standard", "deep", "vision"]
IndependenceDim = Literal["model", "family", "vendor", "serving_endpoint"]
SnapshotSource = Literal["live", "last_known_good", "unavailable"]
CostClass = Literal["free", "funded", "paid"]
Track = Literal["reasoning", "coding"]
StrengthLevel = Literal["economy", "balanced", "strong", "strongest"]

STRENGTH_LEVELS: tuple[StrengthLevel, ...] = ("economy", "balanced", "strong", "strongest")
#: Backends whose spend is drawn from a funded USD budget (never "free", whatever the price).
FUNDED_BACKENDS: frozenset[str] = frozenset({"huggingface"})

#: USD → credits conversion (1 credit == $0.001), so credits = usd * 1000.
USD_TO_CREDITS = 1000.0


class ModelUnavailable(Exception):
    """No model satisfies a :class:`ModelRequirement` against the snapshot.

    Raised by ``select`` (Fail Fast, Constitution V): required independence that
    cannot be met, a paid-only requirement with no headroom, a fresh-required
    call against a stale/unavailable snapshot, or an empty eligible set.
    """


@dataclass(frozen=True)
class ModelRef:
    """Canonical model identity. ``vendor`` (who made the model) and
    ``serving_endpoint``/``backend`` (who serves it) are SEPARATE dimensions:
    e.g. ``openai.gpt-oss-120b`` is an ``openai``-vendor model served through the
    ``dartmouth`` backend.
    """

    backend: str
    serving_endpoint: str
    model_id: str
    model_family: str
    vendor: str


@dataclass(frozen=True)
class ModelPricing:
    """Per-model USD-per-token rates. ``None`` means UNKNOWN (never free)."""

    input_usd_per_token: float | None
    output_usd_per_token: float | None

    @property
    def is_free(self) -> bool:
        return self.input_usd_per_token == 0.0 and self.output_usd_per_token == 0.0

    @property
    def is_known(self) -> bool:
        return self.input_usd_per_token is not None and self.output_usd_per_token is not None


@dataclass(frozen=True)
class SnapshotProvenance:
    """Per-component acquisition provenance: which source the data came from,
    WHEN it was actually observed, and how stale it is relative to the snapshot.

    FR-004/FR-007 require every decision to record BOTH the source AND the age of
    each component (catalog / local / credit-guard), so the pure selector can
    enforce ``max_catalog_age_s`` for high-stakes calls without touching a clock.

    - ``live``: freshly fetched → ``observed_at`` is the snapshot's ``observed_at``
      and ``age_s == 0.0``.
    - ``last_known_good``: served from the LKG store after a fetch failure →
      ``observed_at`` is the ORIGINAL observation time and ``age_s`` its true age.
    - ``unavailable``: no live fetch and no LKG (cold start) → there is no data,
      so ``age_s`` is meaningless; ``source`` is authoritative and MUST be checked
      first (the selector fails closed on ``unavailable`` before reading age).
    """

    source: SnapshotSource
    observed_at: datetime
    age_s: float


@dataclass(frozen=True)
class CreditGuardSnapshot:
    """The credit guard's REAL cap at observation time (mirrors ``credits.py``).

    ``effective_cap = budget_fraction * max_budget`` and
    ``available_headroom = max(0, effective_cap - spend)`` — so selection never
    admits a paid call past the fraction threshold (default 0.75), not merely
    ``balance - spend``.
    """

    balance: float
    spend: float
    max_budget: float
    paid_opt_in: bool
    budget_fraction: float
    effective_cap: float
    available_headroom: float
    budget_reset_at: str
    observed_at: datetime
    source: SnapshotSource


@dataclass(frozen=True)
class CallBudget:
    """The token envelope a call is priced against (given to ``select`` so it can
    bound cost WITHOUT ``ExecutionOptions``)."""

    max_input_tokens: int
    max_output_tokens: int


@dataclass(frozen=True)
class ExecutionOptions:
    """Runtime call controls, applied uniformly to every candidate in a chain.
    ``max_tokens`` MUST be a concrete int and ``<= call_budget.max_output_tokens``
    (enforced by ``execute``). ``temperature`` is ``float | None``: ``None`` means
    "backend default" (sampling ON) — the router omits the kwarg — so a generative
    caller (brainstorm/implementer) that leaves it unset is NOT silently forced to
    the deterministic ``0.0`` a reviewer pins."""

    max_tokens: int
    temperature: float | None = 0.0
    deadline_s: float | None = None


@dataclass(frozen=True)
class IndependenceBaseline:
    """The prior reviewers to differ from (multi-reviewer capable). Used with
    ``required_independence`` (fail closed) / ``preferred_independence`` (degrade
    + record). Distinct from the unconditional ``exclude_*`` prohibitions."""

    models: frozenset[str] = frozenset()
    families: frozenset[str] = frozenset()
    vendors: frozenset[str] = frozenset()
    endpoints: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ModelRequirement:
    """A call's intent — the pure selector's input alongside a snapshot."""

    capability: Capability
    call_budget: CallBudget
    required_features: frozenset[str] = frozenset()
    min_context_tokens: int | None = None
    independence_against: IndependenceBaseline = field(default_factory=IndependenceBaseline)
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
    #: Cost-class escalation (spec 026 slice 6): when True, EVERY free candidate is
    #: excluded so a paid escalation rung genuinely reaches the paid model despite the
    #: free-before-paid tie-break. Only meaningful with allow_paid=True; the combination
    #: require_paid=True + allow_paid=False admits no candidate and fails closed
    #: (ModelUnavailable) — it is never silently reinterpreted.
    require_paid: bool = False
    #: High-stakes (spec-025 judgment) reviews set this True so ``max_catalog_age_s``
    #: gates BOTH the catalog AND the credit/opt-in components (FR-007) — a stale or
    #: unavailable credit observation fails the WHOLE selection closed
    #: (``ModelUnavailable``), even when the resulting model is free. Ordinary
    #: low-risk calls leave it False (they may proceed on a bounded LKG snapshot and
    #: never consult credit freshness unless admitting paid).
    require_fresh_snapshot: bool = False
    #: Funded-provider selection (spec 027 5.10). A requirement with ``track`` or
    #: ``strength`` None gets no funded candidate.
    profile: str | None = None
    track: Track | None = None
    strength: StrengthLevel | None = None
    budget_step_down: bool = False


@dataclass(frozen=True)
class RequirementOverrides:
    """Escalation constraints applied ON TOP of a base profile's requirement
    (spec 026 slice 6). Frozen/typed so the large call graph carries an immutable
    value (safe across the panel ThreadPoolExecutor) with a fixed, validated field
    set — never an arbitrary mapping. Merge semantics (in route_chat): allow_paid is
    explicit tier authority; require_paid ORs; exclude_models unions; max_credits
    tightens. ``allow_paid=None`` means 'defer to the standalone param / snapshot'."""

    allow_paid: bool | None = None
    require_paid: bool = False
    exclude_models: frozenset[str] = frozenset()
    max_credits: int | None = None
    #: Routing-only escalation constraint (spec 026 slice 7): drop whatever
    #: ``select`` ranks FIRST, so the "free second opinion" rung needs no model
    #: id. Applied by ``route_chat`` as a two-pass translation (pass 1 resolves
    #: the leader, pass 2 excludes it), NOT inside ``select`` — ``select``
    #: receives a ``ModelRequirement`` and stays pure.
    exclude_leader: bool = False
    #: The same routing-only constraint, COUNTED: drop the top N ranked candidates
    #: (each pass excludes the leader of what remains), so a deeper free rung can
    #: reach the policy's third-best model without naming it. ``0`` (default) adds
    #: nothing; the effective count is ``max(int(exclude_leader), exclude_leaders)``,
    #: so ``exclude_leader=True`` keeps meaning exactly one.
    exclude_leaders: int = 0
    #: Shift the requirement's strength level by this many steps (any sign;
    #: clamped by ``shift_level``). Part of the selection identity.
    level_delta: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.level_delta, bool) or not isinstance(self.level_delta, int):
            raise TypeError("level_delta must be an int")
        if isinstance(self.exclude_leaders, bool) or not isinstance(self.exclude_leaders, int):
            raise TypeError("exclude_leaders must be an int")
        if self.exclude_leaders < 0:
            raise ValueError("exclude_leaders must be >= 0")


def canonical_overrides(overrides: RequirementOverrides | None) -> str:
    """Canonicalize the EFFECTIVE ``RequirementOverrides`` into a stable string.

    ``overrides=None`` (no override object at all) and an all-default
    ``RequirementOverrides()`` are semantically IDENTICAL to ``route_chat``
    (both mean "no escalation constraints" — see ``model_selection.route``);
    normalizing ``None`` to a fresh default instance up front makes them
    canonicalize to the SAME string, so a no-override run never spuriously
    MISSES a no-override cache entry.

    Fields are read via :func:`dataclasses.fields` rather than a hand-written
    tuple of attribute names, so a future field added to
    ``RequirementOverrides`` is picked up HERE automatically instead of being
    silently dropped from a cache key or receipt — a hand-written list would
    keep compiling and hashing happily while a new escalation constraint
    quietly stopped busting the cache. ``frozenset`` fields
    (``exclude_models``) are sorted first since set iteration order is not
    stable/meaningful.

    The single canonical form shared by the convergence review cache and by
    :func:`llmxive.model_selection.profiles.selection_identity` (Constitution I).
    """
    effective = overrides if overrides is not None else RequirementOverrides()
    parts: list[str] = []
    for f in fields(effective):
        value = getattr(effective, f.name)
        if isinstance(value, frozenset):
            value = tuple(sorted(value))
        parts.append(f"{f.name}={value!r}")
    return "|".join(parts)


@dataclass(frozen=True)
class ArenaScore:
    """One leaderboard rating with its confidence bounds."""

    rating: float
    rating_lower: float
    rating_upper: float
    publish_date: date

    def __post_init__(self) -> None:
        vals = (self.rating, self.rating_lower, self.rating_upper)
        if not all(isfinite(v) for v in vals):
            raise ValueError("ArenaScore values must be finite")
        if not self.rating_lower <= self.rating <= self.rating_upper:
            raise ValueError("ArenaScore requires rating_lower <= rating <= rating_upper")


@dataclass(frozen=True)
class ModelScores:
    reasoning: ArenaScore | None = None
    coding: ArenaScore | None = None

    def for_track(self, track: Track) -> ArenaScore | None:
        return self.reasoning if track == "reasoning" else self.coding


@dataclass(frozen=True)
class ObservedModel:
    """Provider-observed facts; ``features`` is a subset of structured/tools/vision."""

    context_length: int | None
    features: frozenset[str]


@dataclass(frozen=True)
class FundedGuardSnapshot:
    """Funded-spend guard state, in USD."""

    monthly_usd: float
    spent_month_usd: float
    spent_before_today_usd: float
    outstanding_usd: float
    org_balance_usd: float | None
    effective_cap_usd: float
    available_usd: float
    epoch: str
    observed_at: datetime
    source: SnapshotSource


@dataclass(frozen=True)
class RuntimeSnapshot:
    """Composite over EVERY configured backend + the credit-guard state. The
    pure selector's world: ``select`` reads nothing else (no network, no env).
    """

    models: tuple[ModelRef, ...]
    pricing: dict[str, ModelPricing]  # keyed by model_id
    # ADVISORY only (v1): a freshly-assembled snapshot cannot observe per-backend-
    # instance breaker state, so ``select`` does NOT rank on health (the tie-break
    # health rung is inactive; ``execute`` consults live breakers as it walks the
    # chain). Kept because the approved spec includes it; a shared observable
    # health registry would later make this authoritative and re-activate the rung.
    health: dict[str, str]  # model_id -> health hint ("ok" | "breaker_open" | ...)
    credit: CreditGuardSnapshot
    observed_at: datetime
    sources: dict[str, SnapshotProvenance]  # component ("catalog"/"local"/"credit") -> provenance
    digest: str = ""
    funded: FundedGuardSnapshot | None = None
    scores: Mapping[str, ModelScores] = field(default_factory=dict)  # keyed by model_id
    observed: Mapping[str, ObservedModel] = field(default_factory=dict)  # keyed by model_id

    def __post_init__(self) -> None:
        object.__setattr__(self, "scores", MappingProxyType(dict(self.scores)))
        object.__setattr__(self, "observed", MappingProxyType(dict(self.observed)))
        # frozen=True freezes the ATTRIBUTES, not the dicts they point at (#5): wrap
        # the mappings so a caller cannot mutate pricing/health/sources after the
        # snapshot (and its digest) are fixed.
        object.__setattr__(self, "pricing", MappingProxyType(dict(self.pricing)))
        object.__setattr__(self, "health", MappingProxyType(dict(self.health)))
        object.__setattr__(self, "sources", MappingProxyType(dict(self.sources)))


@dataclass(frozen=True)
class Candidate:
    """One ranked option in a chain, priced against the requirement's budget."""

    model_ref: ModelRef
    pricing: ModelPricing
    worst_case_credits: float
    approved_ceiling_credits: float

    @property
    def cost_class(self) -> CostClass:
        return cost_class_of(self.model_ref.backend, self.pricing)


@dataclass(frozen=True)
class ModelChain:
    """The ordered decision + provenance. Carries the ``call_budget`` it was
    priced against so ``execute`` can enforce it; ``snapshot_digest`` binds the
    FULL canonical snapshot (not just the catalog). ``resolved_at`` is DERIVED
    from the snapshot (``= snapshot.observed_at``), never a clock call inside the
    pure ``select`` — preserving determinism + byte-identity (SC-001)."""

    candidates: tuple[Candidate, ...]
    resolved_at: datetime
    call_budget: CallBudget
    snapshot_digest: str
    snapshot_provenance: dict[str, SnapshotProvenance]
    selection_policy_version: int
    explanation: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "snapshot_provenance", MappingProxyType(dict(self.snapshot_provenance))
        )


def worst_case_credits(pricing: ModelPricing, budget: CallBudget) -> float | None:
    """Estimated maximum cost of ONE call, in credits, or ``None`` if pricing is
    unknown (an unknown price NEVER qualifies as free — the caller must exclude
    it from paid selection). Input/output USD rates are applied separately."""
    if not pricing.is_known:
        return None
    return USD_TO_CREDITS * (
        budget.max_input_tokens * (pricing.input_usd_per_token or 0.0)
        + budget.max_output_tokens * (pricing.output_usd_per_token or 0.0)
    )


def worst_case_usd(pricing: ModelPricing, budget: CallBudget) -> float | None:
    """``worst_case_credits`` expressed in USD, or ``None`` if pricing is unknown."""
    credits = worst_case_credits(pricing, budget)
    return None if credits is None else credits / USD_TO_CREDITS


def cost_class_of(backend: str, pricing: ModelPricing) -> CostClass:
    """Funded iff the backend is funded, whatever the price; else free iff priced zero."""
    if backend in FUNDED_BACKENDS:
        return "funded"
    return "free" if pricing.is_free else "paid"


def shift_level(level: StrengthLevel, delta: int) -> StrengthLevel:
    """Move ``level`` by ``delta`` steps, clamped to [economy, strongest]."""
    i = STRENGTH_LEVELS.index(level) + delta
    return STRENGTH_LEVELS[max(0, min(len(STRENGTH_LEVELS) - 1, i))]
