import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

def test_validation_by_session_output():
    """
    Verify that the aggregated validation‑by‑session file exists and
    conforms to a minimal schema: each line must contain
    ``session_id``, ``task_id`` and ``overall_success`` (bool).
    """
    result_path = paths.results("validation_by_session.jsonl")
    assert result_path.is_file(), f"Expected {result_path} to exist"

    with result_path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            assert "session_id" in record, "Missing session_id"
            assert "task_id" in record, "Missing task_id"
            assert "overall_success" in record, "Missing overall_success"
            assert isinstance(record["overall_success"], bool), "overall_success must be bool"