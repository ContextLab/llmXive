import json
from pathlib import Path

from llmxive_toolkit import paths

def test_validation_by_session_file_exists():
    """Basic sanity check that the aggregated file is created."""
    out_path = paths.results("validation_by_session.jsonl")
    assert out_path.is_file(), f"Expected {out_path} to exist"

def test_validation_by_session_schema():
    """Each line must contain the required keys and correct types."""
    out_path = paths.results("validation_by_session.jsonl")
    with out_path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            assert "session_id" in record, "Missing session_id"
            assert "task_id" in record, "Missing task_id"
            assert "overall_success" in record, "Missing overall_success"
            assert isinstance(record["session_id"], str)
            assert isinstance(record["task_id"], str)
            assert isinstance(record["overall_success"], bool)