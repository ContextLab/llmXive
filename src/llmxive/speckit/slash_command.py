"""Base class for an agent that drives a Spec Kit slash command (T022).

Each Spec-Kit-driving agent (Specifier, Clarifier, Planner, Tasker,
Implementer, and their paper-stage analogs) extends this base class.

Per FR-014, every invocation: (1) calls the slash command's mechanical
bash script (headless --json) once, (2) loads the slash command's
authored prompt from upstream `.specify/templates/` or
`.claude/skills/speckit-*/SKILL.md` — referenced by path, never copied
(Principle I), (3) calls the LLM via the configured backend chain, (4)
writes artifacts at canonical Spec Kit paths, (5) appends a run-log
entry.

Opt-in inspection hook (spec 011 / FR-003): when the environment variable
``LLMXIVE_INSPECTION_DIR`` is set, ``run()`` ALSO writes a per-invocation
inspection record (via :mod:`llmxive.speckit._inspection`) to
``<LLMXIVE_INSPECTION_DIR>/<agent_name>.json`` capturing the verbatim
system + user prompts, the raw LLM response, and outcome metadata.
Production cron jobs leave the env var unset, so this is a strict no-op
unless explicitly enabled by the spec-011 validation harness.
"""

from __future__ import annotations

import abc
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.backends.router import chat_with_fallback
from llmxive.state import runlog
from llmxive.types import (
    BackendName,
    Outcome,
    RunLogEntry,
)


@dataclass
class SlashCommandContext:
    project_id: str
    project_dir: Path
    run_id: str
    task_id: str
    inputs: list[str]
    expected_outputs: list[str]
    prompt_template_path: Path
    default_backend: BackendName
    fallback_backends: list[BackendName]
    default_model: str
    prompt_version: str
    agent_name: str


class SlashCommandAgent(abc.ABC):
    """Base for an agent that drives one Spec Kit slash command."""

    @abc.abstractmethod
    def slash_command_name(self) -> str:
        """e.g. 'speckit.specify', 'speckit.plan'."""

    @abc.abstractmethod
    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        """Invoke the slash command's bash script and return its parsed JSON."""

    @abc.abstractmethod
    def build_prompt(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
    ) -> list[ChatMessage]:
        """Combine the upstream slash-command prompt template with project state."""

    @abc.abstractmethod
    def write_artifacts(
        self,
        ctx: SlashCommandContext,
        mechanical_output: dict[str, Any],
        llm_response: ChatResponse,
    ) -> list[str]:
        """Persist the LLM's response at canonical Spec Kit paths.

        Returns the list of artifact paths written.
        """

    def run(self, ctx: SlashCommandContext) -> RunLogEntry:
        started = datetime.now(UTC)
        outcome = Outcome.SUCCESS
        failure_reason: str | None = None
        outputs: list[str] = []
        backend_used: BackendName = ctx.default_backend
        model_used: str = ctx.default_model
        # Spec 011 inspection-hook locals — initialized so the finally block
        # can capture even when build_prompt or chat_with_fallback raises.
        messages: list[ChatMessage] = []
        llm_response_text: str = ""

        try:
            mechanical_output = self.mechanical_step(ctx)
            messages = self.build_prompt(ctx, mechanical_output)
            llm_response = chat_with_fallback(
                messages,
                default_backend=ctx.default_backend.value,
                fallback_backends=[b.value for b in ctx.fallback_backends],
                model=ctx.default_model,
            )
            backend_used = BackendName(llm_response.backend)
            model_used = llm_response.model
            llm_response_text = llm_response.text
            outputs = self.write_artifacts(ctx, mechanical_output, llm_response)
            # FR-026 point 1: validate citations on every artifact write.
            _validate_artifact_citations(ctx, outputs)
        except Exception as exc:
            outcome = Outcome.FAILED
            failure_reason = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            ended = datetime.now(UTC)
            entry = RunLogEntry(
                run_id=ctx.run_id,
                entry_id=str(uuid4()),
                agent_name=ctx.agent_name,
                project_id=ctx.project_id,
                task_id=ctx.task_id,
                inputs=ctx.inputs,
                outputs=outputs,
                backend=backend_used,
                model_name=model_used,
                prompt_version=ctx.prompt_version,
                started_at=started,
                ended_at=ended,
                outcome=outcome,
                failure_reason=failure_reason,
                cost_estimate_usd=0.0,
            )
            runlog.append_entry(entry)
            _maybe_write_inspection(
                agent=self,
                ctx=ctx, started=started, ended=ended, outcome=outcome,
                failure_reason=failure_reason, messages=messages,
                llm_response_text=llm_response_text, model_used=model_used,
                backend_used=backend_used,
            )
        return entry


