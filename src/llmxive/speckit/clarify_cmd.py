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
from llmxive.speckit.yaml_extract import parse_yaml_lenient

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

    def claim_stage_label(self) -> str | None:
        return "spec"  # spec 020 FR-001: planning → references-only + strip/smooth

    def _spec_path(self, ctx: SlashCommandContext) -> Path:
        # Spec-015 fix: resolve the feature dir via the project's authoritative
        # speckit_research_dir pointer so a convergence kickback
        # (specs/001 → specs/002) clarifies the CURRENT spec.md, not the
        # superseded first-glob one. SSoT: llmxive.speckit._feature_dir.
        from llmxive.speckit._feature_dir import resolve_feature_dir
        feature_dir = resolve_feature_dir(ctx)
        spec_path = feature_dir / "spec.md"
        if not spec_path.exists():
            raise FileNotFoundError(f"no spec.md in {feature_dir}")
        return spec_path

    def _memory_dir(self, ctx: SlashCommandContext) -> Path:
        return ctx.project_dir / ".specify" / "memory"

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
        # Spec 015 T032 / discrepancy #5: persist + read real attempt count so the
        # escalation path (cap → human_input_needed) is actually reachable.
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
        system = render_prompt(
            "agents/prompts/clarifier.md",
            {"project_id": ctx.project_id},
            repo_root=repo,
        )
        # Spec 011 / FR-013: inject recent personality + reviewer comments
        # so the clarifier's question selection reflects what reviewers
        # have already flagged on this project.
        from llmxive.speckit._comments_context import render_recent_comments_block
        comments_block = render_recent_comments_block(ctx.project_dir)

        user = (
            f"# Current spec.md\n\n{mechanical_output['spec_text']}\n\n"
            f"# Markers\n\n{yaml.safe_dump(mechanical_output['markers'])}\n\n"
            f"# Attempts so far\n{mechanical_output['attempts_so_far']}\n\n"
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
        report = _parse_clarifier_response(llm_response.text)
        if not isinstance(report, dict):
            report = {"patches": [], "notes": "non-mapping LLM output coerced to empty patches"}

        spec_text = mechanical_output["spec_text"]
        patches: list[dict[str, Any]] = list(report.get("patches", []) or [])
        patches_by_index = {p.get("marker_index"): p for p in patches if p.get("marker_index") is not None}

        # Spec 015 T032 / discrepancy #5: real escalation. Read the persisted
        # attempt count (mechanical_step put it here; legacy callers omit the key
        # → derive from ctx). Branch on the LLM's explicit ``escalate`` verdict OR
        # the attempt cap; either way drop human_input_needed.yaml + raise.
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
                f"clarifier emitted verdict=escalate after {new_n} attempt(s); "
                f"unresolved markers={len(markers) - len(patches_by_index)}"
            )
            # Spec 023 / FR-017: an LLM "escalate" verdict alone is NOT
            # exhaustion — the bounded loop must run to its cap before a
            # human is asked. Below the cap, fail this attempt and retry
            # on a later tick.
            if new_n < TASKER_MAX_REVISION_ROUNDS:
                raise RuntimeError(
                    f"{reason} (attempt {new_n}/{TASKER_MAX_REVISION_ROUNDS}; "
                    "retrying before any human escalation)"
                )
            write_human_input_needed(
                memory_dir, reason,
                rounds_used=new_n, bound=TASKER_MAX_REVISION_ROUNDS,
            )
            raise RuntimeError(reason)
        # Quality gate: every [NEEDS CLARIFICATION] marker MUST have a real
        # replacement. If the LLM produced fewer patches than markers, fail the
        # stage rather than papering over with stub text — and if we've hit the
        # attempt cap, escalate to human input rather than looping forever.
        if markers and len(patches_by_index) < len(markers):
            new_n = bump_attempts(memory_dir)
            missing = [
                m["question"] for i, m in enumerate(markers)
                if i not in patches_by_index
            ]
            if new_n >= TASKER_MAX_REVISION_ROUNDS:
                reason = (
                    f"clarifier hit attempt cap ({new_n} >= "
                    f"{TASKER_MAX_REVISION_ROUNDS}); {len(missing)} markers still "
                    f"unresolved: {missing!r}"
                )
                write_human_input_needed(
                    memory_dir, reason,
                    rounds_used=new_n, bound=TASKER_MAX_REVISION_ROUNDS,
                )
                raise RuntimeError(reason)
            raise RuntimeError(
                f"Clarifier left {len(missing)} of {len(markers)} markers unresolved "
                f"(attempt {new_n}/{TASKER_MAX_REVISION_ROUNDS}); will not advance. "
                f"Unresolved: {missing!r}"
            )

        count_holder = {"n": 0}

        def _sub(match: re.Match[str]) -> str:
            idx = count_holder["n"]
            count_holder["n"] += 1
            patch = patches_by_index.get(idx)
            if patch and patch.get("replacement"):
                return str(patch["replacement"])
            # Should be unreachable thanks to the gate above, but keep
            # the marker in place so a later run can try again rather
            # than silently advancing.
            return match.group(0)

        spec_text = CLARIFY_MARKER_RE.sub(_sub, spec_text)
        spec_path.write_text(spec_text, encoding="utf-8")
        # FR-009: real-only guard — clarify must not regress a spec into template territory
        from llmxive.speckit._real_only_guard import guard_emit
        guard_emit(spec_path, repo_root=repo, unlink_on_fail=False)
        # T032: successful clarify clears the attempt counter.
        reset_attempts(memory_dir)
        outputs = [str(spec_path.relative_to(repo))]

        # --- spec convergence panel (spec-015 / #239) -----------------------
        # The clarified spec.md is now reviewed by the live 4-lens spec panel
        # (requirements_coverage / internal_consistency / testability / scope)
        # via the convergence engine. On all-accept the stage advances as
        # before; on a non-converging panel a kickback marker is written and a
        # StagePanelKickback is raised so the graph routes back. backend=None
        # (offline) skips the panel gracefully.
        self._run_spec_panel(ctx, spec_path, memory_dir, repo)
        return outputs

    def _run_spec_panel(
        self,
        ctx: SlashCommandContext,
        spec_path: Path,
        memory_dir: Path,
        repo: Path,
    ) -> None:
        from llmxive.backends.router import make_backend
        from llmxive.convergence.reviewspecs import build_spec_reviewspec
        from llmxive.speckit._stage_panel import (
            _constitution,
            _idea_md,
            _spec_template,
            render_recent_comments_block,
            run_stage_panel,
        )

        try:
            backend = make_backend(ctx.default_backend.value)
        except Exception:
            backend = None
        if backend is None:
            return  # offline / no-LLM: agent already produced the artifact.

        constitution_text = _constitution(memory_dir) or None
        spec = build_spec_reviewspec(
            backend=backend, repo_root=repo, project_id=ctx.project_id,
            model=ctx.default_model,
        )
        spec_key = str(spec_path.relative_to(repo))
        run_stage_panel(
            stage_label="spec",
            spec=spec,
            artifact_paths={spec_key: spec_path},
            extra_inputs={
                "__idea_md__": _idea_md(ctx.project_dir),
                "__comments_block__": render_recent_comments_block(ctx.project_dir),
                "__spec_template__": _spec_template(ctx.project_dir, repo),
            },
            repo_root=repo,
            memory_dir=memory_dir,
            producer="specifier+clarifier",
            constitution=constitution_text,
        )


def _parse_clarifier_response(text: str) -> dict[str, Any] | None:
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
        parsed = _json.loads(inner)
        return parsed if isinstance(parsed, dict) else None
    except _json.JSONDecodeError:
        pass
    # Try JSON with raw newlines auto-escaped inside strings.
    try:
        parsed = _json.loads(_escape_newlines_in_json_strings(inner))
        return parsed if isinstance(parsed, dict) else None
    except _json.JSONDecodeError:
        pass
    # Fall back to lenient YAML.
    try:
        parsed = parse_yaml_lenient(inner)
        return parsed if isinstance(parsed, dict) else None
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


__all__ = ["TASKER_MAX_REVISION_ROUNDS", "ClarifierAgent"]
