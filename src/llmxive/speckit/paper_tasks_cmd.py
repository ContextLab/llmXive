"""Paper-Tasker Agent (T079) — drives /speckit.tasks + /speckit.analyze for the paper.

Reuses the research-stage Tasker's analyze-resolve loop infrastructure.
The paper-specific prompt (agents/prompts/paper_tasker.md) requires
every task line to include a `[kind:<value>]` token so the
Paper-Implementer dispatcher can route tasks to the right sub-agent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.backends.router import chat_with_fallback
from llmxive.config import TASKER_MAX_REVISION_ROUNDS
from llmxive.speckit.analyze_cmd import is_clean, run_analyze
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


class PaperTaskerAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.tasks"

    def _paper_dir(self, ctx: SlashCommandContext) -> Path:
        return ctx.project_dir / "paper"

    def _feature_dir(self, ctx: SlashCommandContext) -> Path:
        candidates = sorted(self._paper_dir(ctx).glob("specs/*/"))
        if not candidates:
            raise FileNotFoundError(f"no paper specs/ feature dir in {ctx.project_dir}/paper/")
        return candidates[0]

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        feature_dir = self._feature_dir(ctx)
        return {
            "feature_dir": str(feature_dir),
            "spec_path": str(feature_dir / "spec.md"),
            "plan_path": str(feature_dir / "plan.md"),
            "tasks_path": str(feature_dir / "tasks.md"),
            "tasks_template_path": str(
                self._paper_dir(ctx) / ".specify" / "templates" / "tasks-template.md"
            ),
        }

    def build_prompt(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
    ) -> list[ChatMessage]:
        repo = ctx.project_dir.parent.parent
        spec_text = Path(mechanical_output["spec_path"]).read_text(encoding="utf-8")
        plan_text = Path(mechanical_output["plan_path"]).read_text(encoding="utf-8")
        tasks_template_path = Path(mechanical_output["tasks_template_path"])
        tasks_template = (
            tasks_template_path.read_text(encoding="utf-8") if tasks_template_path.exists() else ""
        )
        system = render_prompt(
            "agents/prompts/paper_tasker.md",
            {"project_id": ctx.project_id, "mode": "A"},
            repo_root=repo,
        )
        user = (
            "Mode: A (generate paper tasks.md)\n\n"
            f"# Paper spec.md\n\n{spec_text}\n\n"
            f"# Paper plan.md\n\n{plan_text}\n\n"
            f"# Tasks template\n\n{tasks_template}\n\n"
            "# Task\n\nReturn the full paper tasks.md Markdown. "
            "EVERY task line MUST include a `[kind:<value>]` token."
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
        tasks_path = Path(mechanical_output["tasks_path"])
        tasks_path.parent.mkdir(parents=True, exist_ok=True)
        tasks_path.write_text(llm_response.text.strip() + "\n", encoding="utf-8")
        written = [str(tasks_path.relative_to(repo))]

        spec_path = Path(mechanical_output["spec_path"])
        plan_path = Path(mechanical_output["plan_path"])
        for round_idx in range(TASKER_MAX_REVISION_ROUNDS):
            report = run_analyze(
                spec_text=spec_path.read_text(encoding="utf-8"),
                plan_text=plan_path.read_text(encoding="utf-8"),
                tasks_text=tasks_path.read_text(encoding="utf-8"),
                default_backend=ctx.default_backend,
                fallback_backends=ctx.fallback_backends,
                default_model=ctx.default_model,
                repo_root=repo,
            )
            if is_clean(report):
                round_record = (
                    self._paper_dir(ctx) / ".specify" / "memory" / "tasker_rounds.yaml"
                )
                round_record.parent.mkdir(parents=True, exist_ok=True)
                round_record.write_text(
                    yaml.safe_dump({"rounds_used": round_idx + 1}),
                    encoding="utf-8",
                )
                return written

            mode_b_system = render_prompt(
                "agents/prompts/paper_tasker.md",
                {"project_id": ctx.project_id, "mode": "B"},
                repo_root=repo,
            )
            mode_b_user = (
                "Mode: B (resolve paper analyze findings)\n\n"
                f"# Analyze report\n\n{report}\n\n"
                f"# spec.md\n\n{spec_path.read_text(encoding='utf-8')}\n\n"
                f"# plan.md\n\n{plan_path.read_text(encoding='utf-8')}\n\n"
                f"# tasks.md\n\n{tasks_path.read_text(encoding='utf-8')}\n\n"
                "Return the YAML patch document per the contract."
            )
            patch_response = chat_with_fallback(
                [
                    ChatMessage(role="system", content=mode_b_system),
                    ChatMessage(role="user", content=mode_b_user),
                ],
                default_backend=ctx.default_backend.value,
                fallback_backends=[b.value for b in ctx.fallback_backends],
                model=ctx.default_model,
            )
            try:
                doc = yaml.safe_load(patch_response.text)
            except yaml.YAMLError:
                continue
            if not isinstance(doc, dict):
                continue
            for issue in doc.get("issues_resolved", []) or []:
                f = issue.get("file")
                patch = issue.get("patch", "")
                if f == "spec.md":
                    spec_path.write_text(patch, encoding="utf-8")
                elif f == "plan.md":
                    plan_path.write_text(patch, encoding="utf-8")
                elif f == "tasks.md":
                    tasks_path.write_text(patch, encoding="utf-8")
            if doc.get("verdict") == "escalate":
                escalate_marker = (
                    self._paper_dir(ctx) / ".specify" / "memory" / "human_input_needed.yaml"
                )
                escalate_marker.parent.mkdir(parents=True, exist_ok=True)
                escalate_marker.write_text(
                    yaml.safe_dump({"reason": "paper tasker analyze did not converge",
                                    "rounds_used": round_idx + 1}),
                    encoding="utf-8",
                )
                return written

        escalate_marker = (
            self._paper_dir(ctx) / ".specify" / "memory" / "human_input_needed.yaml"
        )
        escalate_marker.parent.mkdir(parents=True, exist_ok=True)
        escalate_marker.write_text(
            yaml.safe_dump({"reason": "paper tasker reached max rounds",
                            "rounds_used": TASKER_MAX_REVISION_ROUNDS}),
            encoding="utf-8",
        )
        return written


__all__ = ["PaperTaskerAgent"]
