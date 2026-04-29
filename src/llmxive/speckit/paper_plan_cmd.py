"""Paper-Planner Agent (T077) — drives /speckit.plan for the paper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.speckit.plan_cmd import _split_multi_file
from llmxive.speckit.runner import run_script
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


class PaperPlannerAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.plan"

    def _paper_dir(self, ctx: SlashCommandContext) -> Path:
        return ctx.project_dir / "paper"

    def _feature_dir(self, ctx: SlashCommandContext) -> Path:
        candidates = sorted(self._paper_dir(ctx).glob("specs/*/"))
        if not candidates:
            raise FileNotFoundError(f"no specs/ feature dir in {self._paper_dir(ctx)}")
        return candidates[0]

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        repo = ctx.project_dir.parent.parent
        paper_dir = self._paper_dir(ctx)
        feature_dir = self._feature_dir(ctx)
        script = paper_dir / ".specify" / "scripts" / "bash" / "setup-plan.sh"
        result = run_script(
            str(script.relative_to(repo)),
            "--json",
            cwd=paper_dir,
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
        paper_dir = self._paper_dir(ctx)
        spec_path = Path(mechanical_output["spec_path"])
        spec_text = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
        constitution_path = paper_dir / ".specify" / "memory" / "constitution.md"
        paper_constitution = (
            constitution_path.read_text(encoding="utf-8") if constitution_path.exists() else ""
        )
        plan_template_path = paper_dir / ".specify" / "templates" / "plan-template.md"
        plan_template = (
            plan_template_path.read_text(encoding="utf-8") if plan_template_path.exists() else ""
        )

        system = render_prompt(
            "agents/prompts/paper_planner.md",
            {"project_id": ctx.project_id},
            repo_root=repo,
        )
        user = (
            f"# Paper spec.md\n\n{spec_text}\n\n"
            f"# Paper constitution\n\n{paper_constitution}\n\n"
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


__all__ = ["PaperPlannerAgent"]
