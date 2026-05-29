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
from llmxive.librarian.dataset_resolver import (
    render_planner_block,
    resolve_datasets,
    write_manifest,
)
from llmxive.speckit.runner import run_script
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext

_FILE_MARKER_RE = re.compile(
    r"<!--\s*FILE:\s*(?P<path>[^\s]+)\s*-->\s*\n",
    re.IGNORECASE,
)


_FENCE_LINE_RE = re.compile(r"^```[\w.-]*\s*$")


def _strip_wrapping_fences(content: str) -> str:
    """Strip markdown code fences the LLM commonly wraps around emitted file
    content. Two cases: (1) the whole file is wrapped (first line ```lang, last
    line ```), and (2) a stray unmatched fence (odd number of ``` lines), e.g. a
    trailing ``` appended after a YAML schema — which makes the file invalid
    YAML. A balanced set of fences (legit code blocks inside a .md) is left
    untouched."""
    c = content.strip()
    lines = c.splitlines()
    if (
        len(lines) >= 2
        and _FENCE_LINE_RE.match(lines[0].strip())
        and lines[-1].strip() == "```"
    ):
        return "\n".join(lines[1:-1]).strip()
    fence_idxs = [i for i, ln in enumerate(lines) if ln.strip().startswith("```")]
    if len(fence_idxs) % 2 == 1:  # unmatched stray fence
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        elif lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        return "\n".join(lines).strip()
    return c


def _split_multi_file(text: str) -> dict[str, str]:
    """Return mapping of relative path → content from a multi-file LLM reply."""
    parts: dict[str, str] = {}
    matches = list(_FILE_MARKER_RE.finditer(text))
    if not matches:
        # Single-file reply; assume plan.md.
        return {"plan.md": _strip_wrapping_fences(text)}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        parts[m.group("path").strip()] = _strip_wrapping_fences(text[start:end])
    return parts


class PlannerAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.plan"

    def _feature_dir(self, ctx: SlashCommandContext) -> Path:
        candidates = sorted(ctx.project_dir.glob("specs/*/"))
        if not candidates:
            raise FileNotFoundError(f"no specs/ feature directory in {ctx.project_dir}")
        for c in candidates:
            if (c / "tasks.md").exists():
                return c
        for c in candidates:
            if (c / "spec.md").exists():
                return c
        return candidates[0]

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        feature_dir = self._feature_dir(ctx)
        # Use absolute path so run_script (which joins with cwd) doesn't
        # produce a doubled projects/<id>/projects/<id>/... path.
        script = (ctx.project_dir / ".specify" / "scripts" / "bash" / "setup-plan.sh").resolve()
        result = run_script(
            str(script),
            "--json",
            cwd=ctx.project_dir,
            expect_json=True,
        )
        spec_path = feature_dir / "spec.md"
        spec_text = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
        resolved = resolve_datasets(
            spec_text,
            project_dir=ctx.project_dir,
            repo_root=ctx.project_dir.parent.parent,
        )
        write_manifest(resolved, project_dir=ctx.project_dir)
        return {  # type: ignore[no-any-return]
            "feature_dir": str(feature_dir),
            "spec_path": str(spec_path),
            "script_result": result,
            "dataset_block": render_planner_block(resolved),
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
        from llmxive.speckit._comments_context import render_recent_comments_block
        comments_block = render_recent_comments_block(ctx.project_dir)
        # Verified-datasets block: produced by mechanical_step in production.
        # When absent (e.g. a hand-built mechanical_output), resolve here so the
        # Planner still receives the cite-only block instead of nothing.
        dataset_block = mechanical_output.get("dataset_block")
        if dataset_block is None:
            resolved = resolve_datasets(
                spec_text,
                project_dir=ctx.project_dir,
                repo_root=repo,
            )
            dataset_block = render_planner_block(resolved)
        user = (
            f"# spec.md\n\n{spec_text}\n\n"
            f"# Project constitution\n\n{project_constitution}\n\n"
            f"# Plan template\n\n{plan_template}\n\n"
            + (dataset_block + "\n\n" if dataset_block else "")
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
        from llmxive.speckit._research_guard import (
            assert_artifact_set_complete,
            assert_data_model_contracts_consistent,
            assert_urls_reachable,
        )

        files = _split_multi_file(llm_response.text)

        # FR-005: fail closed on an incomplete/partial multi-file split BEFORE
        # any per-file work, so a malformed response never leaves partial
        # artifacts on disk.
        assert_artifact_set_complete(files)

        written: list[str] = []
        written_targets: list[Path] = []

        def _unlink_all_written() -> None:
            # Parity with guard_emit's unlink-on-fail: remove every artifact
            # this invocation wrote so a refused set never pollutes the tree.
            for t in written_targets:
                if t.exists():
                    t.unlink()

        from llmxive.speckit._diff_guard import refuse_if_diff
        try:
            for relpath, content in files.items():
                target = feature_dir / relpath
                target.parent.mkdir(parents=True, exist_ok=True)
                # Spec 010 fix: refuse diff-shaped content per file before write.
                refuse_if_diff(content, artifact_kind=relpath)
                target.write_text(content + "\n", encoding="utf-8")
                written_targets.append(target)
                # FR-009: refuse to commit template artifacts; unlink + raise
                if target.suffix == ".md":
                    guard_emit(target, repo_root=repo)
                written.append(str(target.relative_to(repo)))

            # FR-007 then FR-006: data-model<->contracts consistency, then
            # research.md URL reachability. Both run after the per-file write
            # loop so they see the full, committed artifact set.
            assert_data_model_contracts_consistent(files)
            assert_urls_reachable(files.get("research.md", ""))
        except Exception:
            _unlink_all_written()
            raise
        return written


__all__ = ["PlannerAgent"]
