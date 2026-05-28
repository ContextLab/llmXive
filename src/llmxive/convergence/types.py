"""Data model for the convergence engine (spec 015 T004-T006, #239).

Pydantic v2 models for the identify -> revise -> re-review protocol plus the
``Severity`` ordering used for adaptive kickback routing. See
``specs/015-pipeline-convergence-protocol/data-model.md`` and
``contracts/convergence-engine.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

# --- Severity -------------------------------------------------------------


class Severity(StrEnum):
    """Concern severity, ordered least->most serious (drives kickback routing).

    Widens the existing ``ActionItem.severity`` (``writing|science|fatal``);
    ``from_legacy`` maps the old values onto this enum for back-compat.
    """

    TRIVIAL = "trivial"
    CODE = "code"
    WRITING = "writing"
    REQUIREMENT = "requirement"
    METHODOLOGY = "methodology"
    SCIENCE = "science"
    FATAL = "fatal"


_SEVERITY_ORDER: tuple[Severity, ...] = (
    Severity.TRIVIAL,
    Severity.CODE,
    Severity.WRITING,
    Severity.REQUIREMENT,
    Severity.METHODOLOGY,
    Severity.SCIENCE,
    Severity.FATAL,
)
_SEVERITY_RANK: dict[Severity, int] = {s: i for i, s in enumerate(_SEVERITY_ORDER)}
_LEGACY_SEVERITY: dict[str, Severity] = {
    "writing": Severity.WRITING,
    "science": Severity.SCIENCE,
    "fatal": Severity.FATAL,
}


def severity_rank(s: Severity) -> int:
    """Ordinal rank (0 = least serious)."""
    return _SEVERITY_RANK[s]


def worst_severity(severities: list[Severity]) -> Severity:
    """Return the most-serious severity in the list (for kickback routing)."""
    if not severities:
        raise ValueError("worst_severity() requires at least one severity")
    return max(severities, key=severity_rank)


def from_legacy_severity(value: str) -> Severity:
    """Map a legacy ``ActionItem.severity`` (writing/science/fatal) onto Severity."""
    key = value.strip().lower()
    if key in _LEGACY_SEVERITY:
        return _LEGACY_SEVERITY[key]
    return Severity(key)  # raises ValueError on an unknown value (fail fast)


# --- Records (persisted; strict) ------------------------------------------


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Concern(_Strict):
    """A single critical finding raised in R1 (or newly in R3)."""

    id: str
    reviewer: str
    severity: Severity
    artifact: str
    location: str = ""
    text: str
    round: int = 1


class ConcernResponse(_Strict):
    """The reviser's per-concern reply (R2)."""

    concern_id: str
    response: str
    what_changed: str
    artifacts_changed: list[str] = Field(default_factory=list)


class Verdict(_Strict):
    """A panelist's R3 judgment of one of its own concerns."""

    concern_id: str
    reviewer: str
    status: Literal["pass", "fail"]
    new_concerns: list[Concern] = Field(default_factory=list)
    stale: bool = False
    self_review: bool = False


class ProgressRecord(_Strict):
    """Per-kickback progress snapshot (enables no-cap-but-inspectable iteration)."""

    kickback_index: int
    unresolved_concern_ids: list[str]
    improved: bool


class KickbackRecord(_Strict):
    """Emitted on non-convergence: full provenance for the next worker (FR-014)."""

    from_stage: str
    to_stage: str
    worst_severity: Severity
    unresolved_concerns: list[Concern] = Field(default_factory=list)
    artifact_links: list[str] = Field(default_factory=list)
    reason: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ConvergenceResult(_Strict):
    """The engine's outcome for one reviewable step. ``converged`` ALWAYS
    reflects reality (FR-016 — no masked non-convergence)."""

    stage: str
    converged: bool
    rounds_used: int
    concern_history: list[Concern] = Field(default_factory=list)
    response_history: list[ConcernResponse] = Field(default_factory=list)
    verdict_history: list[Verdict] = Field(default_factory=list)
    next_stage: str | None = None
    kickback: KickbackRecord | None = None
    inspection_path: str | None = None


class TriageRecord(_Strict):
    """A submitted human/personality review after stage-aware triage (FR-021/022)."""

    source: Literal["human", "personality"]
    author: str
    stage_context: str
    quality_pass: bool
    safe_on_topic: bool
    mapped_lenses: list[str] = Field(default_factory=list)
    preserved: bool
    excluded_reason: str | None = None
    review_text: str


# --- Reviewer / Reviser protocols + ReviewSpec (runtime config) -----------


@runtime_checkable
class Reviewer(Protocol):
    """A panel lens. ``identify`` raises R1 concerns; ``rereview`` judges its own
    concerns in R3. (Callables, not data — see contracts/convergence-engine.md.)"""

    name: str

    def identify(
        self, artifacts: dict[str, str], *, constitution: str | None, advisory: list[str]
    ) -> list[Concern]: ...

    def rereview(
        self,
        artifacts: dict[str, str],
        own_concerns: list[Concern],
        responses: list[ConcernResponse],
        *,
        constitution: str | None,
        advisory: list[str],
    ) -> list[Verdict]: ...


@runtime_checkable
class Reviser(Protocol):
    """The step's author/refiner (R2): addresses every concern, returns the updated
    artifacts + a per-concern change-log."""

    def revise(
        self, artifacts: dict[str, str], concerns: list[Concern]
    ) -> tuple[dict[str, str], list[ConcernResponse]]: ...


@dataclass
class ReviewSpec:
    """Per-step configuration the engine consumes (one per reviewable stage).

    Holds runtime callables (reviewers/reviser), so it is a dataclass rather than a
    pydantic model. ``reviewspecs.reviewspec_for(stage)`` builds these (US4).
    """

    stage: str
    artifacts: list[str]
    reviewers: list[Reviewer]
    reviser: Reviser | None
    kickback_routing: dict[Severity, str]
    overflow_goal: str
    constitution_input: bool = False
    max_rounds: int = 3
    exempt: bool = False
    extra: dict[str, str] = field(default_factory=dict)


__all__ = [
    "Concern",
    "ConcernResponse",
    "ConvergenceResult",
    "KickbackRecord",
    "ProgressRecord",
    "ReviewSpec",
    "Reviewer",
    "Reviser",
    "Severity",
    "TriageRecord",
    "Verdict",
    "from_legacy_severity",
    "severity_rank",
    "worst_severity",
]
