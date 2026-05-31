"""Paper-Clarifier Agent (T075) — drives /speckit.clarify on the paper spec.

Subclass of the research-stage ClarifierAgent that searches under
`projects/<PROJ-ID>/paper/specs/*/spec.md` instead of the research
spec, and uses the paper-specific prompt.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.speckit.clarify_cmd import CLARIFY_MARKER_RE
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext
from llmxive.speckit.yaml_extract import parse_yaml_lenient


class PaperClarifierAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.clarify"

    def _spec_path(self, ctx: SlashCommandContext) -> Path:
        candidates = sorted((ctx.project_dir / "paper").glob("specs/*/spec.md"))
        if not candidates:
            raise FileNotFoundError(f"no paper spec.md in {ctx.project_dir}/paper/specs/")
        return candidates[0]

    def _memory_dir(self, ctx: SlashCommandContext) -> Path:
        return ctx.project_dir / "paper" / ".specify" / "memory"

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        spec_path = self._spec_path(ctx)
        text = spec_path.read_text(encoding="utf-8")
        markers = [
            {
                "index": i,
                "question": (m.group("bq") or m.group("mq") or "").strip(),
            }
            for i, m in enumerate(CLARIFY_MARKER_RE.finditer(text))
        ]
        # Spec 015 T032 / discrepancy #5: persist + read real paper-clarifier
        # attempts (was hardcoded 0; escalate verdict was never branched on).
        from llmxive.speckit._clarify_attempts import read_attempts
        memory_dir = self._memory_dir(ctx)
        return {
            "spec_path": str(spec_path),
            "spec_text": text,
            "markers": markers,
            "attempts_so_far": read_attempts(memory_dir),
            "memory_dir": str(memory_dir),
        }

    def build_prompt(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
    ) -> list[ChatMessage]:
        repo = ctx.project_dir.parent.parent
        # Pull paper constitution + research-stage spec as references.
        paper_const = ctx.project_dir / "paper" / ".specify" / "memory" / "constitution.md"
        paper_constitution = paper_const.read_text(encoding="utf-8") if paper_const.exists() else ""
        research_spec = ""
        for sp in sorted(ctx.project_dir.glob("specs/*/spec.md")):
            research_spec = sp.read_text(encoding="utf-8")
            break

        system = render_prompt(
            "agents/prompts/paper_clarifier.md",
            {"project_id": ctx.project_id},
            repo_root=repo,
        )
        from llmxive.speckit._comments_context import render_recent_comments_block
        comments_block = render_recent_comments_block(ctx.project_dir)
        user = (
            f"# Current paper spec.md\n\n{mechanical_output['spec_text']}\n\n"
            f"# Markers\n\n{yaml.safe_dump(mechanical_output['markers'])}\n\n"
            f"# Attempts so far\n{mechanical_output['attempts_so_far']}\n\n"
            f"# Paper constitution\n\n{paper_constitution}\n\n"
            f"# Research-stage spec (source of truth for methodology)\n\n{research_spec}\n\n"
            + (comments_block + "\n\n" if comments_block else "")
            + "# Task\n\nReturn the YAML clarification report per the contract."
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
        spec_path = Path(mechanical_output["spec_path"])
        markers = mechanical_output.get("markers", []) or []
        try:
            report = parse_yaml_lenient(llm_response.text)
        except yaml.YAMLError as exc:
            print(f"[paper_clarify] YAML parse failed ({exc}); empty patches")
            report = {"patches": []}
        if not isinstance(report, dict):
            report = {"patches": []}

        spec_text = mechanical_output["spec_text"]
        patches: list[Any] = list(report.get("patches", []) or [])
        patches_by_index = {p.get("marker_index"): p for p in patches if p.get("marker_index") is not None}

        # Spec 015 T032 / discrepancy #5: branch on the LLM's ``escalate`` verdict
        # (previously ignored — the escalate path was dead) AND the attempt cap,
        # and REMOVE the silent "Resolved by default" stub substitution that
        # violated the no-silent-shortcuts invariant. Match the research
        # clarifier's loud-failure behavior.
        from llmxive.config import TASKER_MAX_REVISION_ROUNDS
        from llmxive.speckit._clarify_attempts import (
            bump_attempts,
            reset_attempts,
            write_human_input_needed,
        )
        memory_dir = Path(
            mechanical_output.get("memory_dir") or self._memory_dir(ctx),
        )
        verdict = report.get("verdict") if isinstance(report, dict) else None
        if verdict == "escalate":
            new_n = bump_attempts(memory_dir)
            reason = (
                f"paper_clarifier emitted verdict=escalate after {new_n} attempt(s); "
                f"unresolved markers={len(markers) - len(patches_by_index)}"
            )
            write_human_input_needed(memory_dir, reason)
            raise RuntimeError(reason)
        if markers and len(patches_by_index) < len(markers):
            new_n = bump_attempts(memory_dir)
            missing = [
                m["question"] for i, m in enumerate(markers)
                if i not in patches_by_index
            ]
            if new_n >= TASKER_MAX_REVISION_ROUNDS:
                reason = (
                    f"paper_clarifier hit attempt cap ({new_n} >= "
                    f"{TASKER_MAX_REVISION_ROUNDS}); {len(missing)} markers still "
                    f"unresolved: {missing!r}"
                )
                write_human_input_needed(memory_dir, reason)
                raise RuntimeError(reason)
            raise RuntimeError(
                f"Paper clarifier left {len(missing)} of {len(markers)} markers "
                f"unresolved (attempt {new_n}/{TASKER_MAX_REVISION_ROUNDS}); will "
                f"not advance. Unresolved: {missing!r}"
            )

        count_holder = {"n": 0}

        def _sub(match: re.Match[str]) -> str:
            idx = count_holder["n"]
            count_holder["n"] += 1
            patch = patches_by_index.get(idx)
            if patch and patch.get("replacement"):
                return str(patch["replacement"])
            # Unreachable thanks to the gate above; keep the marker in place so a
            # next tick can retry rather than silently writing a stub.
            return match.group(0)

        spec_text = CLARIFY_MARKER_RE.sub(_sub, spec_text)
        spec_path.write_text(spec_text, encoding="utf-8")
        # FR-009: real-only guard — paper clarify must not regress spec into template
        from llmxive.speckit._real_only_guard import guard_emit
        guard_emit(spec_path, repo_root=repo, unlink_on_fail=False)
        reset_attempts(memory_dir)
        outputs = [str(spec_path.relative_to(repo))]

        # --- paper-spec convergence panel (spec-015 / #239) -----------------
        # The clarified paper spec.md is reviewed by the live 4-lens paper-spec
        # panel (reader_scenario_coverage / claims_supported /
        # required_sections_figures / scope_vs_research) via the engine.
        self._run_paper_spec_panel(ctx, spec_path, memory_dir, repo)
        return outputs

    def _run_paper_spec_panel(
        self,
        ctx: SlashCommandContext,
        spec_path: Path,
        memory_dir: Path,
        repo: Path,
    ) -> None:
        from llmxive.backends.router import make_backend
        from llmxive.convergence.reviewspecs import build_paper_spec_reviewspec
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
            return  # offline / no-LLM: agent already produced the artifact.

        paper_const = (
            ctx.project_dir / "paper" / ".specify" / "memory" / "constitution.md"
        )
        constitution_text = _read(paper_const) or None
        spec = build_paper_spec_reviewspec(
            backend=backend, repo_root=repo, project_id=ctx.project_id,
            model=ctx.default_model,
        )
        spec_key = str(spec_path.relative_to(repo))
        run_stage_panel(
            stage_label="paper_spec",
            spec=spec,
            artifact_paths={spec_key: spec_path},
            extra_inputs={
                # code/data summaries are real-data artifacts produced later;
                # supply empty so the sentinel key is present (fail-loud).
                "__code_summary__": "",
                "__data_summary__": "",
                "__comments_block__": render_recent_comments_block(ctx.project_dir),
                "__constitution__": constitution_text or "",
            },
            repo_root=repo,
            memory_dir=memory_dir,
            producer="paper_specifier+paper_clarifier",
            constitution=constitution_text,
        )


__all__ = ["PaperClarifierAgent"]
