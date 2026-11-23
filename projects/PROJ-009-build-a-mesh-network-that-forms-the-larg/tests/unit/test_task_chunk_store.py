"""
Unit test for the refactored ``TaskChunkStore`` and its integration with the
scheduler.

The test monkey‑patches ``runtime.paths.TaskChunkStore.base_dir`` to a
temporary directory, creates a dummy chunk (including the required
``run_id`` field), runs a minimal scheduler that stores the chunk, and
finally asserts:

1. The JSONL file exists at the expected location.
2. The file contains exactly one line.
3. The line validates against the official ``task-chunk.schema.yaml``.
"""

import json
from pathlib import Path
import tempfile

import pytest
import yaml
import jsonschema

# Import the objects under test
from runtime.paths import TaskChunkStore as RuntimeTaskChunkStore
from orchestrator.task_chunk_store import TaskChunkStore, validate_task_chunk
from orchestrator.scheduler import Scheduler


@pytest.fixture
def temp_dir():
    """Create a temporary directory that will be automatically cleaned up."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


def load_schema():
    """Load the TaskChunk JSON‑Schema used for validation."""
    schema_path = (
        Path(__file__).resolve()
        .parents[4]  # project root
        / "specs"
        / "001-build-a-mesh-network-that-forms-the-larg"
        / "contracts"
        / "task-chunk.schema.yaml"
    )
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_task_chunk_store_integration(temp_dir):
    """
    End‑to‑end test:

    * Monkey‑patch the mutable base_dir.
    * Create a dummy chunk record.
    * Run the scheduler which should invoke ``TaskChunkStore.append``.
    * Verify the output file and its contents.
    """
    # ------------------------------------------------------------------
    # Redirect storage to the temporary directory
    # ------------------------------------------------------------------
    RuntimeTaskChunkStore.base_dir = temp_dir

    # ------------------------------------------------------------------
    # Prepare a minimal, schema‑valid chunk.
    # ------------------------------------------------------------------
    dummy_chunk = {
        "run_id": "run_001",
        "chunk_id": "c1",
        "task_type": "monte_carlo",
        "payload": {"iterations": 1000, "seed": 42},
        "status": "completed"
    }

    # Validate the chunk before we store it – this mirrors production
    # behaviour and ensures the test fails early if the schema changes.
    assert validate_task_chunk(dummy_chunk) is True

    # ------------------------------------------------------------------
    # Run the scheduler (the only integration point required for T005)
    # ------------------------------------------------------------------
    scheduler = Scheduler()
    processed = scheduler.process_chunks([dummy_chunk])

    # The scheduler should return the same chunk we gave it.
    assert processed == [dummy_chunk]

    # ------------------------------------------------------------------
    # Verify that the JSONL file was created in the patched location.
    # ------------------------------------------------------------------
    jsonl_path = temp_dir / "run_001.jsonl"
    assert jsonl_path.is_file(), f"Expected JSONL file at {jsonl_path}"

    # Read the file – it should contain exactly one line.
    with jsonl_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 1, "JSONL file should contain a single record"

    # Parse the line and validate against the schema.
    stored_record = json.loads(lines[0])
    schema = load_schema()
    jsonschema.validate(instance=stored_record, schema=schema)

    # Ensure the stored record matches the original chunk (order of keys may differ).
    for key, value in dummy_chunk.items():
        assert stored_record[key] == value