"""Tasker Agent — drives /speckit.tasks then /speckit.analyze loop (T052).

Mode A: generate tasks.md from spec.md + plan.md.
Mode B: read /speckit.analyze report and propose patches; loop until
analyze returns CLEAN or `TASKER_MAX_REVISION_ROUNDS` is reached
(then escalate to `human_input_needed`).

There is no dedicated mechanical script in upstream Spec Kit for
/speckit.tasks (the slash command is agent-driven). The Tasker
therefore reads the existing artifacts directly.

Stage transitions:
  `planned` → `tasked` → `analyze_in_progress` →
                                 `analyzed` | `human_input_needed`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.backends.router import chat_with_fallback
from llmxive.config import TASKER_MAX_REVISION_ROUNDS
from llmxive.speckit.analyze_cmd import is_clean, run_analyze
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


class TaskerAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.tasks"

    def _feature_dir(self, ctx: SlashCommandContext) -> Path:
        candidates = sorted(ctx.project_dir.glob("specs/*/"))
        if not candidates:
            raise FileNotFoundError(f"no specs/ feature dir in {ctx.project_dir}")
        # Prefer dir with tasks.md, fall back to dir with spec.md.
        # An LLM's earlier wrong-slug write can leave a ghost specs/
        # subdir; alphabetical-first picks the wrong one.
        for c in candidates:
            if (c / "tasks.md").exists():
                return c
        for c in candidates:
            if (c / "spec.md").exists():
                return c
        return candidates[0]

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        feature_dir = self._feature_dir(ctx)
        return {
            "feature_dir": str(feature_dir),
            "spec_path": str(feature_dir / "spec.md"),
            "plan_path": str(feature_dir / "plan.md"),
            "tasks_path": str(feature_dir / "tasks.md"),
            "tasks_template_path": str(
                ctx.project_dir / ".specify" / "templates" / "tasks-template.md"
            ),
        }

    def build_prompt(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
    ) -> list[ChatMessage]:
        repo = ctx.project_dir.parent.parent
        spec_text = Path(mechanical_output["spec_path"]).read_text(encoding="utf-8")
        plan_text = Path(mechanical_output["plan_path"]).read_text(encoding="utf-8")
        tasks_template_path = Path(mechanical_output["tasks_template_path"])
        tasks_template = (
            tasks_template_path.read_text(encoding="utf-8")
            if tasks_template_path.exists()
            else ""
        )
        # On a revision pass, surface prior review feedback so the
        # Tasker can write tasks that explicitly address each
        # reviewer's complaints. Without this, the Tasker would
        # regenerate the same tasks and the reviewers would reject
        # again.
        existing_tasks_path = Path(mechanical_output["tasks_path"])
        existing_tasks = (
            existing_tasks_path.read_text(encoding="utf-8")
            if existing_tasks_path.exists()
            else ""
        )
        reviews_dir = ctx.project_dir / "reviews" / "research"
        review_block = ""
        if reviews_dir.is_dir():
            review_chunks: list[str] = []
            for md in sorted(reviews_dir.glob("*.md")):
                try:
                    text = md.read_text(encoding="utf-8")
                except OSError:
                    continue
                review_chunks.append(f"## {md.name}\n\n{text}")
            if review_chunks:
                review_block = (
                    "\n\n# Prior research-stage reviews "
                    "(address every reviewer's concerns in the new tasks list)\n\n"
                    + "\n\n---\n\n".join(review_chunks)
                )
        system = render_prompt(
            "agents/prompts/tasker.md",
            {"project_id": ctx.project_id, "mode": "A"},
            repo_root=repo,
        )
        user_parts = [
            "Mode: A (generate tasks.md)",
            f"# spec.md\n\n{spec_text}",
            f"# plan.md\n\n{plan_text}",
            f"# tasks template\n\n{tasks_template}",
        ]
        if existing_tasks.strip():
            user_parts.append(
                "# Existing tasks.md (revise — keep [X] tasks already done, "
                "add new [ ] tasks that address review concerns)\n\n" + existing_tasks
            )
        if review_block:
            user_parts.append(review_block)
        user_parts.append(
            "# Task\n\nReturn the FULL contents of tasks.md as Markdown. "
            "DO NOT return a diff or partial patch — return the entire "
            "file from the first line to the last. Preserve all existing "
            "[X]-marked tasks verbatim and append new [ ]-marked tasks "
            "for the revision concerns. The output MUST contain at least "
            "one line beginning with `- [ ] T###`."
        )
        user = "\n\n".join(user_parts)
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
        tasks_path = Path(mechanical_output["tasks_path"])
        tasks_path.parent.mkdir(parents=True, exist_ok=True)
        # Strip ```markdown / ```md fences if the LLM wrapped its response.
        text = llm_response.text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].lstrip("`").lower() in {"", "markdown", "md"}:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        # Stronger validation: tasks.md must:
        #   1. NOT be a unified or context diff (spec 010 fix — the old
        #      guard caught `@@`-prefixed leads but missed `--- a/<path>`
        #      headers; 8 production files got polluted before this was
        #      tightened). Single source of truth: _diff_guard.refuse_if_diff.
        #   2. contain at least 5 task checkboxes (a real research project
        #      needs setup + multiple phases + polish; <5 is a stub)
        #   3. each checkbox line MUST start with `- [ ] T` followed by
        #      digits (T001, T012, etc.) per the format contract
        from llmxive.speckit._diff_guard import refuse_if_diff
        refuse_if_diff(text, artifact_kind="tasks.md")
        import re as _re
        task_id_lines = _re.findall(r"^- \[[ Xx]\] T\d+\b", text, _re.MULTILINE)
        if len(task_id_lines) < 5:
            raise RuntimeError(
                f"Tasker produced only {len(task_id_lines)} task IDs "
                f"(need >= 5; total chars: {len(text)}). Re-running on next cycle."
            )
        tasks_path.write_text(text + "\n", encoding="utf-8")
        # FR-009: real-only guard — refuse to commit a template tasks.md
        from llmxive.speckit._real_only_guard import guard_emit
        guard_emit(tasks_path, repo_root=repo)
        written = [str(tasks_path.relative_to(repo))]

        # Now run the analyze-resolve loop. Backend failures here are
        # NOT fatal — tasks.md is already a quality artifact (we just
        # validated it has >=5 task IDs and isn't a diff). The analyze
        # loop is a polish step. If a round fails, log and break out
        # so the project advances; downstream specialist reviewers
        # will catch any substantive issues.
        from llmxive.backends.base import BackendError as _BackendError

        spec_path = Path(mechanical_output["spec_path"])
        plan_path = Path(mechanical_output["plan_path"])
        for round_idx in range(TASKER_MAX_REVISION_ROUNDS):
            try:
                report = run_analyze(
                    spec_text=spec_path.read_text(encoding="utf-8"),
                    plan_text=plan_path.read_text(encoding="utf-8"),
                    tasks_text=tasks_path.read_text(encoding="utf-8"),
                    default_backend=ctx.default_backend,
                    fallback_backends=ctx.fallback_backends,
                    default_model=ctx.default_model,
                    repo_root=repo,
                )
            except _BackendError as exc:
                print(f"[tasker] analyze round {round_idx + 1} failed: {exc}; "
                      "skipping further analyze rounds")
                break
            if is_clean(report):
                # Persist the round count alongside tasks.md for SC-012.
                round_record = (
                    ctx.project_dir / ".specify" / "memory" / "tasker_rounds.yaml"
                )
                round_record.parent.mkdir(parents=True, exist_ok=True)
                round_record.write_text(
                    yaml.safe_dump({"rounds_used": round_idx + 1}),
                    encoding="utf-8",
                )
                return written

            # Mode B — ask the Tasker to patch the artifacts.
            mode_b_system = render_prompt(
                "agents/prompts/tasker.md",
                {"project_id": ctx.project_id, "mode": "B"},
                repo_root=repo,
            )
            mode_b_user = (
                "Mode: B (resolve analyze findings)\n\n"
                f"# Analyze report\n\n{report}\n\n"
                f"# spec.md\n\n{spec_path.read_text(encoding='utf-8')}\n\n"
                f"# plan.md\n\n{plan_path.read_text(encoding='utf-8')}\n\n"
                f"# tasks.md\n\n{tasks_path.read_text(encoding='utf-8')}\n\n"
                "Return the YAML patch document per the contract."
            )
            try:
                patch_response = chat_with_fallback(
                    [
                        ChatMessage(role="system", content=mode_b_system),
                        ChatMessage(role="user", content=mode_b_user),
                    ],
                    default_backend=ctx.default_backend.value,
                    fallback_backends=[b.value for b in ctx.fallback_backends],
                    model=ctx.default_model,
                )
            except _BackendError as exc:
                print(f"[tasker] Mode-B round {round_idx + 1} backend failed: {exc}; "
                      "skipping further analyze rounds")
                break
            doc = _parse_tasker_response(patch_response.text)
            if not isinstance(doc, dict):
                # Couldn't parse — let the next round retry rather than
                # silently dropping the patches.
                continue
            for issue in doc.get("issues_resolved", []) or []:
                f = issue.get("file")
                patch = issue.get("patch", "")
                if not patch or not isinstance(patch, str):
                    continue
                # Mode-B patches replace the WHOLE file. Validate the
                # patch keeps the file's essential structure: tasks.md
                # must have >=5 task IDs (else it's been replaced with
                # prose like "All tasks completed"); spec.md and
                # plan.md must have >=1 markdown header.
                import re as _re_inner
                if f == "tasks.md":
                    n_ids = len(_re_inner.findall(
                        r"^- \[[ Xx]\] T\d+[a-z]?\b", patch, _re_inner.MULTILINE
                    ))
                    if n_ids < 5:
                        print(
                            f"[tasker] refusing Mode-B tasks.md patch: "
                            f"only {n_ids} task IDs (need >=5). The LLM "
                            f"likely replaced the file with prose. Skipping."
                        )
                        continue
                if f in ("spec.md", "plan.md"):
                    if not _re_inner.search(r"^# ", patch, _re_inner.MULTILINE):
                        print(
                            f"[tasker] refusing Mode-B {f} patch: "
                            f"no markdown headers. Skipping."
                        )
                        continue
                # Spec 010 fix: the original escalate branch wrote `patch`
                # to disk verbatim; if the LLM returned a diff here, it
                # would pollute the canonical file. Reuse the same
                # _diff_guard used by the main path.
                from llmxive.speckit._diff_guard import looks_like_diff
                is_diff, reason = looks_like_diff(patch)
                if is_diff:
                    print(
                        f"[tasker] refusing Mode-B {f} patch: "
                        f"looks like a diff ({reason}). Skipping."
                    )
                    continue
                if f == "spec.md":
                    spec_path.write_text(patch, encoding="utf-8")
                elif f == "plan.md":
                    plan_path.write_text(patch, encoding="utf-8")
                elif f == "tasks.md":
                    tasks_path.write_text(patch, encoding="utf-8")
            if doc.get("verdict") == "escalate":
                # Escalate flag — caller transitions project to
                # human_input_needed.
                escalate_marker = (
                    ctx.project_dir / ".specify" / "memory" / "human_input_needed.yaml"
                )
                escalate_marker.parent.mkdir(parents=True, exist_ok=True)
                escalate_marker.write_text(
                    yaml.safe_dump(
                        {
                            "reason": "tasker analyze loop did not converge",
                            "rounds_used": round_idx + 1,
                        }
                    ),
                    encoding="utf-8",
                )
                return written

        # Cap reached without converge — accept the current tasks.md as
        # best-effort and let the project advance. The analyze loop is a
        # quality polish, not a hard gate; downstream specialist reviewers
        # will catch substantive issues.
        rounds_marker = (
            ctx.project_dir / ".specify" / "memory" / "tasker_rounds.yaml"
        )
        rounds_marker.parent.mkdir(parents=True, exist_ok=True)
        rounds_marker.write_text(
            yaml.safe_dump({"rounds_used": TASKER_MAX_REVISION_ROUNDS, "converged": False}),
            encoding="utf-8",
        )
        return written


def _parse_tasker_response(text: str) -> dict | None:
    """Parse Tasker Mode-B response, preferring JSON, falling back to YAML.

    LLMs often emit raw newlines inside JSON string values (which JSON
    forbids — newlines must be escaped as \\n). We pre-process the
    payload to escape unescaped newlines inside string literals, so
    standard json.loads succeeds on real-world LLM output.

    Also handles colons inside YAML scalars (a separate failure mode)
    by falling back to lenient YAML parsing if the JSON path fails.
    """
    import json as _json
    import re as _re_local
    from llmxive.speckit.yaml_extract import parse_yaml_lenient as _parse_yaml

    raw = (text or "").strip()
    if not raw:
        return None
    fence = _re_local.search(
        r"```(?:json|yaml|yml)?\s*\n(.*?)\n```",
        raw,
        _re_local.DOTALL | _re_local.IGNORECASE,
    )
    inner = fence.group(1) if fence else raw

    # Try direct JSON.
    try:
        return _json.loads(inner)
    except _json.JSONDecodeError:
        pass

    # Try JSON with raw newlines inside strings auto-escaped. We walk
    # the text in/out of double-quoted regions and replace literal
    # control chars with their JSON-escaped form.
    try:
        return _json.loads(_escape_newlines_in_json_strings(inner))
    except _json.JSONDecodeError:
        pass

    # Try lenient YAML.
    try:
        return _parse_yaml(inner)
    except yaml.YAMLError as exc:
        print(f"[tasker] both JSON and YAML parse failed: {exc}")
        return None


def _escape_newlines_in_json_strings(text: str) -> str:
    """Escape unescaped newlines/tabs inside JSON double-quoted string values.

    Walks the text tracking whether we're inside a string literal. Inside
    a string, replaces literal `\n` with `\\n` and literal `\t` with
    `\\t` so json.loads doesn't choke on them. Outside strings, leaves
    everything alone.
    """
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


__all__ = ["TaskerAgent"]
