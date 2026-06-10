"""Issue #294 typed-boundary work — ``Agent.run`` retries with the
validation error fed back when ``handle_response`` raises
``MalformedResponseError``.

Motivating live failures: run-log 2026-06-05..08 shows every
``google.gemma-4-31B-it`` fallback reviewer call dying fatally on
"response missing YAML frontmatter" with no second chance. The retry
loop re-prompts with the concrete validator error (the structured-output
retry pattern), bounded by ``MAX_MALFORMED_RESPONSE_RETRIES``
(Constitution V: bounded, not retry-forever).
"""

from __future__ import annotations

import pytest

from llmxive.agents import base as agent_base
from llmxive.agents.base import (
    MAX_MALFORMED_RESPONSE_RETRIES,
    Agent,
    AgentContext,
    MalformedResponseError,
)
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.types import AgentRegistryEntry, Outcome


def _entry() -> AgentRegistryEntry:
    return AgentRegistryEntry(
        name="format_probe",
        purpose="exercise the malformed-response retry loop",
        prompt_path="agents/prompts/research_reviewer.md",
        prompt_version="1.0.0",
        default_backend="dartmouth",
        fallback_backends=[],
        default_model="qwen.qwen3.5-122b",
        wall_clock_budget_seconds=60,
        paid_opt_in=False,
    )


class FormatProbeAgent(Agent):
    """Accepts only responses whose text is exactly 'VALID'."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        return [ChatMessage(role="user", content="emit VALID")]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        if response.text != "VALID":
            raise MalformedResponseError(
                f"expected literal VALID, got {response.text!r}",
                format_reminder="Reply with the single word VALID.",
            )
        return ["ok-artifact"]


@pytest.fixture
def ctx() -> AgentContext:
    return AgentContext(
        project_id="PROJ-999-retry-probe",
        run_id="run-1",
        task_id="task-1",
        inputs=[],
    )


@pytest.fixture(autouse=True)
def _quiet_runlog(monkeypatch):
    monkeypatch.setattr("llmxive.state.runlog.append_entry", lambda entry: None)


def _scripted_chat(monkeypatch, replies: list[str]):
    """chat_with_fallback double returning scripted texts, capturing calls."""
    calls: list[list[ChatMessage]] = []

    def fake_chat(messages, **kwargs):
        calls.append(list(messages))
        text = replies[min(len(calls) - 1, len(replies) - 1)]
        return ChatResponse(
            text=text, model="fake-model", backend="dartmouth",
            cost_estimate_usd=0.0,
        )

    monkeypatch.setattr(agent_base, "chat_with_fallback", fake_chat)
    return calls


def test_valid_first_response_no_retry(monkeypatch, ctx):
    calls = _scripted_chat(monkeypatch, ["VALID"])
    entry = FormatProbeAgent(_entry()).run(ctx)
    assert entry.outcome == Outcome.SUCCESS
    assert len(calls) == 1


def test_malformed_then_valid_recovers_with_feedback(monkeypatch, ctx):
    calls = _scripted_chat(monkeypatch, ["```yaml nonsense```", "VALID"])
    entry = FormatProbeAgent(_entry()).run(ctx)
    assert entry.outcome == Outcome.SUCCESS
    assert entry.outputs == ["ok-artifact"]
    assert len(calls) == 2

    # The retry conversation must carry: original messages + the rejected
    # assistant turn + a user turn containing the validation error AND the
    # contract-specific format reminder.
    retry_messages = calls[1]
    assert retry_messages[0].content == "emit VALID"
    assert retry_messages[1].role == "assistant"
    assert retry_messages[1].content == "```yaml nonsense```"
    assert retry_messages[2].role == "user"
    assert "expected literal VALID" in retry_messages[2].content
    assert "Reply with the single word VALID." in retry_messages[2].content


def test_retries_bounded_then_fails(monkeypatch, ctx):
    calls = _scripted_chat(monkeypatch, ["bad"])  # always malformed
    with pytest.raises(MalformedResponseError):
        FormatProbeAgent(_entry()).run(ctx)
    assert len(calls) == MAX_MALFORMED_RESPONSE_RETRIES + 1


def test_non_validation_errors_do_not_retry(monkeypatch, ctx):
    """Only MalformedResponseError triggers the loop — other failures keep
    fail-fast semantics."""
    calls = _scripted_chat(monkeypatch, ["VALID"])

    class ExplodingAgent(FormatProbeAgent):
        def handle_response(self, ctx, response):
            raise OSError("disk full")

    with pytest.raises(OSError):
        ExplodingAgent(_entry()).run(ctx)
    assert len(calls) == 1
