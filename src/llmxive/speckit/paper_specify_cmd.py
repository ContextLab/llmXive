"""Paper-Specifier Agent (T073) — drives /speckit.specify for the paper.

Mirrors the research-stage Specifier but operates inside
`projects/<PROJ-ID>/paper/`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.speckit.runner import run_script
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


class PaperSpecifierAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.specify"

    def _paper_dir(self, ctx: SlashCommandContext) -> Path:
        return ctx.project_dir / "paper"

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        repo = ctx.project_dir.parent.parent
        paper_dir = self._paper_dir(ctx)
        script = paper_dir / ".specify" / "scripts" / "bash" / "create-new-feature.sh"
        short_name = "paper"
        # Description is the project's research-stage spec summary.
        descriptions: list[str] = []
        for sp in sorted(ctx.project_dir.glob("specs/*/spec.md")):
            descriptions.append(sp.read_text(encoding="utf-8"))
            break
        if not descriptions:
            descriptions.append(f"Paper for {ctx.project_id}")
        description = (descriptions[0] or "")[:4000]
        return run_script(  # type: ignore[return-value]
            str(script.relative_to(repo)),
            "--json",
            "--short-name",
            short_name,
            description,
            cwd=paper_dir,
            expect_json=True,
        )

    def build_prompt(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
    ) -> list[ChatMessage]:
        repo = ctx.project_dir.parent.parent
        paper_dir = self._paper_dir(ctx)
        # Pull research-stage artifacts to inform the paper spec.
        research_spec = ""
        research_plan = ""
        research_tasks = ""
        for sp in sorted(ctx.project_dir.glob("specs/*/spec.md")):
            research_spec = sp.read_text(encoding="utf-8")
            base = sp.parent
            plan_path = base / "plan.md"
            tasks_path = base / "tasks.md"
            if plan_path.exists():
                research_plan = plan_path.read_text(encoding="utf-8")
            if tasks_path.exists():
                research_tasks = tasks_path.read_text(encoding="utf-8")
            break

        spec_template_path = paper_dir / ".specify" / "templates" / "spec-template.md"
        spec_template = spec_template_path.read_text(encoding="utf-8") if spec_template_path.exists() else ""

        system = render_prompt(
            "agents/prompts/paper_specifier.md",
            {
                "project_id": ctx.project_id,
                "branch_name": str(mechanical_output.get("BRANCH_NAME", "")),
                "feature_num": str(mechanical_output.get("FEATURE_NUM", "")),
                "feature_dir": str(mechanical_output.get("FEATURE_DIR", "")),
            },
            repo_root=repo,
        )
        user = (
            f"# Research-stage spec.md\n\n{research_spec}\n\n"
            f"# Research-stage plan.md\n\n{research_plan}\n\n"
            f"# Research-stage tasks.md\n\n{research_tasks}\n\n"
            f"# Paper spec template\n\n{spec_template}\n\n"
            "# Task\n\nProduce the final paper-stage spec.md."
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


__all__ = ["PaperSpecifierAgent"]
