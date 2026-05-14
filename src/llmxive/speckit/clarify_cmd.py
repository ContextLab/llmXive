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

from llmxive.speckit.yaml_extract import parse_yaml_lenient

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.config import TASKER_MAX_REVISION_ROUNDS
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


CLARIFY_MARKER_RE = re.compile(
    # Match BOTH the canonical bracket form `[NEEDS CLARIFICATION: …]`
    # AND the markdown-bold form `**NEEDS CLARIFICATION**: …` that the
    # Specifier LLM tends to produce. Bracket form: question is up to
    # closing `]`. Bold form: question runs to end of line.
    r"\[NEEDS CLARIFICATION:\s*(?P<bq>[^\]]+)\]"
    r"|"
    r"\*\*NEEDS CLARIFICATION\*\*\s*:\s*(?P<mq>[^\n]+)",
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
            {
                "index": i,
                "question": (m.group("bq") or m.group("mq") or "").strip(),
            }
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
        markers = mechanical_output.get("markers", []) or []
        report = _parse_clarifier_response(llm_response.text)
        if not isinstance(report, dict):
            report = {"patches": [], "notes": "non-mapping LLM output coerced to empty patches"}

        spec_text = mechanical_output["spec_text"]
        patches = report.get("patches", []) or []
        patches_by_index = {p.get("marker_index"): p for p in patches if p.get("marker_index") is not None}

        # Quality gate: every [NEEDS CLARIFICATION] marker MUST have a
        # real replacement. If the LLM produced fewer patches than there
        # are markers, fail the stage rather than papering over with
        # stub text — the Tasker and reviewers cannot recover from a
        # hidden "Resolved by default" lie. The pipeline graph treats
        # this as a real failure (no advancement to clarified) so the
        # next scheduler tick will retry the Clarifier.
        if markers and len(patches_by_index) < len(markers):
            missing = [
                m["question"] for i, m in enumerate(markers)
                if i not in patches_by_index
            ]
            raise RuntimeError(
                f"Clarifier left {len(missing)} of {len(markers)} markers unresolved; "
                f"will not advance. Unresolved: {missing!r}"
            )

        count_holder = {"n": 0}

        def _sub(match: re.Match[str]) -> str:
            idx = count_holder["n"]
            count_holder["n"] += 1
            patch = patches_by_index.get(idx)
            if patch and patch.get("replacement"):
                return patch["replacement"]
            # Should be unreachable thanks to the gate above, but keep
            # the marker in place so a later run can try again rather
            # than silently advancing.
            return match.group(0)

        spec_text = CLARIFY_MARKER_RE.sub(_sub, spec_text)
        spec_path.write_text(spec_text, encoding="utf-8")
        # FR-009: real-only guard — clarify must not regress a spec into template territory
        from llmxive.speckit._real_only_guard import guard_emit
        guard_emit(spec_path, repo_root=repo, unlink_on_fail=False)
        return [str(spec_path.relative_to(repo))]


def _parse_clarifier_response(text: str) -> dict | None:
    """Parse the Clarifier's response, preferring JSON, falling back to YAML.

    Why JSON-first: YAML's `key: value` syntax breaks when an LLM puts
    a citation title containing a colon inside a quoted string without
    YAML-escaping. JSON has no such ambiguity. The current prompt asks
    for JSON, but YAML responses from older sessions still need to
    parse.

    Handles raw newlines inside JSON string literals (a common LLM
    failure mode) by escaping them before retry.
    """
    import json as _json
    raw = (text or "").strip()
    if not raw:
        return None
    # Strip code fences ```json ... ``` or ```yaml ... ```.
    fence = re.search(r"```(?:json|yaml|yml)?\s*\n(.*?)\n```", raw, re.DOTALL | re.IGNORECASE)
    inner = fence.group(1) if fence else raw
    # Try JSON first.
    try:
        return _json.loads(inner)
    except _json.JSONDecodeError:
        pass
    # Try JSON with raw newlines auto-escaped inside strings.
    try:
        return _json.loads(_escape_newlines_in_json_strings(inner))
    except _json.JSONDecodeError:
        pass
    # Fall back to lenient YAML.
    try:
        return parse_yaml_lenient(inner)
    except yaml.YAMLError as exc:
        print(f"[clarify] both JSON and YAML parse failed: {exc}")
        return None


def _escape_newlines_in_json_strings(text: str) -> str:
    """Escape unescaped \\n / \\t / \\r inside JSON double-quoted strings."""
    out = []
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            out.append(ch)
            escape_next = False
            continue
        if ch == "\\":
            out.append(ch)
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string:
            if ch == "\n":
                out.append("\\n")
            elif ch == "\t":
                out.append("\\t")
            elif ch == "\r":
                out.append("\\r")
            else:
                out.append(ch)
        else:
            out.append(ch)
    return "".join(out)


__all__ = ["ClarifierAgent", "TASKER_MAX_REVISION_ROUNDS"]
