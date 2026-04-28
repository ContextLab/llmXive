"""Agent base class (T023).

Every agent in agents/registry.yaml extends Agent. The base class
declares input/output artifact types, default backend, fallback chain,
prompt path, prompt version, wall-clock budget, and emits a run-log
entry on every invocation.

Spec-Kit-driving agents extend `SlashCommandAgent` (in speckit/) instead;
non-Spec-Kit agents (e.g., Brainstorm, Reference-Validator,
Status-Reporter) extend Agent directly.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.backends.router import chat_with_fallback
from llmxive.state import runlog
from llmxive.types import (
    AgentRegistryEntry,
    BackendName,
    Outcome,
    RunLogEntry,
)


@dataclass
class AgentContext:
    project_id: str
    run_id: str
    task_id: str
    inputs: list[str]
    expected_outputs: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


class Agent(abc.ABC):
    """Base class for non-Spec-Kit-driving specialist agents."""

    def __init__(self, registry_entry: AgentRegistryEntry) -> None:
        self.entry = registry_entry

    @property
    def name(self) -> str:
        return self.entry.name

    @abc.abstractmethod
    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        """Compose the LLM input — usually system prompt + project context."""

    @abc.abstractmethod
    def handle_response(
        self,
        ctx: AgentContext,
        response: ChatResponse,
    ) -> list[str]:
        """Persist outputs from the LLM response. Returns artifact paths."""

    def run(self, ctx: AgentContext) -> RunLogEntry:
        started = datetime.now(timezone.utc)
        outcome = Outcome.SUCCESS
        failure_reason: str | None = None
        outputs: list[str] = []
        backend_used = self.entry.default_backend
        model_used = self.entry.default_model

        try:
            messages = self.build_messages(ctx)
            response = chat_with_fallback(
                messages,
                default_backend=self.entry.default_backend.value,
                fallback_backends=[b.value for b in self.entry.fallback_backends],
                model=self.entry.default_model,
            )
            backend_used = BackendName(response.backend)
            model_used = response.model
            outputs = self.handle_response(ctx, response)
        except Exception as exc:
            outcome = Outcome.FAILED
            failure_reason = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            ended = datetime.now(timezone.utc)
            entry = RunLogEntry(
                run_id=ctx.run_id,
                entry_id=str(uuid4()),
                agent_name=self.name,
                project_id=ctx.project_id,
                task_id=ctx.task_id,
                inputs=ctx.inputs,
                outputs=outputs,
                backend=backend_used,
                model_name=model_used,
                prompt_version=self.entry.prompt_version,
                started_at=started,
                ended_at=ended,
                outcome=outcome,
                failure_reason=failure_reason,
                cost_estimate_usd=0.0,
            )
            runlog.append_entry(entry)
        return entry


__all__ = ["Agent", "AgentContext"]
