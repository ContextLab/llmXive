"""
Contract tests for the ``TaskChunk`` JSON‑Schema.

The test suite validates that a correct record passes validation and
that an intentionally malformed record raises a ``jsonschema.exceptions.ValidationError``.
"""

import jsonschema
import pytest

from orchestrator.task_chunk_store import validate_task_chunk, TaskChunkStore

VALID_CHUNK = {
    "task_id": "chunk_001",
    "estimated_ops": 5000,
    "actual_duration": 1.23,
    "assigned_node_id": "192.168.1.101",
    "status": "completed"
}

INVALID_CHUNK_MISSING_FIELD = {
    # ``task_id`` omitted intentionally
    "estimated_ops": 5000,
    "actual_duration": 1.23,
    "assigned_node_id": "192.168.1.101",
    "status": "completed"
}

INVALID_CHUNK_EXTRA_FIELD = {
    "task_id": "chunk_001",
    "estimated_ops": 5000,
    "actual_duration": 1.23,
    "assigned_node_id": "192.168.1.101",
    "status": "completed",
    "unexpected": "value"
}

def test_valid_task_chunk_passes():
    """A well‑formed ``TaskChunk`` must validate without error."""
    assert validate_task_chunk(VALID_CHUNK) is True

def test_missing_required_field_raises():
    """Omitting a required field should raise a ValidationError."""
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validate_task_chunk(INVALID_CHUNK_MISSING_FIELD)

def test_additional_property_raises():
    """Additional properties are forbidden by the schema."""
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validate_task_chunk(INVALID_CHUNK_EXTRA_FIELD)

def test_store_writes_and_validates(tmp_path):
    """
    End‑to‑end test that the ``TaskChunkStore`` writes a valid line to disk.
    """
    # Patch the data directory to a temporary location
    from llmxive_toolkit import paths as toolkit_paths

    original_root = toolkit_paths.root
    try:
        # Redirect the project's root for this test
        toolkit_paths.root = tmp_path
        store = TaskChunkStore()
        store.write_chunk("run_001", VALID_CHUNK)

        jsonl_path = store._jsonl_path("run_001")
        assert jsonl_path.is_file()

        # Load the line back and ensure it matches the original dict
        with jsonl_path.open("r", encoding="utf-8") as f:
            line = f.readline().strip()
            loaded = json.loads(line)
        assert loaded == VALID_CHUNK
    finally:
        toolkit_paths.root = original_root
