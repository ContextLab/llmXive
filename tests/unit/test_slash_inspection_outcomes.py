"""Skipped and interrupted calls replace stale inspection records honestly."""
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from llmxive.speckit import slash_command as slash
from llmxive.types import BackendName, Outcome


def context(root):
    return slash.SlashCommandContext(
        project_id="PROJ-001-test", project_dir=root / "projects/PROJ-001-test", run_id=str(uuid4()),
        task_id=str(uuid4()), inputs=[], expected_outputs=[], prompt_template_path=Path("unused"),
        default_backend=BackendName.DARTMOUTH, fallback_backends=[], default_model="test",
        prompt_version="1.0.0", agent_name="implementer",
    )


def test_skipped_response_replaces_previous_success(tmp_path, monkeypatch):
    monkeypatch.setenv("LLMXIVE_INSPECTION_DIR", str(tmp_path / "notes/inspections"))
    ctx = context(tmp_path)
    now = datetime.now(UTC)
    for outcome, text in [(Outcome.SUCCESS, "old output"), (Outcome.SKIPPED, "malformed YAML response")]:
        slash._maybe_write_inspection(ctx=ctx, started=now, ended=now, outcome=outcome,
                                      failure_reason=None, messages=[], llm_response_text=text,
                                      model_used="test", backend_used=BackendName.DARTMOUTH)
    record = json.loads((tmp_path / "inspections/PROJ-001-test/implementer.json").read_text())
    assert record["outcome"] == "no-op"
    assert record["raw_response"] == "malformed YAML response"
    assert record["error"] is None


def test_interrupt_is_failed_in_both_log_and_inspection(tmp_path, monkeypatch):
    monkeypatch.setenv("LLMXIVE_INSPECTION_DIR", str(tmp_path / "notes/inspections"))
    entries = []
    monkeypatch.setattr(slash.runlog, "append_entry", lambda entry, **kw: entries.append(entry))

    class Interrupted(slash.SlashCommandAgent):
        def slash_command_name(self): return "test"
        def mechanical_step(self, ctx): raise KeyboardInterrupt()
        def build_prompt(self, ctx, mechanical_output): raise AssertionError("unreachable")
        def write_artifacts(self, ctx, mechanical_output, llm_response): raise AssertionError("unreachable")

    with pytest.raises(KeyboardInterrupt):
        Interrupted().run(context(tmp_path))
    assert entries[0].outcome == Outcome.FAILED
    record = json.loads((tmp_path / "inspections/PROJ-001-test/implementer.json").read_text())
    assert record["outcome"] == "failed"
    assert "KeyboardInterrupt" in record["error"]
