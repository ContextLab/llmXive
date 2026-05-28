"""Inspection-record capture for non-speckit Agent subclasses (spec 015 T080).

Verifies the new ``_capture_non_speckit_inspection`` hook in
``src/llmxive/agents/base.py``:

- No-op when ``LLMXIVE_INSPECTION_DIR`` is unset.
- Writes ``<inspection_dir>/non-speckit/<project_id>/<agent_name>.json``
  when set, matching the speckit inspection schema.
- Failures in the inspection writer NEVER propagate (an audit fault must
  not break agent execution).
- Successful agent runs map Outcome.SUCCESS → ``"committed"``; failed
  agent runs map Outcome.FAILED → ``"failed"``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from llmxive.agents.base import Agent, AgentContext
from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.types import BackendName

# --- Test doubles ---------------------------------------------------------


@dataclass
class _FakeRegistryEntry:
    """Minimal AgentRegistryEntry shape the test needs."""

    name: str = "fake_test_agent"
    prompt_version: str = "1.0.0"
    default_model: str = "fake-model"
    default_backend: BackendName = BackendName.DARTMOUTH
    fallback_backends: list[BackendName] = field(default_factory=list)


class _FakeAgent(Agent):
    """Concrete Agent subclass for testing. Doesn't actually call an LLM;
    monkeypatches in the test replace `chat_with_fallback`."""

    def build_messages(self, ctx: AgentContext) -> list[ChatMessage]:
        return [
            ChatMessage(role="system", content="you are a test agent"),
            ChatMessage(role="user", content=f"do the thing for {ctx.project_id}"),
        ]

    def handle_response(self, ctx: AgentContext, response: ChatResponse) -> list[str]:
        return ["projects/PROJ-001-test/output.md"]


def _make_ctx(project_id: str = "PROJ-001-test") -> AgentContext:
    return AgentContext(
        project_id=project_id,
        run_id="run-1",
        task_id="task-1",
        inputs=[],
    )


# --- Tests ----------------------------------------------------------------


def test_no_inspection_dir_means_no_record_written(monkeypatch, tmp_path: Path):
    """When LLMXIVE_INSPECTION_DIR is unset, the agent runs normally but
    no inspection record is written."""
    monkeypatch.delenv("LLMXIVE_INSPECTION_DIR", raising=False)

    # Stub the runlog + chat_with_fallback so the agent runs without
    # touching real state or making network calls.
    from llmxive.agents import base as base_mod
    monkeypatch.setattr(base_mod.runlog, "append_entry", lambda entry: None)
    monkeypatch.setattr(
        base_mod, "chat_with_fallback",
        lambda *a, **kw: ChatResponse(text="ok", model="m", backend="dartmouth"),
    )

    agent = _FakeAgent(_FakeRegistryEntry())  # type: ignore[arg-type]
    agent.run(_make_ctx())

    # No inspection records produced anywhere under tmp_path.
    inspection_files = list(tmp_path.rglob("*.json"))
    assert inspection_files == []


def test_success_run_writes_committed_inspection_record(monkeypatch, tmp_path: Path):
    """When LLMXIVE_INSPECTION_DIR is set, a successful Agent.run() writes
    an inspection record with outcome 'committed' under
    ``<dir>/non-speckit/<project_id>/<agent_name>.json``."""
    monkeypatch.setenv("LLMXIVE_INSPECTION_DIR", str(tmp_path))

    from llmxive.agents import base as base_mod
    monkeypatch.setattr(base_mod.runlog, "append_entry", lambda entry: None)
    monkeypatch.setattr(
        base_mod, "chat_with_fallback",
        lambda *a, **kw: ChatResponse(text="hello", model="fake-model", backend="dartmouth"),
    )

    agent = _FakeAgent(_FakeRegistryEntry())  # type: ignore[arg-type]
    agent.run(_make_ctx())

    expected = tmp_path / "non-speckit" / "PROJ-001-test" / "fake_test_agent.json"
    assert expected.exists(), f"expected inspection record at {expected}"

    record = json.loads(expected.read_text())
    assert record["project_id"] == "PROJ-001-test"
    assert record["agent_name"] == "fake_test_agent"
    assert record["outcome"] == "committed"
    assert record["raw_response"] == "hello"
    assert "you are a test agent" in record["prompts"]["system"]
    assert "do the thing for PROJ-001-test" in record["prompts"]["user"]


def test_failed_run_writes_failed_inspection_record(monkeypatch, tmp_path: Path):
    """When the agent raises, the inspection record's outcome is 'failed'
    and the error field is populated."""
    monkeypatch.setenv("LLMXIVE_INSPECTION_DIR", str(tmp_path))

    from llmxive.agents import base as base_mod
    monkeypatch.setattr(base_mod.runlog, "append_entry", lambda entry: None)

    def _raise(*a, **kw):
        raise RuntimeError("simulated LLM failure")

    monkeypatch.setattr(base_mod, "chat_with_fallback", _raise)
    agent = _FakeAgent(_FakeRegistryEntry())  # type: ignore[arg-type]
    with pytest.raises(RuntimeError, match="simulated LLM failure"):
        agent.run(_make_ctx())

    expected = tmp_path / "non-speckit" / "PROJ-001-test" / "fake_test_agent.json"
    assert expected.exists()
    record = json.loads(expected.read_text())
    assert record["outcome"] == "failed"
    assert record["error"] is not None
    assert "simulated LLM failure" in record["error"]


def test_inspection_capture_failure_does_not_break_agent_run(
    monkeypatch, tmp_path: Path, caplog
):
    """The inspection writer's failure path MUST NOT propagate — an
    audit-capture fault is not allowed to break agent execution. Set
    LLMXIVE_INSPECTION_DIR to a read-only location so the writer fails;
    verify the agent's `run()` still returns successfully + a warning
    is logged."""
    # Point inspection at a non-existent + non-writable parent path.
    bad_dir = tmp_path / "readonly" / "blocked"
    tmp_path.chmod(0o555)  # remove write on tmp_path itself
    try:
        monkeypatch.setenv("LLMXIVE_INSPECTION_DIR", str(bad_dir))

        from llmxive.agents import base as base_mod
        monkeypatch.setattr(base_mod.runlog, "append_entry", lambda entry: None)
        monkeypatch.setattr(
            base_mod, "chat_with_fallback",
            lambda *a, **kw: ChatResponse(text="ok", model="m", backend="dartmouth"),
        )

        agent = _FakeAgent(_FakeRegistryEntry())  # type: ignore[arg-type]
        # Critical assertion: run() returns normally despite the writer
        # being unable to land its file.
        entry = agent.run(_make_ctx())
        assert entry is not None  # success
    finally:
        # Restore writability so pytest can clean up tmp_path.
        tmp_path.chmod(0o755)
