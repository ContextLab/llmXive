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
        # Spec-015 fix: resolve via the project's authoritative
        # speckit_paper_dir pointer (set by paper_specify_cmd) so a
        # convergence kickback plans against the CURRENT paper spec, not the
        # superseded first-glob one. SSoT: llmxive.speckit._feature_dir.
        from llmxive.speckit._feature_dir import resolve_feature_dir
        return resolve_feature_dir(ctx, paper=True)

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        paper_dir = self._paper_dir(ctx)
        feature_dir = self._feature_dir(ctx)
        script = paper_dir / ".specify" / "scripts" / "bash" / "setup-plan.sh"
        # Use absolute path so cwd doesn't double-prefix.
        result = run_script(
            str(script),
            "--json",
            cwd=paper_dir,
            expect_json=True,
        )
        return {
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
        from llmxive.speckit._comments_context import render_recent_comments_block
        comments_block = render_recent_comments_block(ctx.project_dir)
        user = (
            f"# Paper spec.md\n\n{spec_text}\n\n"
            f"# Paper constitution\n\n{paper_constitution}\n\n"
            f"# Plan template\n\n{plan_template}\n\n"
            + (comments_block + "\n\n" if comments_block else "")
            + "# Task\n\nProduce all five documents per the output contract."
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
        from llmxive.speckit._real_only_guard import guard_emit

        files = _split_multi_file(llm_response.text)
        written: list[str] = []
        for relpath, content in files.items():
            target = feature_dir / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content + "\n", encoding="utf-8")
            # FR-009: real-only guard for markdown artifacts
            if target.suffix == ".md":
                guard_emit(target, repo_root=repo)
            written.append(str(target.relative_to(repo)))

        # --- paper-plan convergence panel (spec-015 / #239) -----------------
        # The just-written paper plan.md + sibling docs are reviewed by the
        # live paper-plan panel (paper_structure / spec_section_coverage /
        # plan_constitution_consistency) via the convergence engine.
        self._run_paper_plan_panel(ctx, feature_dir, repo)
        return written

    def _run_paper_plan_panel(
        self,
        ctx: SlashCommandContext,
        feature_dir: Path,
        repo: Path,
    ) -> None:
        from llmxive.backends.router import make_backend
        from llmxive.convergence.reviewspecs import build_paper_plan_reviewspec
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

        artifact_paths: dict[str, Path] = {}
        for name in ("plan.md", "research.md", "data-model.md", "quickstart.md"):
            p = feature_dir / name
            if p.exists():
                artifact_paths[str(p.relative_to(repo))] = p
        for c in sorted((feature_dir / "contracts").glob("*")):
            if c.is_file():
                artifact_paths[str(c.relative_to(repo))] = c
        # PaperPlanReviser reads the paper source spec from a key ending
        # 'spec.md' under 'paper/specs/'; include it.
        spec_path = feature_dir / "spec.md"
        if spec_path.exists():
            artifact_paths[str(spec_path.relative_to(repo))] = spec_path

        memory_dir = ctx.project_dir / "paper" / ".specify" / "memory"
        constitution_text = _read(memory_dir / "constitution.md") or None
        spec = build_paper_plan_reviewspec(
            backend=backend, repo_root=repo, project_id=ctx.project_id,
            model=ctx.default_model,
        )
        run_stage_panel(
            stage_label="paper_plan",
            spec=spec,
            artifact_paths=artifact_paths,
            extra_inputs={
                "__constitution__": constitution_text or "",
                "__comments_block__": render_recent_comments_block(ctx.project_dir),
                "__spec_md__": _read(spec_path),
            },
            repo_root=repo,
            memory_dir=memory_dir,
            producer="paper_planner",
            constitution=constitution_text,
        )


__all__ = ["PaperPlannerAgent"]
