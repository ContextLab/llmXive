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

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.speckit.runner import run_script
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


def _find_prior_spec(*, current_feature_dir: Path) -> Path | None:
    """Locate the prior mature spec.md to revise from (spec-015 fix).

    On a post-kickback REGENERATION the convergence graph routes
    spec → flesh_out → project_initialize → specify, and ``create-new-feature.sh``
    mints a fresh ``specs/NNN-*`` dir (``current_feature_dir``) for THIS run.
    The mature spec the panel already converged toward lives in a
    lower-numbered sibling. Regenerating from scratch ignores it and ratchets
    quality DOWN; instead we feed that prior spec back in as a revision base.

    Returns the highest-numbered ``specs/NNN-*/spec.md`` that is:

    * a sibling of ``current_feature_dir`` (same ``specs/`` parent),
    * NOT ``current_feature_dir`` itself (the dir this run writes to), and
    * non-empty (more than whitespace).

    Returns ``None`` for a genuine first-time spec (no such sibling), in which
    case the Specifier's behavior is UNCHANGED.
    """
    specs_root = current_feature_dir.parent
    if not specs_root.is_dir():
        return None
    current = current_feature_dir.resolve()
    candidates = sorted(
        d for d in specs_root.glob("*/") if d.is_dir() and d.resolve() != current
    )
    for d in reversed(candidates):
        spec_md = d / "spec.md"
        if spec_md.is_file() and spec_md.read_text(encoding="utf-8").strip():
            return spec_md
    return None


class SpecifierAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.specify"

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        # The per-project create-new-feature.sh resolves spec dirs
        # relative to the cwd the script is invoked from. To keep all
        # artifacts under projects/<id>/ we MUST run with cwd=project_dir
        # — running with cwd=repo causes specs to land at the repo root.
        script = ctx.project_dir / ".specify" / "scripts" / "bash" / "create-new-feature.sh"
        short_name = ctx.project_id.split("-", 2)[-1]
        idea_path = ctx.project_dir / "idea"
        descriptions: list[str] = []
        if idea_path.is_dir():
            for md in sorted(idea_path.glob("*.md")):
                descriptions.append(md.read_text(encoding="utf-8"))
        if not descriptions:
            descriptions.append(f"Spec for project {ctx.project_id}")
        description = "\n\n".join(descriptions)[:4000]
        out = run_script(
            str(script),
            "--json",
            "--short-name",
            short_name,
            description,
            cwd=ctx.project_dir,
            expect_json=True,
        )
        # Older scripts emit only SPEC_FILE; older code expects FEATURE_DIR.
        # Synthesize it from SPEC_FILE so write_artifacts has what it needs.
        if isinstance(out, dict) and "FEATURE_DIR" not in out and out.get("SPEC_FILE"):
            out["FEATURE_DIR"] = str(Path(out["SPEC_FILE"]).parent)
        return out  # type: ignore[return-value]

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
        # Spec 011 / FR-013: inject recent personality + reviewer
        # comments into the user prompt so the agent's output reflects
        # accumulated feedback (single source of truth — every speckit
        # command pulls this from `_comments_context.render_recent_comments_block`).
        from llmxive.speckit._comments_context import render_recent_comments_block
        comments_block = render_recent_comments_block(ctx.project_dir)

        # Spec-015 fix: on a post-kickback REGENERATION (the realigned idea is
        # re-specified into a fresh specs/NNN dir), seed from the PRIOR mature
        # spec so convergence improves monotonically instead of ratcheting
        # quality down. First-time specs (no prior non-empty spec) are UNCHANGED.
        revision_block = ""
        feature_dir_str = str(mechanical_output.get("FEATURE_DIR", ""))
        if feature_dir_str:
            current_feature_dir = Path(feature_dir_str)
            if not current_feature_dir.is_absolute():
                current_feature_dir = repo / current_feature_dir
            prior_spec = _find_prior_spec(current_feature_dir=current_feature_dir)
            if prior_spec is not None:
                prior_text = prior_spec.read_text(encoding="utf-8")
                revision_block = (
                    "# Prior spec (revision base)\n\n"
                    "A prior version of this spec already exists below. The idea "
                    "has been realigned to address a review concern, so you are "
                    "RE-specifying — not starting fresh. Produce the spec by "
                    "REVISING the prior version: preserve EVERY still-valid "
                    "functional requirement, success criterion, edge case, key "
                    "entity, and already-resolved clarification. Do NOT drop "
                    "detail. Do NOT re-introduce `[NEEDS CLARIFICATION]` for "
                    "anything the prior spec already resolved. Only change what "
                    "the realigned idea actually requires. The result MUST be at "
                    "least as complete as the prior spec (no fewer requirements "
                    "or success criteria unless the realigned idea explicitly "
                    "removes that scope).\n\n"
                    "```markdown\n"
                    f"{prior_text.strip()}\n"
                    "```\n\n"
                )

        # Trustworthiness Phase 2: feed canonical verified facts back into the
        # generation agent so it cites the verified value (and never invents a
        # contradicting one). Pure addition — empty string when no facts exist,
        # keeping a fact-free prompt BYTE-IDENTICAL to before.
        from llmxive.claims.verified_facts_prompt import (
            load_verified_facts,
            render_verified_facts_block,
        )
        verified_facts_block = render_verified_facts_block(
            load_verified_facts(ctx.project_dir)
        )

        user = (
            "# Idea Markdown\n\n"
            f"{idea_md}\n\n"
            "# Spec template (canonical Spec Kit)\n\n"
            f"{spec_template}\n\n"
            + revision_block
            + (comments_block + "\n\n" if comments_block else "")
            + (verified_facts_block + "\n\n" if verified_facts_block else "")
            + "# Task\n\n"
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
        # Spec 010 fix: refuse LLM responses that returned a diff. Without
        # this guard, polluted files like:
        #     --- a/spec.md
        #     +++ b/spec.md
        #     @@ -1,N +1,N @@
        # got written verbatim. 8 production files were affected before this
        # tightened.
        from llmxive.speckit._diff_guard import refuse_if_diff
        refuse_if_diff(llm_response.text, artifact_kind="spec.md")
        spec_path.write_text(llm_response.text.strip() + "\n", encoding="utf-8")

        # Spec 009 FR-009 + FR-010: real-only guard. If the emitter produced a
        # template-classified artifact, delete it, log the actionable error,
        # and DO NOT advance project progression points (SC-004).
        from llmxive.speckit._real_only_guard import (
            TemplateRefused,
            assert_real_or_raise,
        )
        try:
            assert_real_or_raise(spec_path, repo_root=repo)
        except TemplateRefused as exc:
            spec_path.unlink(missing_ok=True)
            import logging
            logging.getLogger(__name__).error(
                "speckit specify refused template emission: %s", exc
            )
            raise

        # Persist speckit_research_dir on project state so the Project
        # validator allows the `specified` stage. The directory is
        # stored relative to the repo root.
        from llmxive.state import project as project_store
        project = project_store.load(ctx.project_id, repo_root=repo)
        rel_feature_dir = str(feature_dir.resolve().relative_to(repo.resolve()))
        if project.speckit_research_dir != rel_feature_dir:
            project.speckit_research_dir = rel_feature_dir
            project_store.save(project, repo_root=repo)
        return [str(spec_path.relative_to(repo))]


__all__ = ["SpecifierAgent", "_find_prior_spec"]
