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
from datetime import UTC, datetime
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
    # Spec 009 FR-026: activity-feed context block injected by runner BEFORE
    # any other project-scoped instruction. Empty when no feed is available
    # (e.g. project has no activity.jsonl yet).
    feed_context: str = ""
    # Spec 009 FR-027/FR-028: ULID identifying this dispatch; required to be
    # echoed back in the agent's comments-considered manifest.
    dispatch_id: str = ""
    # Spec 009 FR-031: True iff the packed feed included a "[truncated N earlier
    # items]" marker; the agent's manifest MUST acknowledge truncation when set.
    feed_truncated: bool = False
    # Spec 009 FR-033: ISO 8601 snapshot timestamp of the feed delivered to the
    # agent — used by the post-tick validator to detect concurrent-write races.
    feed_snapshot_at: str = ""


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
        started = datetime.now(UTC)
        outcome = Outcome.SUCCESS
        failure_reason: str | None = None
        outputs: list[str] = []
        backend_used = self.entry.default_backend
        model_used = self.entry.default_model
        # Spec 015 T080: capture verbatim I/O for inspection-record audit
        # when LLMXIVE_INSPECTION_DIR is set. Mirrors the speckit
        # SlashCommandAgent's inspection-capture flow so flesh_out /
        # validator / brainstorm and every other non-speckit Agent
        # subclass appears in the audit trail too.
        captured_messages: list[ChatMessage] | None = None
        captured_response: ChatResponse | None = None

        try:
            messages = self.build_messages(ctx)
            captured_messages = messages
            response = chat_with_fallback(
                messages,
                default_backend=self.entry.default_backend.value,
                fallback_backends=[b.value for b in self.entry.fallback_backends],
                model=self.entry.default_model,
            )
            captured_response = response
            backend_used = BackendName(response.backend)
            model_used = response.model
            outputs = self.handle_response(ctx, response)
        except Exception as exc:
            outcome = Outcome.FAILED
            failure_reason = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            ended = datetime.now(UTC)
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
            # Inspection-record capture (spec 015 T080 — closes design §9
            # gap). No-op unless LLMXIVE_INSPECTION_DIR is set. Failures
            # in the inspection writer NEVER propagate — agent invocations
            # must succeed even if audit capture fails.
            _capture_non_speckit_inspection(
                agent=self,
                ctx=ctx,
                started=started,
                ended=ended,
                outcome=outcome,
                failure_reason=failure_reason,
                outputs=outputs,
                model=model_used,
                backend=backend_used.value if hasattr(backend_used, "value") else str(backend_used),
                messages=captured_messages,
                response=captured_response,
            )
        return entry


def _capture_non_speckit_inspection(
    *,
    agent: Agent,
    ctx: AgentContext,
    started: datetime,
    ended: datetime,
    outcome: Outcome,
    failure_reason: str | None,
    outputs: list[str],
    model: str,
    backend: str,
    messages: list[ChatMessage] | None,
    response: ChatResponse | None,
) -> None:
    """Spec 015 T080 — write a per-invocation inspection record for
    non-speckit ``Agent`` subclasses (flesh_out, validator, brainstorm,
    status_reporter, etc.), closing the design §9 gap where the existing
    inspection hook only fired for ``SlashCommandAgent``.

    No-op unless ``LLMXIVE_INSPECTION_DIR`` is set. Records land at
    ``<LLMXIVE_INSPECTION_DIR>/non-speckit/<project_id>/<agent_name>.json``
    using the same JSON schema as the speckit inspection records. Errors
    in the writer are LOGGED but never raised — the agent invocation
    must succeed even if audit capture fails (otherwise enabling
    inspection would itself become a fault-injection vector).
    """
    import logging
    import os

    inspection_dir = os.environ.get("LLMXIVE_INSPECTION_DIR")
    if not inspection_dir:
        return

    try:
        # We bypass speckit `capture()` (which writes to
        # `<spec_root>/inspections/<project_id>/<agent_name>.json` — a
        # layout tied to per-project spec roots) and write directly to
        # `<inspection_dir>/non-speckit/<project_id>/<agent_name>.json`.
        # The JSON schema MATCHES the speckit record (downstream audit
        # tooling reads them identically); only the path differs.
        import json as _json

        from llmxive.speckit._inspection import _atomic_write, _redact

        # Map Outcome → speckit vocabulary
        # ({"committed", "abstained", "failed", "held", "no-op", "escalated"}).
        outcome_map = {
            Outcome.SUCCESS: "committed",
            Outcome.FAILED: "failed",
            Outcome.SKIPPED: "no-op",
        }
        outcome_value = outcome_map.get(outcome, "failed")

        # Messages → prompts dict (concat by role to fit speckit schema).
        prompts = {"system": "", "user": ""}
        if messages:
            sys_parts = [m.content for m in messages if m.role == "system"]
            usr_parts = [m.content for m in messages if m.role == "user"]
            prompts["system"] = "\n\n".join(sys_parts)
            prompts["user"] = "\n\n".join(usr_parts)

        raw_response = response.text if response is not None else ""
        file_diffs = [{"path": p, "before": "", "after": ""} for p in outputs]

        record = {
            "project_id": ctx.project_id,
            "agent_name": agent.name,
            "agent_version": agent.entry.prompt_version,
            "model": model,
            "backend": backend,
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "duration_s": (ended - started).total_seconds(),
            "outcome": outcome_value,
            "reset_artifacts": [],
            "prompts": {
                "system": _redact(prompts.get("system", "")),
                "user": _redact(prompts.get("user", "")),
            },
            "raw_response": _redact(raw_response),
            "parsed_output": {},
            "file_diffs": file_diffs,
            "error": failure_reason if outcome_value == "failed" else None,
            "rounds": [],
        }

        out_path = (
            Path(inspection_dir) / "non-speckit" / ctx.project_id /
            f"{agent.name}.json"
        )
        _atomic_write(
            out_path,
            _json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        )
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "inspection-capture failed for agent %s: %s", agent.name, exc,
        )


__all__ = ["Agent", "AgentContext"]
