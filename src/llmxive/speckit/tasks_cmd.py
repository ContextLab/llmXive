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

import difflib
from pathlib import Path
from typing import Any

import yaml

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import (
    BackendUnavailable,
    ChatMessage,
    ChatResponse,
    TransientBackendError,
)
from llmxive.backends.router import chat_with_fallback
from llmxive.config import TASKER_MAX_REVISION_ROUNDS
from llmxive.speckit.analyze_cmd import is_clean, run_analyze
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext


def _unified_diff(before: str, after: str, path: str) -> str:
    """Return a unified diff string for an inspection round's file rewrite."""
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )


class TaskerAgent(SlashCommandAgent):
    def slash_command_name(self) -> str:
        return "speckit.tasks"

    def claim_stage_label(self) -> str | None:
        return "tasks"  # spec 020 FR-001: planning → references-only + strip/smooth

    def _feature_dir(self, ctx: SlashCommandContext) -> Path:
        # Spec-015 fix: resolve via the project's authoritative
        # speckit_research_dir pointer so a convergence kickback
        # (specs/001 → specs/002) builds tasks against the CURRENT spec, not
        # the superseded first-glob one. The fallback still handles ghost
        # slug dirs by preferring spec.md, but picks the LATEST not the first.
        # SSoT: llmxive.speckit._feature_dir.
        from llmxive.speckit._feature_dir import resolve_feature_dir
        return resolve_feature_dir(ctx)

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

        # Spec 015 T027 production cutover: the convergence engine is
        # now the DEFAULT analyze-resolve path. The legacy Mode-A/Mode-B
        # loop below is retained only as an emergency rollback via the
        # opt-out env var ``LLMXIVE_TASKER_LEGACY=1`` (FR-009 SSoT: one
        # convergence engine parameterized per step). The dispatch
        # happens AFTER the Mode-A write above so the bridge has a
        # tasks.md to revise.
        from llmxive.speckit._tasker_engine_bridge import (
            tasker_engine_enabled as _tasker_engine_enabled,
        )
        self._inspection_rounds: list[dict[str, Any]] = []
        if _tasker_engine_enabled():
            self._run_engine_path(
                ctx=ctx,
                repo=repo,
                tasks_path=tasks_path,
                spec_path=spec_path,
                plan_path=plan_path,
                written=written,
            )
            return written
        # spec 014 / FR-004 (T007): accumulate one observability sub-record per
        # analyze round into self._inspection_rounds. This is OBSERVABILITY
        # ONLY — no decision/branch below reads it. _maybe_write_inspection in
        # slash_command.py picks it up via getattr(agent, "_inspection_rounds").
        for round_idx in range(TASKER_MAX_REVISION_ROUNDS):
            try:
                # Spec 015 T031 + FR-030: include the project's constitution.md
                # in analyze inputs (when present) so the analyzer can flag
                # Constitution-Check violations.
                _const_path = ctx.project_dir / ".specify" / "memory" / "constitution.md"
                _const_text = (
                    _const_path.read_text(encoding="utf-8") if _const_path.exists() else None
                )
                report = run_analyze(
                    spec_text=spec_path.read_text(encoding="utf-8"),
                    plan_text=plan_path.read_text(encoding="utf-8"),
                    tasks_text=tasks_path.read_text(encoding="utf-8"),
                    default_backend=ctx.default_backend,
                    fallback_backends=ctx.fallback_backends,
                    default_model=ctx.default_model,
                    repo_root=repo,
                    project_dir=ctx.project_dir,
                    kind="research",
                    constitution_text=_const_text,
                )
            except _BackendError as exc:
                print(f"[tasker] analyze round {round_idx + 1} failed: {exc}; "
                      "skipping further analyze rounds")
                break
            if is_clean(report):
                # T007 observability: a clean analyze pass is still a round —
                # record the report it received (no Mode-B patch, no rewrites).
                self._inspection_rounds.append({
                    "round_index": round_idx,
                    "analyze_report": report,
                    "mode_b_patch": None,
                    "verdict": "clean",
                    "files_rewritten": [],
                    "diffs": {},
                })
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
                # T007 observability: an unparseable Mode-B response is still a
                # round — record the report + raw patch so the inspection trail
                # shows why nothing was rewritten.
                self._inspection_rounds.append({
                    "round_index": round_idx,
                    "analyze_report": report,
                    "mode_b_patch": patch_response.text,
                    "verdict": None,
                    "files_rewritten": [],
                    "diffs": {},
                })
                # Couldn't parse — let the next round retry rather than
                # silently dropping the patches.
                continue
            # T007 observability: snapshot the three artifacts so we can emit a
            # before/after diff for whichever ones this round rewrites.
            _round_before = {
                "spec.md": spec_path.read_text(encoding="utf-8") if spec_path.exists() else "",
                "plan.md": plan_path.read_text(encoding="utf-8") if plan_path.exists() else "",
                "tasks.md": tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else "",
            }
            _files_rewritten: list[str] = []
            for issue in doc.get("issues_resolved", []) or []:
                f = issue.get("file")
                patch = issue.get("patch", "")
                if not patch or not isinstance(patch, str):
                    continue
                # Mode-B patches replace the WHOLE file. Validate the
                # patch via the FR-031 SSoT pre-filter guards
                # (_legacy_guards.check_legacy_guards) so the same
                # rejection logic runs in BOTH the legacy loop AND the
                # convergence-engine bridge (spec-015 T027).
                from llmxive.speckit._legacy_guards import (
                    check_legacy_guards as _check_legacy_guards,
                )
                if f not in ("tasks.md", "spec.md", "plan.md"):
                    continue
                _original_for_guard = ""
                if f == "spec.md" and spec_path.exists():
                    _original_for_guard = spec_path.read_text(encoding="utf-8")
                elif f == "plan.md" and plan_path.exists():
                    _original_for_guard = plan_path.read_text(encoding="utf-8")
                elif f == "tasks.md" and tasks_path.exists():
                    _original_for_guard = tasks_path.read_text(encoding="utf-8")
                _refusals = _check_legacy_guards(
                    filename=f,
                    new_content=patch,
                    original_content=_original_for_guard,
                )
                if _refusals:
                    for _msg in _refusals:
                        print(f"[tasker] {_msg}. Skipping.")
                    continue
                if f == "spec.md":
                    spec_path.write_text(patch, encoding="utf-8")
                    _files_rewritten.append("spec.md")
                elif f == "plan.md":
                    plan_path.write_text(patch, encoding="utf-8")
                    _files_rewritten.append("plan.md")
                elif f == "tasks.md":
                    tasks_path.write_text(patch, encoding="utf-8")
                    _files_rewritten.append("tasks.md")
            # T007 observability: record this Mode-B round (before any
            # escalate short-circuit so a cap-hit round is still captured).
            _round_after = {
                "spec.md": spec_path.read_text(encoding="utf-8") if spec_path.exists() else "",
                "plan.md": plan_path.read_text(encoding="utf-8") if plan_path.exists() else "",
                "tasks.md": tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else "",
            }
            _round_diffs = {
                fn: _unified_diff(_round_before[fn], _round_after[fn], fn)
                for fn in dict.fromkeys(_files_rewritten)
            }
            self._inspection_rounds.append({
                "round_index": round_idx,
                "analyze_report": report,
                "mode_b_patch": patch_response.text,
                "verdict": doc.get("verdict"),
                "files_rewritten": list(dict.fromkeys(_files_rewritten)),
                "diffs": _round_diffs,
            })
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

    def _run_engine_path(
        self,
        *,
        ctx: SlashCommandContext,
        repo: Path,
        tasks_path: Path,
        spec_path: Path,
        plan_path: Path,
        written: list[str],
    ) -> None:
        """Spec 015 T027 production cutover — convergence-engine path
        replacing the legacy Mode-A/Mode-B loop.

        Mirrors the legacy semantics:

        1. Reads the project's constitution.md (if present) so it can be
           passed to the analyzer and (via ``extra_inputs``) to the engine
           reviser.
        2. Runs the first ``run_analyze`` (Mode-A equivalent) on the just-
           written tasks.md + on-disk spec.md + plan.md. If the analyzer
           returns ``CLEAN``, records a single observability round and
           writes the ``tasker_rounds.yaml`` marker — no engine call
           needed.
        3. Otherwise delegates the iterative resolve to
           :func:`run_tasker_via_engine` (which runs the engine internally
           up to ``CONVERGENCE_MAX_ROUNDS=3``, applies the FR-031
           deterministic guards on every R2 writeback, and persists the
           tasks.md / spec.md / plan.md changes).
        4. After the engine returns, runs ``run_analyze`` once more to
           confirm the analyzer is clean on the post-engine artifacts;
           records the final round + writes the ``tasker_rounds.yaml``
           marker (``converged`` reflects the actual analyzer + engine
           outcomes — FR-016 honest reporting).

        Backend failures during the FIRST analyze are NOT fatal: tasks.md
        was already validated in ``write_artifacts`` to have ≥5 task IDs
        and pass the diff guard — the analyze loop is a polish step. If
        the first analyze can't run, we skip the engine loop and let the
        downstream specialist reviewers catch substantive issues.
        """
        from llmxive.backends.base import BackendError as _BackendError
        from llmxive.backends.router import make_backend
        from llmxive.speckit._tasker_engine_bridge import run_tasker_via_engine

        _const_path = ctx.project_dir / ".specify" / "memory" / "constitution.md"
        _const_text = (
            _const_path.read_text(encoding="utf-8") if _const_path.exists() else None
        )

        # ---- Round 0: first analyze (Mode-A equivalent) ----
        try:
            first_report = run_analyze(
                spec_text=spec_path.read_text(encoding="utf-8"),
                plan_text=plan_path.read_text(encoding="utf-8"),
                tasks_text=tasks_path.read_text(encoding="utf-8"),
                default_backend=ctx.default_backend,
                fallback_backends=ctx.fallback_backends,
                default_model=ctx.default_model,
                repo_root=repo,
                project_dir=ctx.project_dir,
                kind="research",
                constitution_text=_const_text,
            )
        except _BackendError as exc:
            print(
                f"[tasker/engine] initial analyze failed: {exc}; "
                "skipping engine resolve loop"
            )
            return

        if is_clean(first_report):
            # First analyze is clean — no engine call needed.
            self._inspection_rounds.append({
                "round_index": 0,
                "analyze_report": first_report,
                "mode_b_patch": None,
                "verdict": "clean",
                "files_rewritten": [],
                "diffs": {},
            })
            rounds_marker = (
                ctx.project_dir / ".specify" / "memory" / "tasker_rounds.yaml"
            )
            rounds_marker.parent.mkdir(parents=True, exist_ok=True)
            rounds_marker.write_text(
                yaml.safe_dump({"rounds_used": 1, "converged": True}),
                encoding="utf-8",
            )
            return

        # ---- Engine resolve loop ----
        # Package the analyze report as a single synthetic finding so the
        # bridge's _AnalyzeReportReviewer feeds the engine's R1 the
        # analyzer's full critique. Severity defaults to "writing" (the
        # most conservative) inside analyze_findings_to_concerns; if the
        # analyzer is producing structured class tags they survive
        # through analyze_findings_to_concerns's class→severity map.
        analyze_findings = [{
            "id": "F001",
            "class": "writing",
            "artifact": tasks_path.relative_to(repo).as_posix(),
            "location": "",
            "text": first_report,
        }]

        # Snapshot the pre-engine state for the observability diff.
        _round_before = {
            "spec.md": spec_path.read_text(encoding="utf-8") if spec_path.exists() else "",
            "plan.md": plan_path.read_text(encoding="utf-8") if plan_path.exists() else "",
            "tasks.md": tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else "",
        }

        try:
            backend = make_backend(ctx.default_backend.value)
        except Exception as exc:
            print(
                f"[tasker/engine] backend instantiation failed: {exc}; "
                "falling back to legacy path is not possible mid-write; "
                "marking non-converged"
            )
            rounds_marker = (
                ctx.project_dir / ".specify" / "memory" / "tasker_rounds.yaml"
            )
            rounds_marker.parent.mkdir(parents=True, exist_ok=True)
            rounds_marker.write_text(
                yaml.safe_dump({"rounds_used": 1, "converged": False}),
                encoding="utf-8",
            )
            return

        try:
            engine_result = run_tasker_via_engine(
                project_id=ctx.project_id,
                repo_root=repo,
                tasks_path=tasks_path,
                spec_path=spec_path,
                plan_path=plan_path,
                analyze_findings=analyze_findings,
                backend=backend,
                constitution_text=_const_text,
                analyze_report_text=first_report,
                model=ctx.default_model,
            )
        except (TransientBackendError, BackendUnavailable):
            # A transiently-degraded / circuit-broken endpoint is NOT
            # human-actionable and MUST NOT advance the tasks stage (bug-#8
            # principle; parity with run_stage_panel). Re-raise AS-IS so
            # run_one_step fails transiently and the project STAYS at PLANNED to
            # retry when the endpoint recovers — rather than swallowing the
            # failure and advancing to TASKED as though the panel had accepted.
            raise
        except Exception as exc:
            print(
                f"[tasker/engine] engine path raised: {exc}; "
                "marking non-converged + leaving on-disk artifacts unchanged"
            )
            rounds_marker = (
                ctx.project_dir / ".specify" / "memory" / "tasker_rounds.yaml"
            )
            rounds_marker.parent.mkdir(parents=True, exist_ok=True)
            rounds_marker.write_text(
                yaml.safe_dump({"rounds_used": 1, "converged": False}),
                encoding="utf-8",
            )
            return

        # Adaptive kickback (spec-015 F-20 Part B) — parity with the spec/plan
        # panels: when the tasks convergence panel does NOT converge, emit the
        # adaptive sentinel and raise StagePanelKickback so run_one_step routes
        # the project back to the panel's kickback target (a writing-only nit →
        # forward to TASKED; a deeper unresolved concern → self-loop at PLANNED to
        # re-task), bounded by the per-stage kickback cap. Previously the tasker
        # swallowed non-convergence into tasker_rounds.yaml and the project
        # advanced as though the panel had accepted. The engine already persisted
        # the per-round convergence trail.
        _conv = engine_result.convergence
        if not _conv.converged and _conv.kickback is not None:
            from llmxive.speckit._stage_panel import (
                StagePanelKickback,
                emit_convergence_kickback,
            )

            emit_convergence_kickback(
                ctx.project_dir / ".specify" / "memory",
                _conv.kickback,
                stage_label="tasks",
            )
            raise StagePanelKickback(
                f"tasks panel did not converge: {_conv.kickback.reason} "
                f"(kickback → {_conv.kickback.to_stage})"
            )

        _round_after = {
            "spec.md": spec_path.read_text(encoding="utf-8") if spec_path.exists() else "",
            "plan.md": plan_path.read_text(encoding="utf-8") if plan_path.exists() else "",
            "tasks.md": tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else "",
        }
        _files_rewritten = [
            fn for fn in ("spec.md", "plan.md", "tasks.md")
            if _round_before[fn] != _round_after[fn]
        ]
        _round_diffs = {
            fn: _unified_diff(_round_before[fn], _round_after[fn], fn)
            for fn in _files_rewritten
        }

        # ---- Final analyze + honest reporting (FR-016) ----
        try:
            final_report = run_analyze(
                spec_text=spec_path.read_text(encoding="utf-8"),
                plan_text=plan_path.read_text(encoding="utf-8"),
                tasks_text=tasks_path.read_text(encoding="utf-8"),
                default_backend=ctx.default_backend,
                fallback_backends=ctx.fallback_backends,
                default_model=ctx.default_model,
                repo_root=repo,
                project_dir=ctx.project_dir,
                kind="research",
                constitution_text=_const_text,
            )
            final_clean = is_clean(final_report)
        except _BackendError as exc:
            # If the final analyze can't run, fall back to the engine's
            # `converged` flag for the honest verdict.
            print(
                f"[tasker/engine] final analyze failed: {exc}; "
                "trusting engine convergence flag for verdict"
            )
            final_report = "ANALYZER_UNAVAILABLE"
            final_clean = engine_result.convergence.converged

        rounds_used = max(1, engine_result.convergence.rounds_used + 1)
        self._inspection_rounds.append({
            "round_index": 0,
            "analyze_report": first_report,
            "mode_b_patch": None,
            "verdict": "engine_dispatched",
            "files_rewritten": _files_rewritten,
            "diffs": _round_diffs,
        })
        self._inspection_rounds.append({
            "round_index": 1,
            "analyze_report": final_report,
            "mode_b_patch": None,
            "verdict": "clean" if final_clean else "non_converged",
            "files_rewritten": [],
            "diffs": {},
        })
        rounds_marker = (
            ctx.project_dir / ".specify" / "memory" / "tasker_rounds.yaml"
        )
        rounds_marker.parent.mkdir(parents=True, exist_ok=True)
        rounds_marker.write_text(
            yaml.safe_dump({
                "rounds_used": rounds_used,
                "converged": final_clean,
                "path": "engine",
            }),
            encoding="utf-8",
        )


def _parse_tasker_response(text: str) -> dict[str, Any] | None:
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
        parsed = _json.loads(inner)
        return parsed if isinstance(parsed, dict) else None
    except _json.JSONDecodeError:
        pass

    # Try JSON with raw newlines inside strings auto-escaped. We walk
    # the text in/out of double-quoted regions and replace literal
    # control chars with their JSON-escaped form.
    try:
        parsed = _json.loads(_escape_newlines_in_json_strings(inner))
        return parsed if isinstance(parsed, dict) else None
    except _json.JSONDecodeError:
        pass

    # Try lenient YAML.
    try:
        parsed = _parse_yaml(inner)
        return parsed if isinstance(parsed, dict) else None
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
