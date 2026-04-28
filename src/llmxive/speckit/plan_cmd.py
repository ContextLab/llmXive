"""Planner Agent — drives /speckit.plan (T050).

Mechanical step: invokes per-project
`.specify/scripts/bash/setup-plan.sh --json` and parses output.

LLM step: produces five Markdown documents (plan.md, research.md,
data-model.md, quickstart.md, contracts/<schema>.schema.yaml) in a
single response separated by `<!-- FILE: <path> -->` markers, which
this agent splits and writes to canonical Spec Kit paths.

Stage transitions: `clarified` → `planned`.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.speckit.runner import run_script
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


_FILE_MARKER_RE = re.compile(
    r"<!--\s*FILE:\s*(?P<path>[^\s]+)\s*-->\s*\n",
    re.IGNORECASE,
)


def _split_multi_file(text: str) -> dict[str, str]:
    """Return mapping of relative path → content from a multi-file LLM reply."""
    parts: dict[str, str] = {}
    matches = list(_FILE_MARKER_RE.finditer(text))
    if not matches:
        # Single-file reply; assume plan.md.
        return {"plan.md": text.strip()}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        parts[m.group("path").strip()] = text[start:end].strip()
    return parts


class PlannerAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.plan"

    def _feature_dir(self, ctx: SlashCommandContext) -> Path:
        candidates = sorted(ctx.project_dir.glob("specs/*/"))
        if not candidates:
            raise FileNotFoundError(f"no specs/ feature directory in {ctx.project_dir}")
        return candidates[0]

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        repo = ctx.project_dir.parent.parent
        feature_dir = self._feature_dir(ctx)
        script = ctx.project_dir / ".specify" / "scripts" / "bash" / "setup-plan.sh"
        # setup-plan.sh expects to be run inside the feature dir's parent
        # context; pass the feature_dir as cwd metadata for the LLM but
        # invoke from project root.
        result = run_script(
            str(script.relative_to(repo)),
            "--json",
            cwd=ctx.project_dir,
            expect_json=True,
        )
        return {  # type: ignore[no-any-return]
            "feature_dir": str(feature_dir),
            "spec_path": str(feature_dir / "spec.md"),
            "script_result": result,
        }

    def build_prompt(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
    ) -> list[ChatMessage]:
        repo = ctx.project_dir.parent.parent
        spec_path = Path(mechanical_output["spec_path"])
        spec_text = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
        constitution_path = ctx.project_dir / ".specify" / "memory" / "constitution.md"
        project_constitution = (
            constitution_path.read_text(encoding="utf-8")
            if constitution_path.exists()
            else ""
        )
        plan_template_path = ctx.project_dir / ".specify" / "templates" / "plan-template.md"
        plan_template = (
            plan_template_path.read_text(encoding="utf-8")
            if plan_template_path.exists()
            else ""
        )

        system = render_prompt(
            "agents/prompts/planner.md",
            {"project_id": ctx.project_id},
            repo_root=repo,
        )
        user = (
            f"# spec.md\n\n{spec_text}\n\n"
            f"# Project constitution\n\n{project_constitution}\n\n"
            f"# Plan template\n\n{plan_template}\n\n"
            "# Task\n\nProduce all five documents per the output contract."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def write_artifacts(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
        llm_response: ChatResponse,
    ) -> list[str]:
        repo = ctx.project_dir.parent.parent
        feature_dir = Path(mechanical_output["feature_dir"])
        if not feature_dir.is_absolute():
            feature_dir = repo / feature_dir
        feature_dir.mkdir(parents=True, exist_ok=True)

        files = _split_multi_file(llm_response.text)
        written: list[str] = []
        for relpath, content in files.items():
            target = feature_dir / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content + "\n", encoding="utf-8")
            written.append(str(target.relative_to(repo)))
        return written


__all__ = ["PlannerAgent"]
