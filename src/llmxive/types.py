"""Pydantic v2 models matching every contract under contracts/.

Each model mirrors a YAML/JSON Schema file in
specs/001-agentic-pipeline-refactor/contracts/. Cross-field invariants from
those schemas are enforced via Pydantic validators.

The models are the single source of truth for in-memory representations;
on-disk forms (YAML / JSONL / Markdown frontmatter) are read into and
written out from these models via state/.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ----- action item id (spec 012) ---------------------------------------------

# Strip section/figure references (e.g., "in Section 4.1", "Figure 3") before
# hashing so cosmetic LLM rephrasings that change only the reference don't
# break ID stability across re-reviews.
_SECTION_REF_RE = re.compile(r"\b(?:Section|Sec\.?)\s*\d+(?:\.\d+)*\b", re.IGNORECASE)
_FIGURE_REF_RE = re.compile(r"\b(?:Figure|Fig\.?)\s*\d+(?:\.\d+)*\b", re.IGNORECASE)
_TABLE_REF_RE = re.compile(r"\b(?:Table|Tab\.?)\s*\d+(?:\.\d+)*\b", re.IGNORECASE)
_EQ_REF_RE = re.compile(r"\b(?:Equation|Eq\.?)\s*\d+(?:\.\d+)*\b", re.IGNORECASE)
_PUNCT_RE = re.compile(r"[\s,;:!?\.\(\)\[\]\{\}'\"`\-_/\\]+")


def _canonicalize_action_item_text(text: str) -> str:
    """Normalize an action item's text for stable ID derivation.

    Steps (in order):
      1. Strip section/figure/table/equation references.
      2. Lowercase.
      3. Collapse all punctuation runs and whitespace to a single space.
      4. Strip leading/trailing whitespace.
    """
    s = _SECTION_REF_RE.sub("", text)
    s = _FIGURE_REF_RE.sub("", s)
    s = _TABLE_REF_RE.sub("", s)
    s = _EQ_REF_RE.sub("", s)
    s = s.lower()
    s = _PUNCT_RE.sub(" ", s)
    return s.strip()


def action_item_id(text: str) -> str:
    """Compute a stable 12-char hex ID for an action item from its text.

    Two action items whose texts are canonicalize-equivalent will share an
    ID. This is the contract from spec 012's research R1: stability across
    re-reviews depends on the SAME concern producing the SAME hash.
    """
    canonical = _canonicalize_action_item_text(text)
    return hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:12]

# ----- shared regexes ---------------------------------------------------------

PROJ_ID_RE: re.Pattern[str] = re.compile(r"^PROJ-\d{3,}-[a-z0-9-]+$")
SHA256_RE: re.Pattern[str] = re.compile(r"^[a-f0-9]{64}$")
SEMVER_RE: re.Pattern[str] = re.compile(r"^\d+\.\d+\.\d+$")
SNAKE_NAME_RE: re.Pattern[str] = re.compile(r"^[a-z][a-z0-9_]*$")
PROMPT_PATH_RE: re.Pattern[str] = re.compile(r"^agents/prompts/[a-z0-9_]+\.md$")

ProjectIdField = Annotated[str, Field(pattern=PROJ_ID_RE.pattern)]
Sha256Field = Annotated[str, Field(pattern=SHA256_RE.pattern)]
SemverField = Annotated[str, Field(pattern=SEMVER_RE.pattern)]
SnakeNameField = Annotated[str, Field(pattern=SNAKE_NAME_RE.pattern)]


# ----- enums ------------------------------------------------------------------


class Stage(StrEnum):
    """Project lifecycle stages (FR-003).

    Mirrors the enum in contracts/project-state.schema.yaml. The
    Advancement-Evaluator Agent is the sole writer of this field.
    """

    # Idea-generation phase
    BRAINSTORMED = "brainstormed"
    FLESH_OUT_IN_PROGRESS = "flesh_out_in_progress"
    FLESH_OUT_COMPLETE = "flesh_out_complete"
    # Research-question validation: catches implementation-method narrowing
    # and circular question framing before idea_selector promotes the project.
    # Verdicts: validated (advance) | validator_revise (back to flesh_out) |
    # validator_rejected (back to brainstormed).
    VALIDATED = "validated"
    VALIDATOR_REVISE = "validator_revise"
    VALIDATOR_REJECTED = "validator_rejected"
    # Per-project research Spec Kit pipeline
    PROJECT_INITIALIZED = "project_initialized"
    SPECIFIED = "specified"
    CLARIFY_IN_PROGRESS = "clarify_in_progress"
    CLARIFIED = "clarified"
    PLANNED = "planned"
    TASKED = "tasked"
    ANALYZE_IN_PROGRESS = "analyze_in_progress"
    ANALYZED = "analyzed"
    IN_PROGRESS = "in_progress"
    RESEARCH_COMPLETE = "research_complete"
    # Research-quality review
    RESEARCH_REVIEW = "research_review"
    RESEARCH_ACCEPTED = "research_accepted"
    # Spec 015 T042 / FR-034: the 7 transient revision stages
    # (RESEARCH_MINOR_REVISION, RESEARCH_FULL_REVISION? - kept,
    # PAPER_MINOR_REVISION, PAPER_MAJOR_REVISION_WRITING/SCIENCE,
    # PAPER_REVISION_IN_PROGRESS, READY_FOR_IMPLEMENTATION,
    # PAPER_REVISION_BLOCKED) were DELETED. The convergence engine is
    # the sole inter-stage revision driver: every non-convergence emits
    # a ``KickbackRecord`` whose ``to_stage`` is a regular (stable)
    # stage like ``tasked`` / ``clarified`` / ``brainstormed``, and the
    # auto-revisions directory (specs/auto-revisions/<id>/round-N/)
    # carries the per-concern work for the implementer agent to pick
    # up. See ``llmxive.convergence.revision_adapter`` for the bridge.
    RESEARCH_FULL_REVISION = "research_full_revision"
    RESEARCH_REJECTED = "research_rejected"
    # Paper drafting Spec Kit pipeline
    PAPER_DRAFTING_INIT = "paper_drafting_init"
    PAPER_SPECIFIED = "paper_specified"
    PAPER_CLARIFIED = "paper_clarified"
    PAPER_PLANNED = "paper_planned"
    PAPER_TASKED = "paper_tasked"
    PAPER_ANALYZED = "paper_analyzed"
    PAPER_IN_PROGRESS = "paper_in_progress"
    PAPER_COMPLETE = "paper_complete"
    # Final paper review
    PAPER_REVIEW = "paper_review"
    PAPER_ACCEPTED = "paper_accepted"
    PAPER_FUNDAMENTAL_FLAWS = "paper_fundamental_flaws"
    # Spec 015 (FR-036/FR-054): mandatory manual maintainer sign-off gate before
    # any Zenodo DOI mint. Flow: paper_accepted -> publisher(assemble) ->
    # awaiting_publication_signoff -> [maintainer approves] -> publisher(mint) -> posted.
    AWAITING_PUBLICATION_SIGNOFF = "awaiting_publication_signoff"
    POSTED = "posted"
    # Spec 013 (FR-030): 5 consecutive Zenodo failures during publication
    # transition the project to PUBLISH_BLOCKED. Operator clears via
    # `llmxive project republish <PROJ-ID>` which rolls back to PAPER_ACCEPTED.
    PUBLISH_BLOCKED = "publish_blocked"
    # Cross-stage states
    HUMAN_INPUT_NEEDED = "human_input_needed"
    BLOCKED = "blocked"
    # Spec 015 T042 / FR-034 generic agent-failsafe state. Reached when
    # an agent's failsafe (e.g. implementer's 5-consecutive-failure
    # diagnostic) cannot classify the failure into an actionable Concern.
    # Cleared via `llmxive project unblock-agent <PROJ-ID>` after the
    # operator edits the action items file.
    AGENT_BLOCKED = "agent_blocked"


class ArtifactKind(StrEnum):
    IDEA = "idea"
    TECHNICAL_DESIGN = "technical_design"
    IMPLEMENTATION_PLAN = "implementation_plan"
    CODE = "code"
    DATA = "data"
    PAPER = "paper"
    REVIEW = "review"
    STATUS_COMMENT = "status_comment"
    PROJECT_STATE = "project_state"


class BackendName(StrEnum):
    DARTMOUTH = "dartmouth"
    # The HF Inference-API backend was removed (2026-05-29): HF models run
    # LOCALLY via the `local`/transformers backend, with no API token.
    LOCAL = "local"


class BackendKind(StrEnum):
    OPENAI_COMPATIBLE = "openai_compatible"
    HF_INFERENCE = "hf_inference"
    LOCAL_TRANSFORMERS = "local_transformers"


class CitationKind(StrEnum):
    URL = "url"
    ARXIV = "arxiv"
    DOI = "doi"
    DATASET = "dataset"


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    UNREACHABLE = "unreachable"
    MISMATCH = "mismatch"
    PENDING = "pending"


class ReviewerKind(StrEnum):
    LLM = "llm"
    HUMAN = "human"


class Outcome(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    QUARANTINED = "quarantined"


# ----- models -----------------------------------------------------------------


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Project(_Strict):
    """state/projects/<PROJ-ID>.yaml (contracts/project-state.schema.yaml)."""

    id: ProjectIdField
    title: str = Field(min_length=1, max_length=250)
    field: str = Field(min_length=1)
    current_stage: Stage
    points_research: dict[str, float] = Field(default_factory=dict)
    points_paper: dict[str, float] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    last_run_id: str | None = None
    last_run_status: Literal["success", "failed", "skipped", "blocked"] | None = None
    failed_stage: str | None = None
    artifact_hashes: dict[str, Sha256Field] = Field(default_factory=dict)
    assigned_agent: SnakeNameField | None = None
    speckit_research_dir: str | None = None
    speckit_paper_dir: str | None = None
    revision_round: int = Field(default=0, ge=0)
    human_escalation_reason: str | None = None
    # Spec 015 T042: points to the most-recent auto-revisions directory
    # (specs/auto-revisions/<id>/round-N/) written by
    # ``llmxive.convergence.revision_adapter.kickback_to_revision_spec``
    # whenever the convergence engine emits a KickbackRecord. The
    # implementer agent polls projects with this set + a non-empty
    # auto-revisions tasks.md and applies the per-Concern work in place.
    # Cleared back to None when the implementer completes a round.
    revision_spec_path: str | None = None

    @field_validator("points_research", "points_paper")
    @classmethod
    def _non_negative(cls, value: dict[str, float]) -> dict[str, float]:
        for k, v in value.items():
            if v < 0:
                raise ValueError(f"point bucket {k!r} must be >= 0; got {v}")
        return value

    @model_validator(mode="after")
    def _stage_invariants(self) -> Project:
        # FR-007 self-review prohibition does not apply here; that lives on
        # ReviewRecord. Cross-field invariants documented in contracts/.
        if self.current_stage in {Stage.SPECIFIED, Stage.CLARIFIED, Stage.PLANNED, Stage.TASKED,
                                  Stage.ANALYZED, Stage.IN_PROGRESS, Stage.RESEARCH_COMPLETE}:
            if not self.speckit_research_dir:
                raise ValueError(
                    f"speckit_research_dir is required from 'specified' onward "
                    f"(stage={self.current_stage.value})"
                )
        if self.current_stage in {Stage.PAPER_SPECIFIED, Stage.PAPER_CLARIFIED, Stage.PAPER_PLANNED,
                                  Stage.PAPER_TASKED, Stage.PAPER_ANALYZED, Stage.PAPER_IN_PROGRESS,
                                  Stage.PAPER_COMPLETE}:
            if not self.speckit_paper_dir:
                raise ValueError(
                    f"speckit_paper_dir is required from 'paper_specified' onward "
                    f"(stage={self.current_stage.value})"
                )
        if self.current_stage == Stage.HUMAN_INPUT_NEEDED and not self.human_escalation_reason:
            raise ValueError("human_escalation_reason is required when stage='human_input_needed'")
        return self


class Citation(_Strict):
    """One entry inside state/citations/<PROJ-ID>.yaml."""

    cite_id: str = Field(min_length=1)
    artifact_path: str
    artifact_hash: Sha256Field
    kind: CitationKind
    value: str = Field(min_length=1)
    cited_title: str | None = None
    cited_authors: list[str] = Field(default_factory=list)
    verification_status: VerificationStatus
    verified_against_url: str | None = None
    fetched_title: str | None = None
    verified_at: datetime | None = None

    @field_validator("artifact_path")
    @classmethod
    def _under_project(cls, value: str) -> str:
        if not value.startswith("projects/PROJ-"):
            raise ValueError("artifact_path must start with projects/PROJ-")
        return value


class ActionItem(_Strict):
    """One concrete reviewer-raised concern (spec 012).

    Two action items with the same `id` represent the same concern (the id
    is deterministic from `canonicalize(text)`). When a re-reviewer flags
    the same concern they MUST reuse the prior id rather than minting a
    new one — see FR-020 and contracts/action_item.md.
    """

    id: str = Field(pattern=r"^[0-9a-f]{12}$")
    text: str = Field(min_length=1, max_length=500)
    severity: Literal["writing", "science", "fatal"]

    @classmethod
    def from_text(cls, text: str, severity: Literal["writing", "science", "fatal"]) -> ActionItem:
        """Build an ActionItem from text + severity, auto-deriving the id."""
        return cls(id=action_item_id(text), text=text, severity=severity)


class ReviewRecord(_Strict):
    """Frontmatter of a review file under projects/<PROJ-ID>/reviews/{research,paper}/."""

    reviewer_name: str = Field(min_length=1)
    reviewer_kind: ReviewerKind
    artifact_path: str
    artifact_hash: Sha256Field
    score: float
    verdict: Literal[
        "accept",
        "minor_revision",
        "full_revision",
        "reject",
        "major_revision_writing",
        "major_revision_science",
        "fundamental_flaws",
    ]
    feedback: str = ""
    reviewed_at: datetime
    prompt_version: SemverField | None = None
    model_name: str | None = None
    backend: BackendName | None = None
    # Set to True ONLY by the OAuth-authenticated submission flow
    # (web auth → GitHub PR/issue with the user's verified login).
    # Self-written human reviews dropped into the filesystem MUST NOT
    # set this; the advancement-evaluator refuses to count points
    # from human reviews where this is False/missing.
    github_authenticated: bool = False
    # Spec 012: structured action items per-reviewer. Empty for accept;
    # non-empty for non-accept (validator below). Old records (without this
    # field) load with the default empty list — back-compat preserved.
    action_items: list[ActionItem] = Field(default_factory=list)

    @field_validator("score")
    @classmethod
    def _score_in_allowed_set(cls, v: float) -> float:
        # Spec 015 removes the point system, but this field is retained for
        # back-compat with stored records; preserve the historical constraint.
        # (Replaces a Literal[float] annotation, which is invalid per PEP 586.)
        if v not in (0.0, 0.5, 1.0):
            raise ValueError("score must be one of 0.0, 0.5, 1.0")
        return v

    @model_validator(mode="after")
    def _score_matches_verdict(self) -> ReviewRecord:
        if self.reviewer_kind == ReviewerKind.LLM:
            if self.verdict == "accept" and self.score != 0.5:
                raise ValueError("LLM accept must score 0.5")
            if self.verdict in {"reject", "minor_revision", "full_revision",
                                "major_revision_writing", "major_revision_science",
                                "fundamental_flaws"} and self.score != 0.0:
                raise ValueError(f"LLM non-accept verdict {self.verdict!r} must score 0.0")
            if self.prompt_version is None or self.model_name is None or self.backend is None:
                raise ValueError(
                    "LLM reviews must declare prompt_version, model_name, backend"
                )
            # Spec 012 / FR-018: structured action items required for
            # non-accept verdicts emitted under prompt_version >= 1.1.0.
            # Legacy records (prompt_version 1.0.x) are grandfathered to
            # preserve back-compat with reviews emitted before this spec.
            if (
                self.prompt_version is not None
                and self.prompt_version >= "1.1.0"
                and self.verdict != "accept"
                and len(self.action_items) == 0
            ):
                raise ValueError(
                    f"LLM non-accept verdict {self.verdict!r} under prompt_version "
                    f"{self.prompt_version} must include at least one action_item"
                )
        else:  # human
            if self.verdict == "accept" and self.score != 1.0:
                raise ValueError("human accept must score 1.0")
        return self


class RunLogEntry(_Strict):
    """One line in state/run-log/<YYYY-MM>/<run-id>.jsonl."""

    run_id: str
    entry_id: str
    parent_entry_id: str | None = None
    agent_name: SnakeNameField
    project_id: ProjectIdField
    task_id: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    backend: BackendName
    model_name: str = Field(min_length=1)
    prompt_version: SemverField
    started_at: datetime
    ended_at: datetime
    outcome: Outcome
    failure_reason: str | None = None
    cost_estimate_usd: float = Field(ge=0.0)

    @model_validator(mode="after")
    def _time_order(self) -> RunLogEntry:
        if self.ended_at < self.started_at:
            raise ValueError("ended_at must be >= started_at")
        return self


class BackendEntry(_Strict):
    name: BackendName
    kind: BackendKind
    auth_env_vars: list[str] = Field(default_factory=list)
    base_url: str | None = None
    daily_quota_estimate: int | None = Field(default=None, ge=0)
    is_paid: Literal[False]  # v1 invariant: Constitution Principle IV


class AgentRegistryEntry(_Strict):
    name: SnakeNameField
    purpose: str = Field(min_length=10, max_length=200)
    inputs: list[ArtifactKind] = Field(default_factory=list)
    outputs: list[ArtifactKind] = Field(default_factory=list)
    prompt_path: Annotated[str, Field(pattern=PROMPT_PATH_RE.pattern)]
    prompt_version: SemverField
    default_backend: BackendName
    fallback_backends: list[BackendName] = Field(default_factory=list)
    default_model: str = Field(min_length=1)
    tools: list[SnakeNameField] = Field(default_factory=list)
    wall_clock_budget_seconds: int = Field(ge=30, le=1800)
    # Default False (Constitution Principle IV free-first). True is
    # sanctioned ONLY via the credit-managed Dartmouth daily-budget path
    # (issue #295; runtime-gated by LLMXIVE_PAID_OPT_IN + the live credit
    # cap in backends/credits.py) and requires written justification in
    # the introducing PR.
    paid_opt_in: bool = False


class AgentRegistry(_Strict):
    version: SemverField
    backends: list[BackendEntry]
    agents: list[AgentRegistryEntry] = Field(default_factory=list)


class Lock(_Strict):
    project_id: ProjectIdField
    holder_run_id: str
    acquired_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def _expires_after(self) -> Lock:
        if self.expires_at <= self.acquired_at:
            raise ValueError("expires_at must be > acquired_at")
        return self


class Task(_Strict):
    task_id: str
    parent_task_id: str | None = None
    agent_name: SnakeNameField
    project_id: ProjectIdField
    wall_clock_estimate_seconds: int = Field(ge=1)
    inputs: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    is_leaf: bool
    siblings_total: int | None = Field(default=None, ge=1)


#  Spec 013 — Paper revision implementer + publisher schemas
#  -------------------------------------------------------------------------
#  These models back the on-disk artifacts the new agents read/write:
#    - ImplementerLogEntry / ImplementerLog → implementer-log.yaml (per round)
#    - RevisionRound / RevisionHistory      → revision_history.yaml
#    - AuthorEntry                          → paper/metadata.json::authors
#    - VolumeIssue / DOIVersion / Publication / ZenodoDeposition
#                                           → paper/publication.yaml + metadata.json mirror
#  Contracts: specs/013-paper-revision-implementer/contracts/.
# -------------------------------------------------------------------------


ImplementerStatus = Literal[
    "done", "compile-failed", "file-not-found", "skipped", "needs-external-data"
]


class ImplementerLogEntry(_Strict):
    """One per task processed in an implementer round (FR-004)."""

    task_id: str
    status: ImplementerStatus
    action_item_severity: Literal["writing", "science"] | None = None
    action_item_text: str = ""
    edit_kind: Literal["search_and_replace", "unified_diff"] | None = None
    files_modified: list[str] = Field(default_factory=list)
    before_hashes: dict[str, Sha256Field] = Field(default_factory=dict)
    after_hashes: dict[str, Sha256Field] = Field(default_factory=dict)
    model_response_excerpt: str = ""
    duration_s: float = Field(ge=0.0)
    error_reason: str | None = None


class ImplementerLog(_Strict):
    """`specs/auto-revisions/<PROJ-ID>/round-<N>/implementer-log.yaml`."""

    schema_version: Literal["1"] = "1"
    round_number: int = Field(ge=1)
    project_id: ProjectIdField
    revision_spec_path: str
    implementer_agent: str          # name only (dedupe key part 1)
    agent_version: str              # dedupe key part 2
    model_name: str
    backend: str
    canonical_identity: str
    started_at: datetime
    ended_at: datetime
    duration_s: float = Field(ge=0.0)
    exit_reason: Literal[
        "all-tasks-processed", "wall-clock-budget-exceeded", "halted-error"
    ]
    total_tasks: int = Field(ge=0)
    tasks_done: int = Field(ge=0)
    tasks_compile_failed: int = Field(ge=0)
    tasks_file_not_found: int = Field(ge=0)
    tasks_skipped: int = Field(ge=0)
    tasks_needs_external_data: int = Field(ge=0)
    final_compile_attempted: bool = False
    final_compile_succeeded: bool = False
    final_compile_pdf_sha256: Sha256Field | None = None
    final_compile_pdf_bytes: int | None = None
    author_added: bool = False
    author_entry: AuthorEntry | None = None  # forward-declared below
    task_outcomes: list[ImplementerLogEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def _outcome_count_invariant(self) -> ImplementerLog:
        observed_total = (self.tasks_done + self.tasks_compile_failed
                          + self.tasks_file_not_found + self.tasks_skipped
                          + self.tasks_needs_external_data)
        if observed_total != self.total_tasks:
            raise ValueError(
                f"task outcome counts ({observed_total}) must sum to total_tasks "
                f"({self.total_tasks})"
            )
        if len(self.task_outcomes) != self.total_tasks:
            raise ValueError(
                f"len(task_outcomes)={len(self.task_outcomes)} != total_tasks={self.total_tasks}"
            )
        return self


class RevisionRound(_Strict):
    """One entry per round in `paper/revision_history.yaml` (FR-009).

    Summary form: see ImplementerLog for the per-task detail.
    """

    round_number: int = Field(ge=1)
    ran_at: datetime
    implementer_agent: str
    canonical_identity: str
    tasks_done: int = Field(ge=0)
    tasks_failed: int = Field(ge=0)
    tasks_skipped: int = Field(ge=0)
    resulting_pdf_sha256: Sha256Field | None = None
    implementer_log_path: str
    task_outcomes: list[dict[str, str]] = Field(default_factory=list)


class RevisionHistory(_Strict):
    """`projects/<PROJ-ID>/paper/revision_history.yaml`. Append-only."""

    schema_version: Literal["1"] = "1"
    project_id: ProjectIdField
    rounds: list[RevisionRound] = Field(default_factory=list)


class AuthorEntry(_Strict):
    """`paper/metadata.json::authors[]` extended schema (FR-006)."""

    name: str = Field(min_length=1)
    kind: Literal["human", "llm"] = "human"
    affiliation: str | None = None
    email: str | None = None
    # LLM-only fields
    agent_version: str | None = None
    model_name: str | None = None
    backend: str | None = None
    first_contributed_at: datetime | None = None


class VolumeIssue(_Strict):
    """Derived from acceptance timestamp; `YY.MM` (FR-024)."""

    volume: str = Field(pattern=r"^\d{2}$")
    issue: str = Field(pattern=r"^\d{2}$")

    @classmethod
    def from_datetime(cls, dt: datetime) -> VolumeIssue:
        return cls(volume=dt.strftime("%y"), issue=dt.strftime("%m"))

    @property
    def display(self) -> str:
        return f"{self.volume}.{self.issue}"


class DOIVersion(_Strict):
    """One row of `publication.yaml::doi_versions[]` (FR-027)."""

    doi: str = Field(pattern=r"^10\.\d{4,9}/[^\s]+$")
    version_index: int = Field(ge=1)
    published_at: datetime
    pdf_sha256: Sha256Field


class ZenodoDeposition(_Strict):
    """Reference to a Zenodo-side record."""

    deposition_id: int = Field(ge=1)
    doi: str
    concept_doi: str | None = None
    published_at: datetime
    pdf_sha256: Sha256Field
    version_index: int = Field(ge=1)


class Publication(_Strict):
    """`projects/<PROJ-ID>/paper/publication.yaml` (FR-032).

    Authoritative publication metadata. `paper/metadata.json` mirrors
    `doi`/`doi_url`/`zenodo_id`/`volume`/`issue` for convenience but
    `publication.yaml` is the single source of truth.
    """

    schema_version: Literal["1"] = "1"
    project_id: ProjectIdField
    title: str = Field(min_length=1)
    volume: str = Field(pattern=r"^\d{2}$")
    issue: str = Field(pattern=r"^\d{2}$")
    display_volume_issue: str = Field(pattern=r"^\d{2}\.\d{2}$")
    doi: str = Field(pattern=r"^10\.\d{4,9}/[^\s]+$")
    doi_url: str = Field(pattern=r"^https://doi\.org/")
    concept_doi: str | None = None
    doi_versions: list[DOIVersion] = Field(default_factory=list)
    zenodo_id: int = Field(ge=1)
    zenodo_environment: Literal["production", "sandbox"] = "production"
    citation_string: str = Field(min_length=1)
    authors_at_publication: list[AuthorEntry] = Field(default_factory=list)
    accepted_at: datetime
    published_at: datetime
    review_summary: dict[str, int] = Field(default_factory=dict)


# Resolve the forward reference inside ImplementerLog.
ImplementerLog.model_rebuild()


__all__ = [
    "AgentRegistry",
    "AgentRegistryEntry",
    "ArtifactKind",
    "AuthorEntry",
    "BackendEntry",
    "BackendKind",
    "BackendName",
    "Citation",
    "CitationKind",
    "DOIVersion",
    "ImplementerLog",
    "ImplementerLogEntry",
    "ImplementerStatus",
    "Lock",
    "Outcome",
    "Project",
    "Publication",
    "ReviewRecord",
    "ReviewerKind",
    "RevisionHistory",
    "RevisionRound",
    "RunLogEntry",
    "Stage",
    "Task",
    "VerificationStatus",
    "VolumeIssue",
    "ZenodoDeposition",
]
