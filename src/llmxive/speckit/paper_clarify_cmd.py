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


class PaperClarifierAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.clarify"

    def _spec_path(self, ctx: SlashCommandContext) -> Path:
        candidates = sorted((ctx.project_dir / "paper").glob("specs/*/spec.md"))
        if not candidates:
            raise FileNotFoundError(f"no paper spec.md in {ctx.project_dir}/paper/specs/")
        return candidates[0]

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        spec_path = self._spec_path(ctx)
        text = spec_path.read_text(encoding="utf-8")
        markers = [
            {"index": i, "question": m.group("question").strip()}
            for i, m in enumerate(CLARIFY_MARKER_RE.finditer(text))
        ]
        return {
            "spec_path": str(spec_path),
            "spec_text": text,
            "markers": markers,
            "attempts_so_far": 0,
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
        user = (
            f"# Current paper spec.md\n\n{mechanical_output['spec_text']}\n\n"
            f"# Markers\n\n{yaml.safe_dump(mechanical_output['markers'])}\n\n"
            f"# Attempts so far\n{mechanical_output['attempts_so_far']}\n\n"
            f"# Paper constitution\n\n{paper_constitution}\n\n"
            f"# Research-stage spec (source of truth for methodology)\n\n{research_spec}\n\n"
            "# Task\n\nReturn the YAML clarification report per the contract."
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
        try:
            report = yaml.safe_load(llm_response.text)
        except yaml.YAMLError as exc:
            raise RuntimeError(f"Paper-Clarifier returned invalid YAML: {exc}") from exc
        if not isinstance(report, dict):
            raise RuntimeError("Paper-Clarifier YAML must be a mapping")

        spec_text = mechanical_output["spec_text"]
        for patch in report.get("patches", []) or []:
            idx = patch.get("marker_index")
            replacement = patch.get("replacement", "")
            if idx is None:
                continue
            count = 0

            def _sub(match: re.Match[str]) -> str:
                nonlocal count
                count += 1
                if count - 1 == idx:
                    return replacement
                return match.group(0)

            spec_text = CLARIFY_MARKER_RE.sub(_sub, spec_text)
        spec_path.write_text(spec_text, encoding="utf-8")
        return [str(spec_path.relative_to(repo))]


__all__ = ["PaperClarifierAgent"]
