"""Specifier Agent — drives /speckit.specify (T046).

Mechanical step: invokes the project's per-project
`.specify/scripts/bash/create-new-feature.sh --json --short-name <slug> "<desc>"`
to create the feature directory + branch and obtain the feature_dir
path.

LLM step: drafts `spec.md` from the fleshed-out idea using the
project's `spec-template.md` as the structural skeleton.

Stage transitions: `project_initialized` → `specified`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from llmxive.agents.prompts import load_prompt, render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.speckit.runner import run_script
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


class SpecifierAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.specify"

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        # Use the project's own per-project script (already in place after
        # Project-Initializer's init_speckit_in call).
        repo = ctx.project_dir.parent.parent  # projects/<id>/.. → repo
        script = ctx.project_dir / ".specify" / "scripts" / "bash" / "create-new-feature.sh"
        # Use a short-name derived from the project id (last hyphen-segment)
        short_name = ctx.project_id.split("-", 2)[-1]
        idea_path = ctx.project_dir / "idea"
        # Concatenate any idea Markdown files for the description.
        descriptions: list[str] = []
        if idea_path.is_dir():
            for md in sorted(idea_path.glob("*.md")):
                descriptions.append(md.read_text(encoding="utf-8"))
        if not descriptions:
            descriptions.append(f"Spec for project {ctx.project_id}")
        description = "\n\n".join(descriptions)[:4000]
        return run_script(  # type: ignore[return-value]
            str(script.relative_to(repo)),
            "--json",
            "--short-name",
            short_name,
            description,
            cwd=repo,
            expect_json=True,
        )  # type: ignore[no-any-return]

    def build_prompt(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
    ) -> list[ChatMessage]:
        repo = ctx.project_dir.parent.parent
        idea_md = ""
        idea_dir = ctx.project_dir / "idea"
        if idea_dir.is_dir():
            for md in sorted(idea_dir.glob("*.md")):
                idea_md += md.read_text(encoding="utf-8") + "\n\n"

        spec_template_path = ctx.project_dir / ".specify" / "templates" / "spec-template.md"
        spec_template = (
            spec_template_path.read_text(encoding="utf-8")
            if spec_template_path.exists()
            else ""
        )

        system = render_prompt(
            "agents/prompts/specifier.md",
            {
                "project_id": ctx.project_id,
                "branch_name": str(mechanical_output.get("BRANCH_NAME", "")),
                "feature_num": str(mechanical_output.get("FEATURE_NUM", "")),
                "feature_dir": str(mechanical_output.get("FEATURE_DIR", "")),
            },
            repo_root=repo,
        )
        user = (
            "# Idea Markdown\n\n"
            f"{idea_md}\n\n"
            "# Spec template (canonical Spec Kit)\n\n"
            f"{spec_template}\n\n"
            "# Task\n\n"
            "Produce the final spec.md content."
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
        feature_dir_str = mechanical_output.get("FEATURE_DIR", "")
        if not feature_dir_str:
            raise RuntimeError(
                f"create-new-feature.sh returned no FEATURE_DIR: {mechanical_output}"
            )
        feature_dir = Path(feature_dir_str)
        if not feature_dir.is_absolute():
            feature_dir = repo / feature_dir
        feature_dir.mkdir(parents=True, exist_ok=True)
        spec_path = feature_dir / "spec.md"
        spec_path.write_text(llm_response.text.strip() + "\n", encoding="utf-8")
        return [str(spec_path.relative_to(repo))]


__all__ = ["SpecifierAgent"]
