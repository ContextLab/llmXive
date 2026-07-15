"""Writing-Agent (T081).

Composes one section/subsection of LaTeX prose. Writes to
`projects/<PROJ-ID>/paper/source/<section>.tex`.

Stage transitions: none (this is a sub-agent invoked by the
Paper-Implementer dispatcher; stage transitions happen at the
dispatcher level after every task in tasks.md is complete).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.config import repo_root as _repo_root
from llmxive.speckit.yaml_extract import parse_yaml_lenient
from llmxive.state.project import feature_dir_for


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


class PaperWritingAgent(Agent):
    """Handles [kind:prose] tasks routed by the Paper-Implementer dispatcher."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        repo = _repo_root()
        project_dir = repo / "projects" / ctx.project_id
        paper_dir = project_dir / "paper"

        target_section = ctx.metadata.get("target_section", "")
        target_path_rel = ctx.metadata.get("target_path", "")
        target_path = repo / target_path_rel if target_path_rel else None

        # Pull paper-stage spec + plan + research-stage results. Resolve the
        # CURRENT paper feature dir via the canonical pointer-first selector
        # (state.project.feature_dir_for) rather than the first/oldest
        # ``specs/*/`` glob: on a project that cycled through kickbacks the
        # first-sorted dir is the STALE prior cycle, so the writer would compose
        # against a superseded spec/plan (spec 023 defect #17).
        paper_feature_dir = feature_dir_for(project_dir, track="paper")
        paper_spec_text = (
            _read_optional(paper_feature_dir / "spec.md") if paper_feature_dir else ""
        )
        paper_plan_text = (
            _read_optional(paper_feature_dir / "plan.md") if paper_feature_dir else ""
        )
        constitution = paper_dir / ".specify" / "memory" / "constitution.md"
        paper_constitution = _read_optional(constitution)
        results_summary = _read_optional(project_dir / "results.md")
        existing = _read_optional(target_path) if target_path else ""

        system = render_prompt(
            "agents/prompts/paper_writing.md",
            {
                "project_id": ctx.project_id,
                "target_section": target_section,
                "target_path": target_path_rel,
            },
            repo_root=repo,
        )
        user = (
            f"# task_id\n{ctx.task_id}\n\n"
            f"# task_description\n{ctx.metadata.get('task_description', '')}\n\n"
            f"# Paper spec.md\n\n{paper_spec_text}\n\n"
            f"# Paper plan.md\n\n{paper_plan_text}\n\n"
            f"# Paper constitution\n\n{paper_constitution}\n\n"
            f"# Research-stage results summary\n\n{results_summary}\n\n"
            f"# Existing section text\n\n{existing}\n\n"
            "# Task\n\nReturn the YAML document per the contract."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        repo = _repo_root()
        try:
            doc = parse_yaml_lenient(response.text)
        except yaml.YAMLError as exc:
            raise RuntimeError(f"Writing-Agent returned invalid YAML: {exc}") from exc
        if not isinstance(doc, dict):
            raise RuntimeError("Writing-Agent YAML must be a mapping")
        if doc.get("verdict") != "completed":
            return []
        artifact = doc.get("artifact") or {}
        relpath = artifact.get("path", "")
        contents = artifact.get("contents", "")
        if not relpath:
            return []
        target = repo / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents, encoding="utf-8")
        return [relpath]


__all__ = ["PaperWritingAgent"]