def _maybe_write_inspection(
    *,
    ctx: SlashCommandContext,
    started: datetime,
    ended: datetime,
    outcome: Outcome,
    failure_reason: str | None,
    messages: list[ChatMessage],
    llm_response_text: str,
    model_used: str,
    backend_used: BackendName,
    agent: SlashCommandAgent | None = None,
) -> None:
    """Spec 011 / FR-003 inspection-record hook (opt-in via env var).

    No-op unless ``LLMXIVE_INSPECTION_DIR`` is set. When set, writes a
    minimal per-invocation record to ``<env_dir>/<agent_name>.json``
    capturing the verbatim system + user prompts, the raw LLM response,
    timestamps, model, backend, and outcome. The validation harness
    (``scripts/validate_phase3.py``) augments this record post-hoc with
    file_diffs and reset_artifacts (which the agent doesn't know about).
    Any hook failure is swallowed — never block the agent on inspection.
    """
    env_dir = os.environ.get("LLMXIVE_INSPECTION_DIR")
    if not env_dir:
        return
    try:
        from llmxive.speckit._inspection import capture
        sys_prompt = next((m.content for m in messages if m.role == "system"), "")
        usr_prompt = next((m.content for m in messages if m.role == "user"), "")
        # spec 014 / FR-004: an agent that ran an analyze loop (the Tasker)
        # accumulates per-round sub-records on ``_inspection_rounds``; capture
        # them here. Every other agent leaves the attribute unset → ``[]``.
        rounds = list(getattr(agent, "_inspection_rounds", []) or [])
        capture(
            project_id=ctx.project_id,
            agent_name=ctx.agent_name,
            agent_version=ctx.prompt_version,
            model=model_used,
            backend=backend_used.value if hasattr(backend_used, "value") else str(backend_used),
            started_at=started,
            ended_at=ended,
            outcome=("committed" if outcome == Outcome.SUCCESS else "failed"),
            prompts={"system": sys_prompt, "user": usr_prompt},
            raw_response=llm_response_text,
            parsed_output={},
            file_diffs=[],
            reset_artifacts=[],
            error=failure_reason,
            spec_root=Path(env_dir).parent.parent,  # env points at .../inspections/<project_id>; spec_root = .../  (two parents up)
            rounds=rounds,
        )
    except Exception:
        pass


def _validate_artifact_citations(
    ctx: SlashCommandContext, outputs: list[str]
) -> None:
    """Run the Reference-Validator over every newly-written artifact.

    Per FR-026 point 1: citations are verified at every artifact write.
    Failures are recorded in `state/citations/<PROJ-ID>.yaml` but do
    NOT raise — the Advancement-Evaluator gates on the persisted
    state at point 2 (review-point award) and point 3 (final accept
    transition).

    Skipped for non-Markdown artifacts (no citation extraction yet for
    binary or code).
    """
    # Lazy import to avoid a cycle: speckit -> agents.reference_validator
    # would form a cycle on package import.
    from llmxive.agents.reference_validator import validate_artifact
    from llmxive.state.project import hash_file

    repo = ctx.project_dir.parent.parent
    for relpath in outputs:
        path = repo / relpath
        if not path.exists() or not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".markdown", ".tex"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        try:
            validate_artifact(
                project_id=ctx.project_id,
                artifact_path=relpath,
                artifact_text=text,
                artifact_hash=hash_file(path),
                repo_root=repo,
            )
        except Exception:
            # Non-fatal: validation is best-effort during artifact writes.
            # The blocking gates upstream (Advancement-Evaluator) re-check
            # the persisted citations YAML on every transition decision.
            continue


__all__ = ["SlashCommandAgent", "SlashCommandContext"]
