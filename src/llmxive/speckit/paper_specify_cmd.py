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

    def _research_spec_path(self, ctx: SlashCommandContext) -> Path | None:
        """Resolve the CURRENT research spec.md via the project pointer.

        Spec 023 defect #17 class: the old first-glob (`sorted(...)[0]`)
        picked the OLDEST specs/NNN dir — stale after any spec-cycle
        regeneration. SSoT: llmxive.speckit._feature_dir.
        """
        from llmxive.speckit._feature_dir import resolve_feature_dir
        try:
            spec_path = resolve_feature_dir(ctx) / "spec.md"
        except FileNotFoundError:
            return None
        return spec_path if spec_path.exists() else None

    def _reusable_feature_dir(self, ctx: SlashCommandContext) -> Path | None:
        """Return the pointer paper feature dir when it holds a mature spec.md.

        Spec 023 defect #19 (paper twin): a re-specify must revise IN
        PLACE, not mint a sibling paper/specs/NNN dir.
        """
        repo = ctx.project_dir.parent.parent
        from llmxive.state import project as project_store
        try:
            project = project_store.load(ctx.project_id, repo_root=repo)
        except FileNotFoundError:
            return None
        pointer = project.speckit_paper_dir
        if not pointer:
            return None
        candidate = repo / pointer
        spec_md = candidate / "spec.md"
        try:
            if spec_md.is_file() and spec_md.read_text(encoding="utf-8").strip():
                return candidate
        except OSError:
            return None
        return None

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        # Spec 023 defect #19 (paper twin): reuse the pointer dir on a
        # re-specify — see SpecifierAgent.mechanical_step for rationale.
        reused = self._reusable_feature_dir(ctx)
        if reused is not None:
            repo = ctx.project_dir.parent.parent
            return {
                "FEATURE_DIR": str(reused.relative_to(repo)),
                "BRANCH_NAME": "",
                "FEATURE_NUM": reused.name.split("-", 1)[0],
                "REUSED_FEATURE_DIR": True,
            }
        paper_dir = self._paper_dir(ctx)
        script = paper_dir / ".specify" / "scripts" / "bash" / "create-new-feature.sh"
        short_name = "paper"
        research_spec_path = self._research_spec_path(ctx)
        description = (
            research_spec_path.read_text(encoding="utf-8")
            if research_spec_path is not None
            else f"Paper for {ctx.project_id}"
        )[:4000]
        out = run_script(
            str(script),
            "--json",
            "--short-name",
            short_name,
            description,
            cwd=paper_dir,
            expect_json=True,
        )
        # Synthesize FEATURE_DIR from SPEC_FILE when missing.
        if isinstance(out, dict) and "FEATURE_DIR" not in out and out.get("SPEC_FILE"):
            out["FEATURE_DIR"] = str(Path(out["SPEC_FILE"]).parent)
        return out  # type: ignore[return-value]

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
        # Spec 023 defect #17 class: pointer-first resolution, not first-glob.
        research_spec_path = self._research_spec_path(ctx)
        if research_spec_path is not None:
            research_spec = research_spec_path.read_text(encoding="utf-8")
            base = research_spec_path.parent
            plan_path = base / "plan.md"
            tasks_path = base / "tasks.md"
            if plan_path.exists():
                research_plan = plan_path.read_text(encoding="utf-8")
            if tasks_path.exists():
                research_tasks = tasks_path.read_text(encoding="utf-8")

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
        from llmxive.speckit._comments_context import render_recent_comments_block
        comments_block = render_recent_comments_block(ctx.project_dir)
        # Spec 015 T033 (discrepancy #10): paper_specifier.md advertises
        # ``code_summary``/``data_summary`` inputs the code never supplied. Supply
        # them now (reusing research_reviewer._summarize_tree as the SSoT
        # tree-summary helper) so the prompt's advertised inputs ARE present.
        from llmxive.agents.research_reviewer import _summarize_tree
        code_summary = _summarize_tree(ctx.project_dir / "code")
        data_summary = _summarize_tree(ctx.project_dir / "data")
        # Spec 023 defect #19 (paper twin): on an in-place re-specify the
        # mature paper spec is the revision base — preserve it, don't
        # regenerate from scratch.
        revision_block = ""
        if mechanical_output.get("REUSED_FEATURE_DIR"):
            feature_dir = Path(str(mechanical_output.get("FEATURE_DIR", "")))
            if not feature_dir.is_absolute():
                feature_dir = repo / feature_dir
            own_spec = feature_dir / "spec.md"
            if own_spec.is_file():
                prior_text = own_spec.read_text(encoding="utf-8").strip()
                if prior_text:
                    revision_block = (
                        "# Prior paper spec (revision base)\n\n"
                        "A prior version of this paper spec already exists "
                        "below. You are RE-specifying — not starting fresh. "
                        "REVISE the prior version: preserve every still-valid "
                        "requirement, success criterion, and section; only "
                        "change what the feedback actually requires.\n\n"
                        "```markdown\n"
                        f"{prior_text}\n"
                        "```\n\n"
                    )
        user = (
            f"# Research-stage spec.md\n\n{research_spec}\n\n"
            f"# Research-stage plan.md\n\n{research_plan}\n\n"
            f"# Research-stage tasks.md\n\n{research_tasks}\n\n"
            f"# code_summary\n\n{code_summary}\n\n"
            f"# data_summary\n\n{data_summary}\n\n"
            f"# Paper spec template\n\n{spec_template}\n\n"
            + revision_block
            + (comments_block + "\n\n" if comments_block else "")
            + "# Task\n\nProduce the final paper-stage spec.md."
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
        # FR-009: real-only guard — refuse template paper spec emissions
        from llmxive.speckit._real_only_guard import guard_emit
        guard_emit(spec_path, repo_root=repo)
        # Persist speckit_paper_dir on project state so the validator
        # accepts the `paper_specified` stage transition.
        from llmxive.state import project as project_store
        project = project_store.load(ctx.project_id, repo_root=repo)
        rel = str(feature_dir.resolve().relative_to(repo.resolve()))
        if project.speckit_paper_dir != rel:
            project.speckit_paper_dir = rel
            project_store.save(project, repo_root=repo)
        return [str(spec_path.relative_to(repo))]


__all__ = ["PaperSpecifierAgent"]
