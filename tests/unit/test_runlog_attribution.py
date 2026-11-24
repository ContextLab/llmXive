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


def test_unattributed_failure_is_persisted_by_the_real_run_log(tmp_path):
    """The on-disk contract agrees with the model: a failed run with no
    attribution is APPENDED (not parked as invalid) and reads back unchanged.
    Before the schema allowed null here, every pre-response failure raised a
    contract ValidationError from the caller's ``finally`` block."""
    import uuid

    from llmxive.state import runlog

    run_id = str(uuid.uuid4())
    entry = _entry(run_id=run_id, entry_id=str(uuid.uuid4()), outcome=Outcome.FAILED,
                   backend=None, model_name=None, failure_reason="BackendUnavailable")
    path = runlog.append_entry(entry, repo_root=tmp_path)
    assert path.is_file() and not (path.parent / ".invalid").exists()
    (read_back,) = runlog.read_entries(run_id, repo_root=tmp_path)
    assert read_back.backend is None and read_back.model_name is None
    assert read_back.outcome is Outcome.FAILED


@pytest.mark.parametrize("missing", ["backend", "model_name"])
def test_contract_schema_rejects_an_unattributed_success(missing):
    """The JSON contract enforces the same rule as the model, independently."""
    import uuid

    from jsonschema import ValidationError

    from llmxive.contract_validate import validate

    payload = _entry(run_id=str(uuid.uuid4()), entry_id=str(uuid.uuid4())).model_dump(mode="json")
    validate("run-log-entry", payload)  # a fully attributed success is valid
    payload[missing] = None
    with pytest.raises(ValidationError):
        validate("run-log-entry", payload)
