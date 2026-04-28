"""Pydantic v2 models matching every contract under contracts/.

Each model mirrors a YAML/JSON Schema file in
specs/001-agentic-pipeline-refactor/contracts/. Cross-field invariants from
those schemas are enforced via Pydantic validators.

The models are the single source of truth for in-memory representations;
on-disk forms (YAML / JSONL / Markdown frontmatter) are read into and
written out from these models via state/.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


class Stage(str, Enum):
    """Project lifecycle stages (FR-003).

    Mirrors the enum in contracts/project-state.schema.yaml. The
    Advancement-Evaluator Agent is the sole writer of this field.
    """

    # Idea-generation phase
    BRAINSTORMED = "brainstormed"
    FLESH_OUT_IN_PROGRESS = "flesh_out_in_progress"
    FLESH_OUT_COMPLETE = "flesh_out_complete"
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
    RESEARCH_MINOR_REVISION = "research_minor_revision"
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
    PAPER_MINOR_REVISION = "paper_minor_revision"
    PAPER_MAJOR_REVISION_WRITING = "paper_major_revision_writing"
    PAPER_MAJOR_REVISION_SCIENCE = "paper_major_revision_science"
    PAPER_FUNDAMENTAL_FLAWS = "paper_fundamental_flaws"
    POSTED = "posted"
    # Cross-stage states
    HUMAN_INPUT_NEEDED = "human_input_needed"
    BLOCKED = "blocked"


class ArtifactKind(str, Enum):
    IDEA = "idea"
    TECHNICAL_DESIGN = "technical_design"
    IMPLEMENTATION_PLAN = "implementation_plan"
    CODE = "code"
    DATA = "data"
    PAPER = "paper"
    REVIEW = "review"
    STATUS_COMMENT = "status_comment"
    PROJECT_STATE = "project_state"


class BackendName(str, Enum):
    DARTMOUTH = "dartmouth"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"


class BackendKind(str, Enum):
    OPENAI_COMPATIBLE = "openai_compatible"
    HF_INFERENCE = "hf_inference"
    LOCAL_TRANSFORMERS = "local_transformers"


class CitationKind(str, Enum):
    URL = "url"
    ARXIV = "arxiv"
    DOI = "doi"
    DATASET = "dataset"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNREACHABLE = "unreachable"
    MISMATCH = "mismatch"
    PENDING = "pending"


class ReviewerKind(str, Enum):
    LLM = "llm"
    HUMAN = "human"


class Outcome(str, Enum):
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


class ReviewRecord(_Strict):
    """Frontmatter of a review file under projects/<PROJ-ID>/reviews/{research,paper}/."""

    reviewer_name: str = Field(min_length=1)
    reviewer_kind: ReviewerKind
    artifact_path: str
    artifact_hash: Sha256Field
    score: Literal[0.0, 0.5, 1.0]
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
    paid_opt_in: Literal[False]  # v1 invariant: Constitution Principle IV


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


__all__ = [
    "AgentRegistry",
    "AgentRegistryEntry",
    "ArtifactKind",
    "BackendEntry",
    "BackendKind",
    "BackendName",
    "Citation",
    "CitationKind",
    "Lock",
    "Outcome",
    "Project",
    "ReviewRecord",
    "ReviewerKind",
    "RunLogEntry",
    "Stage",
    "Task",
    "VerificationStatus",
]
