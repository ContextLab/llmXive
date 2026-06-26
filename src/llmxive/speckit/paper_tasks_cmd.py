"""Paper-Tasker Agent (T079) — drives /speckit.tasks + /speckit.analyze for the paper.

Reuses the research-stage Tasker's analyze-resolve loop infrastructure.
The paper-specific prompt (agents/prompts/paper_tasker.md) requires
every task line to include a `[kind:<value>]` token so the
Paper-Implementer dispatcher can route tasks to the right sub-agent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.speckit.analyze_cmd import run_analyze
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


class PaperTaskerAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.tasks"

    def _paper_dir(self, ctx: SlashCommandContext) -> Path:
        return ctx.project_dir / "paper"

    def _feature_dir(self, ctx: SlashCommandContext) -> Path:
        # Spec-015 fix: resolve via the project's authoritative
        # speckit_paper_dir pointer so a convergence kickback builds paper
        # tasks against the CURRENT paper spec, not the superseded first-glob
        # one. SSoT: llmxive.speckit._feature_dir.
        from llmxive.speckit._feature_dir import resolve_feature_dir
        return resolve_feature_dir(ctx, paper=True)

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
        from llmxive.speckit._comments_context import render_recent_comments_block
        comments_block = render_recent_comments_block(ctx.project_dir)
        user = (
            "Mode: A (generate paper tasks.md)\n\n"
            f"# Paper spec.md\n\n{spec_text}\n\n"
            f"# Paper plan.md\n\n{plan_text}\n\n"
            f"# Tasks template\n\n{tasks_template}\n\n"
            + (comments_block + "\n\n" if comments_block else "")
            + "# Task\n\nReturn the full paper tasks.md Markdown. "
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
        # Defect #21: capture any existing tasks.md so a guard refusal
        # restores it instead of leaving no file on disk.
        prior_tasks = (
            tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else None
        )
        tasks_path.write_text(llm_response.text.strip() + "\n", encoding="utf-8")
        # FR-009: real-only guard — refuse template tasks emissions
        from llmxive.speckit._real_only_guard import guard_emit
        guard_emit(tasks_path, repo_root=repo, previous_content=prior_tasks)
        written = [str(tasks_path.relative_to(repo))]

        spec_path = Path(mechanical_output["spec_path"])
        plan_path = Path(mechanical_output["plan_path"])
        # Spec 015 T031 (discrepancy #4) + FR-030: paper analyze now uses a
        # paper-appropriate prompt (not the reused research tasker.md), and the
        # paper's constitution is included as a panel input.
        _paper_const_path = (
            self._paper_dir(ctx) / ".specify" / "memory" / "constitution.md"
        )
        _paper_const_text = (
            _paper_const_path.read_text(encoding="utf-8")
            if _paper_const_path.exists()
            else None
        )
        # Run the SAME shared convergence engine as every other review stage
        # (Constitution I + VI — one mechanism, never re-implemented per gate). The
        # live paper-tasks panel (coverage / ordering / executability /
        # constraint_preservation lenses + its reviser) does round-1 identify,
        # round-2 revise, and round-3 CLOSED-SET sign-off, and emits the kickback
        # itself on non-convergence. A single analyze pass supplies the
        # cross-artifact report as panel context. This REPLACES the legacy
        # Mode-A/Mode-B analyze-revise loop that re-implemented review/revise for
        # this one stage and re-critiqued OPEN-SET every round (the moving-goalposts
        # non-convergence #60 fixes engine-wide); non-convergence is now a kickback
        # (consistent with every other stage), not a bespoke human-input escalation.
        report = run_analyze(
            spec_text=spec_path.read_text(encoding="utf-8"),
            plan_text=plan_path.read_text(encoding="utf-8"),
            tasks_text=tasks_path.read_text(encoding="utf-8"),
            default_backend=ctx.default_backend,
            fallback_backends=ctx.fallback_backends,
            default_model=ctx.default_model,
            repo_root=repo,
            project_dir=ctx.project_dir,
            kind="paper",
            constitution_text=_paper_const_text,
        )
        self._run_paper_tasks_panel(
            ctx, spec_path, plan_path, tasks_path, repo,
            analyze_report_text=str(report),
        )
        return written

    def _run_paper_tasks_panel(
        self,
        ctx: SlashCommandContext,
        spec_path: Path,
        plan_path: Path,
        tasks_path: Path,
        repo: Path,
        *,
        analyze_report_text: str,
    ) -> None:
        from llmxive.backends.router import make_backend
        from llmxive.convergence.reviewspecs import build_paper_tasks_reviewspec
        from llmxive.speckit._stage_panel import (
            _read,
            render_recent_comments_block,
            run_stage_panel,
        )

        try:
            backend = make_backend(ctx.default_backend.value)
        except Exception:
            backend = None
        if backend is None:
            return  # offline / no-LLM: agent already produced the artifacts.

        memory_dir = self._paper_dir(ctx) / ".specify" / "memory"
        constitution_text = _read(memory_dir / "constitution.md") or None
        spec = build_paper_tasks_reviewspec(
            backend=backend, repo_root=repo, project_id=ctx.project_id,
            model=ctx.default_model,
        )
        artifact_paths: dict[str, Path] = {
            str(tasks_path.relative_to(repo)): tasks_path,
        }
        # Context artifacts the reviser reads by suffix (paper-side keys).
        for p in (spec_path, plan_path):
            if p.exists():
                artifact_paths[str(p.relative_to(repo))] = p
        run_stage_panel(
            stage_label="paper_tasks",
            spec=spec,
            artifact_paths=artifact_paths,
            extra_inputs={
                "__analyze_report__": analyze_report_text,
                "__prior_reviews__": "",
                "__constitution__": constitution_text or "",
                "__comments_block__": render_recent_comments_block(ctx.project_dir),
                "__spec_md__": _read(spec_path),
                "__plan_md__": _read(plan_path),
            },
            repo_root=repo,
            memory_dir=memory_dir,
            producer="paper_tasker",
            constitution=constitution_text,
        )


__all__ = ["PaperTaskerAgent"]
