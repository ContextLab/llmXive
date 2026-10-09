"""Paper-Planner Agent (T077) — drives /speckit.plan for the paper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage
from llmxive.speckit.plan_cmd import PlannerAgent
from llmxive.speckit.runner import run_script
from llmxive.speckit.slash_command import SlashCommandContext


class PaperPlannerAgent(PlannerAgent):
    def slash_command_name(self) -> str:
        return "speckit.plan"

    def claim_stage_label(self) -> str | None:
        # Paper claims require full evidence checks, unlike research planning.
        return None

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
        feature_dir.resolve().relative_to(paper_dir.resolve())
        plan_path = feature_dir / "plan.md"
        if plan_path.is_file():
            result = {"FEATURE_SPEC": str(feature_dir / "spec.md"),
                      "IMPL_PLAN": str(plan_path), "SPECS_DIR": str(feature_dir)}
        else:
            script = (paper_dir / ".specify/scripts/bash/setup-plan.sh").resolve()
            result = run_script(
                str(script), "--json", cwd=paper_dir, expect_json=True,
                extra_env={"SPECIFY_FEATURE_DIRECTORY": str(feature_dir.resolve()),
                           "SPECIFY_FEATURE": feature_dir.name},
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
        feature_dir = Path(mechanical_output["feature_dir"])
        existing = []
        remaining = 80_000
        paths = [feature_dir / name for name in
                 ("plan.md", "research.md", "data-model.md", "quickstart.md")]
        paths.extend(sorted((feature_dir / "contracts").glob("*")))
        for path in paths:
            if not path.is_file() or path.suffix not in {".md", ".yaml", ".yml", ".json"}:
                continue
            text = path.read_text(encoding="utf-8")
            if len(text) <= remaining:
                existing.append(f"### {path.relative_to(feature_dir)}\n\n{text}")
                remaining -= len(text)
            else:
                existing.append(f"### {path.relative_to(feature_dir)} (not loaded: context budget)")
        existing_block = ("# Existing paper planning artifacts\n\n"
                          "Revise these in place; preserve unaffected scientific requirements, "
                          "methods, figure bindings and paths.\n\n" + "\n\n".join(existing)) if existing else ""
        user = (
            f"# Paper spec.md\n\n{spec_text}\n\n"
            f"# Paper constitution\n\n{paper_constitution}\n\n"
            f"# Plan template\n\n{plan_template}\n\n"
            + (existing_block + "\n\n" if existing_block else "")
            + (comments_block + "\n\n" if comments_block else "")
            + "# Task\n\nProduce all five documents per the output contract. "
            "FILE markers must be relative to the active paper feature directory: "
            "plan.md, research.md, data-model.md, quickstart.md and contracts/<name>.schema.yaml. "
            "Do not prefix markers with specs/, a feature slug, or a repository path."
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def _run_plan_panel(
        self, ctx: SlashCommandContext, feature_dir: Path, repo: Path,
    ) -> None:
        # Reuse the research planner's complete-set validation, confined writes,
        # rollback and bounded corrective retry, then keep the paper panel.
        self._run_paper_plan_panel(ctx, feature_dir, repo)

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
