"""Data model for the convergence engine (spec 015 T004-T006, #239).

Pydantic v2 models for the identify -> revise -> re-review protocol plus the
``Severity`` ordering used for adaptive kickback routing. See
``specs/015-pipeline-convergence-protocol/data-model.md`` and
``contracts/convergence-engine.md``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


logger = logging.getLogger(__name__)

# LLM panels frequently emit a GENERIC severity word (low/medium/high/minor/
# major/critical) instead of llmXive's domain classes. A hard ``Severity(raw)``
# ValueError on those crashed the whole stage panel — the live PROJ-492 tasks
# gate "unknown severity 'low'" engine failure that blocks EVERY project at the
# tasks stage. Map the common generic vocabulary onto the canonical enum by
# RANK, and — crucially — keep every generic mapping inside the in-place
# doc-revision band (trivial..requirement): a generic word must NEVER trigger the
# drastic idea-stage re-routing reserved for an EXPLICIT methodology/science/
# fatal class (which the panel prompts still name verbatim when they mean it).
_SEVERITY_SYNONYMS: dict[str, Severity] = {
    "trivial": Severity.TRIVIAL, "nit": Severity.TRIVIAL, "nitpick": Severity.TRIVIAL,
    "info": Severity.TRIVIAL, "informational": Severity.TRIVIAL, "cosmetic": Severity.TRIVIAL,
    "suggestion": Severity.TRIVIAL, "optional": Severity.TRIVIAL,
    "low": Severity.WRITING, "minor": Severity.WRITING, "small": Severity.WRITING,
    "style": Severity.WRITING, "note": Severity.WRITING, "polish": Severity.WRITING,
    "medium": Severity.REQUIREMENT, "moderate": Severity.REQUIREMENT,
    "normal": Severity.REQUIREMENT, "default": Severity.REQUIREMENT,
    "high": Severity.REQUIREMENT, "major": Severity.REQUIREMENT, "important": Severity.REQUIREMENT,
    "critical": Severity.REQUIREMENT, "blocker": Severity.REQUIREMENT, "blocking": Severity.REQUIREMENT,
    "severe": Severity.REQUIREMENT, "serious": Severity.REQUIREMENT,
}


def coerce_severity(value: str, *, lens: str = "") -> Severity:
    """Best-effort map an LLM-emitted severity string onto :class:`Severity`.

    Canonical values pass through unchanged; common GENERIC vocabulary
    (low/medium/high/minor/major/critical/...) maps by rank into the in-place
    doc-revision band; a genuinely unrecognised value defaults to ``writing``
    with a warning rather than crashing the stage panel. This is robust parsing,
    not silent papering-over — the unexpected token is logged loudly, and the
    canonical methodology/science/fatal classes (which alone trigger idea-stage
    routing) are NEVER produced from a generic word.
    """
    key = (value or "").strip().lower()
    try:
        return Severity(key)
    except ValueError:
        pass
    if key in _SEVERITY_SYNONYMS:
        return _SEVERITY_SYNONYMS[key]
    logger.warning(
        "coerce_severity: unrecognised severity %r%s; defaulting to 'writing'",
        value, f" (lens={lens})" if lens else "",
    )
    return Severity.WRITING


# --- Records (persisted; strict) ------------------------------------------


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Concern(_Strict):
    """A single critical finding raised in R1 (or newly in R3).

    ``text`` MUST be a non-empty, non-whitespace-only description of the
    finding (``min_length=1`` + whitespace-stripping validator). A concern
    without text is structurally meaningless — the panel claims a problem
    exists but never says what — and gets silently rendered downstream as
    ``... — `` with nothing after the em-dash. We reject those at the
    model layer (mirrors the existing ``ActionItem.text: min_length=1``
    invariant in ``llmxive.types``) so the bug surfaces at the source.

    ``location`` stays optional (default ``""``) because some panel
    prompts emit it as a free-form pointer that is naturally absent for
    whole-artifact concerns; the SSoT ``panel_review_block.md`` schema
    treats it as an aid to the reviser, not a structural requirement.
    """

    id: str
    reviewer: str
    severity: Severity
    artifact: str
    location: str = ""
    text: str = Field(min_length=1)
    round: int = 1

    @field_validator("text")
    @classmethod
    def _text_not_whitespace_only(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError(
                "Concern.text must contain non-whitespace content "
                "(empty / whitespace-only concerns are structurally invalid)"
            )
        return stripped


class ConcernResponse(_Strict):
    """The reviser's per-concern reply (R2).

    Both ``response`` and ``what_changed`` are required non-empty: a
    reviser that returns an empty ``response`` claims to have addressed
    a concern with no description, and an empty ``what_changed`` claims
    a change happened without saying what. Both are equivalent to the
    empty-``Concern.text`` bug and rejected at the same layer. The
    existing reviser implementations all substitute explicit
    placeholders (``"<missing>"`` / ``"<empty>"``) when the LLM omits
    the field, so this validator never breaks the honest fail-loud
    path — it only catches programmer mistakes.
    """

    concern_id: str
    response: str = Field(min_length=1)
    what_changed: str = Field(min_length=1)
    artifacts_changed: list[str] = Field(default_factory=list)

    @field_validator("response", "what_changed")
    @classmethod
    def _not_whitespace_only(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError(
                "ConcernResponse fields must contain non-whitespace content "
                "(empty / whitespace-only responses are structurally invalid)"
            )
        return stripped


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
    advance_stage: str | None = None  # the normal forward stage on convergence
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
