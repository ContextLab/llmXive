"""Research-Reviewer Agent (T064).

Reads the project's implementation artifacts and writes a review
record under
`projects/<PROJ-ID>/reviews/research/<reviewer-name>__<YYYY-MM-DD>__research.md`
with frontmatter validated against `contracts/review-record.schema.yaml`.

Stage transitions are NOT handled here — the Advancement-Evaluator
Agent reads the accumulated review records and decides whether the
project advances to `research_accepted` / `research_minor_revision` /
`research_full_revision` / `research_rejected`.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

import yaml
from pydantic import ValidationError

from llmxive.agents.base import Agent, AgentContext, MalformedResponseError
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.config import repo_root as _repo_root
from llmxive.state import reviews as reviews_store
from llmxive.state import runlog as runlog_store
from llmxive.types import (
    AgentRegistryEntry,
    ReviewerKind,
    ReviewRecord,
)

_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(?P<frontmatter>.*?)\n---\s*\n(?P<body>.*)$",
    re.DOTALL,
)

# Appended to the retry prompt when output validation rejects a response
# (issue #294 typed-boundary work; see base.MalformedResponseError).
_FORMAT_REMINDER = (
    "Your response MUST start with a line containing exactly `---`, "
    "followed by the YAML frontmatter fields required by the review-record "
    "contract in the system prompt, followed by a line containing exactly "
    "`---`, followed by the markdown review body."
)


def _summarize_tree(root: Path, *, max_files: int = 25) -> str:
    """Bulleted listing of files under `root` with byte sizes."""
    if not root.is_dir():
        return "(no files)"
    lines: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(p.startswith(".") for p in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        size = path.stat().st_size
        lines.append(f"- `{rel}` ({size} bytes)")
        if len(lines) >= max_files:
            lines.append(f"- ... ({sum(1 for _ in root.rglob('*')) - max_files} more)")
            break
    return "\n".join(lines) if lines else "(empty)"


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


class ResearchReviewerAgent(Agent):
    """Casts a single research-quality vote on a project's tasks.md."""

    def __init__(self, registry_entry: AgentRegistryEntry) -> None:
        super().__init__(registry_entry)

    def _project_dir(self, ctx: AgentContext) -> Path:
        repo = _repo_root()
        return repo / "projects" / ctx.project_id

    def _feature_dir(self, project_dir: Path) -> Path | None:
        # Prefer the dir that actually has tasks.md, then spec.md.
        # Pure alphabetical sort can pick a ghost dir created when an
        # earlier LLM run wrote artifacts to an invented slug.
        candidates = sorted(project_dir.glob("specs/*/"))
        if not candidates:
            return None
        for c in candidates:
            if (c / "tasks.md").exists():
                return c
        for c in candidates:
            if (c / "spec.md").exists():
                return c
        return candidates[0]

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = _repo_root()
        project_dir = self._project_dir(ctx)
        feature_dir = self._feature_dir(project_dir)
        if feature_dir is None:
            raise FileNotFoundError(f"no specs/ feature dir in {project_dir}")

        spec_text = _read_optional(feature_dir / "spec.md")
        plan_text = _read_optional(feature_dir / "plan.md")
        tasks_text = _read_optional(feature_dir / "tasks.md")
        code_summary = _summarize_tree(project_dir / "code")
        data_summary = _summarize_tree(project_dir / "data")
        results_summary = _read_optional(project_dir / "results.md")

        # Prior research-stage reviews (if any).
        prior = reviews_store.list_for(ctx.project_id, stage="research", repo_root=repo)
        prior_block = (
            "\n\n".join(
                f"- {r.reviewer_name} ({r.reviewer_kind.value}): {r.verdict} — {r.feedback[:120]}"
                for r in prior
            )
            or "(no prior reviews)"
        )

        # Use the registry entry's prompt_path so specialist reviewers
        # (research_reviewer_idea_quality, _creativity, etc.) load
        # their own focused prompts. The generic research_reviewer
        # agent falls back to agents/prompts/research_reviewer.md.
        prompt_path = self.entry.prompt_path or "agents/prompts/research_reviewer.md"
        system = render_prompt(
            prompt_path,
            {"project_id": ctx.project_id, "reviewer_name": self.entry.name},
            repo_root=repo,
        )
        user = (
            f"# project_id\n{ctx.project_id}\n\n"
            f"# spec.md\n\n{spec_text}\n\n"
            f"# plan.md\n\n{plan_text}\n\n"
            f"# tasks.md\n\n{tasks_text}\n\n"
            f"# code summary\n\n{code_summary}\n\n"
            f"# data summary\n\n{data_summary}\n\n"
            f"# results summary\n\n{results_summary}\n\n"
            f"# prior reviews\n\n{prior_block}\n\n"
            "# Task\n\nReturn the review record per the contract."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = _repo_root()
        text = response.text.strip()
        match = _FRONTMATTER_RE.match(text)
        if not match:
            raise MalformedResponseError(
                "research_reviewer: response missing YAML frontmatter",
                format_reminder=_FORMAT_REMINDER,
            )
        try:
            front = yaml.safe_load(match.group("frontmatter"))
        except yaml.YAMLError as exc:
            raise MalformedResponseError(
                f"research_reviewer: frontmatter is not valid YAML ({exc})",
                format_reminder=_FORMAT_REMINDER,
            ) from exc
        body = match.group("body").strip()
        if not isinstance(front, dict):
            raise MalformedResponseError(
                "research_reviewer: frontmatter must be a YAML mapping",
                format_reminder=_FORMAT_REMINDER,
            )

        # Force the runtime-known fields onto the record (LLM may echo
        # placeholder values that we replace authoritatively).
        front["reviewer_name"] = self.entry.name
        front["reviewer_kind"] = ReviewerKind.LLM.value
        front["model_name"] = response.model
        front["backend"] = response.backend
        front["prompt_version"] = self.entry.prompt_version
        front["reviewed_at"] = datetime.now(UTC).isoformat()

        # Compute the artifact_hash from the live tasks.md.
        project_dir = self._project_dir(ctx)
        feature_dir = self._feature_dir(project_dir)
        if feature_dir is not None:
            tasks_path = feature_dir / "tasks.md"
            if tasks_path.exists():
                from llmxive.state.project import hash_file

                front["artifact_hash"] = hash_file(tasks_path)
                front["artifact_path"] = str(tasks_path.relative_to(repo))

        try:
            record = ReviewRecord.model_validate(front)
        except ValidationError as exc:
            raise MalformedResponseError(
                f"research_reviewer: frontmatter failed ReviewRecord schema "
                f"validation: {exc}",
                format_reminder=_FORMAT_REMINDER,
            ) from exc

        # Self-review prevention (discrepancy #7 / #49): resolve the agent that
        # actually produced the reviewed artifact from the run-log so
        # reviews_store refuses a reviewer reviewing its own output. (For the
        # research panel the producer is the tasker/implementer — disjoint from
        # the research_reviewer* names — so this is defense-in-depth; None when
        # the run-log has no record of the artifact, preserving prior behavior.)
        producer = runlog_store.producer_of_artifact(
            ctx.project_id, record.artifact_path, repo_root=repo
        )
        path = reviews_store.write(
            record,
            body=body,
            stage="research",
            review_type="research",
            produced_by_agent=producer,
            repo_root=repo,
        )
        return [str(path.relative_to(repo))]


__all__ = ["ResearchReviewerAgent"]
