"""Clarifier Agent — drives /speckit.clarify (T048).

There is no dedicated mechanical script for clarify in upstream Spec
Kit; the slash command is purely an LLM workflow that edits spec.md
in place. The agent's mechanical_step here therefore reads the
current spec.md and parses its `[NEEDS CLARIFICATION: ...]` markers.

Stage transitions:
  `specified` → `clarify_in_progress` → `clarified` |
                                      → `human_input_needed` (after attempts cap)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.config import TASKER_MAX_REVISION_ROUNDS
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


CLARIFY_MARKER_RE = re.compile(
    r"\[NEEDS CLARIFICATION:\s*(?P<question>[^\]]+)\]",
    re.IGNORECASE | re.DOTALL,
)


class ClarifierAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.clarify"

    def _spec_path(self, ctx: SlashCommandContext) -> Path:
        repo = ctx.project_dir.parent.parent
        feature_dir_str = ctx.metadata if isinstance(ctx, dict) else None  # type: ignore[unreachable]
        # Find the project's spec.md by walking specs/.
        candidates = sorted(ctx.project_dir.glob("specs/*/spec.md"))
        if not candidates:
            raise FileNotFoundError(f"no spec.md in {ctx.project_dir}/specs/")
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
        system = render_prompt(
            "agents/prompts/clarifier.md",
            {"project_id": ctx.project_id},
            repo_root=repo,
        )
        user = (
            f"# Current spec.md\n\n{mechanical_output['spec_text']}\n\n"
            f"# Markers\n\n{yaml.safe_dump(mechanical_output['markers'])}\n\n"
            f"# Attempts so far\n{mechanical_output['attempts_so_far']}\n\n"
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
            raise RuntimeError(f"Clarifier returned invalid YAML: {exc}") from exc
        if not isinstance(report, dict):
            raise RuntimeError("Clarifier YAML must be a mapping")

        spec_text = mechanical_output["spec_text"]
        for patch in report.get("patches", []) or []:
            idx = patch.get("marker_index")
            replacement = patch.get("replacement", "")
            if idx is None:
                continue
            # Replace the Nth occurrence in order.
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


__all__ = ["ClarifierAgent", "TASKER_MAX_REVISION_ROUNDS"]
