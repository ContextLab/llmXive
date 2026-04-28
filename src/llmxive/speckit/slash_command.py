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
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from datetime import datetime, timezone
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
        started = datetime.now(timezone.utc)
        outcome = Outcome.SUCCESS
        failure_reason: str | None = None
        outputs: list[str] = []
        backend_used: BackendName = ctx.default_backend
        model_used: str = ctx.default_model

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
            outputs = self.write_artifacts(ctx, mechanical_output, llm_response)
        except Exception as exc:
            outcome = Outcome.FAILED
            failure_reason = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            ended = datetime.now(timezone.utc)
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
        return entry


__all__ = ["SlashCommandAgent", "SlashCommandContext"]
