"""A run log records the model that ANSWERED — never one invented before the call."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from llmxive.types import BackendName, Outcome, RunLogEntry


def _entry(**kw):
    now = datetime.now(UTC)
    base = dict(
        run_id="r1", entry_id="e1", agent_name="brainstorm", project_id="PROJ-001-x",
        task_id="t1", inputs=[], outputs=[], prompt_version="1.0.0",
        started_at=now, ended_at=now, outcome=Outcome.SUCCESS,
        backend=BackendName.DARTMOUTH, model_name="qwen.qwen3.5-122b",
        cost_estimate_usd=0.0,
    )
    base.update(kw)
    return RunLogEntry(**base)


def test_failure_before_any_call_records_no_attribution():
    e = _entry(outcome=Outcome.FAILED, backend=None, model_name=None,
               failure_reason="BackendUnavailable")
    assert e.backend is None and e.model_name is None


def test_success_requires_both_fields():
    with pytest.raises(ValueError):
        _entry(backend=None)
    with pytest.raises(ValueError):
        _entry(model_name=None)


def test_success_with_both_is_valid():
    assert _entry().model_name == "qwen.qwen3.5-122b"
