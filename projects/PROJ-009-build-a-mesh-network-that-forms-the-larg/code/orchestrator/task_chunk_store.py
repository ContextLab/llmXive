"""
Persistence helper for ``TaskChunk`` records.

The store writes each ``TaskChunk`` as a JSON line into a file under
``data/raw/task_chunks/<run_id>.jsonl``.  It also provides a simple
validation function that checks a record against the JSON‑Schema
defined in ``specs/001-build-a-mesh-network-that-forms-the-larg/contracts/task-chunk.schema.yaml``.
"""

import json
from pathlib import Path
from typing import Dict

import yaml
import jsonschema
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------
def _load_schema() -> Dict:
    """
    Load the TaskChunk JSON‑Schema from the project specifications.

    Returns
    -------
    dict
        The JSON‑Schema dictionary.
    """
    # The schema lives two levels up from this file under the specs folder.
    schema_path = (
        Path(__file__).resolve()
        .parents[2]  # project root
        / "specs"
        / "001-build-a-mesh-network-that-forms-the-larg"
        / "contracts"
        / "task-chunk.schema.yaml"
    )
    if not schema_path.is_file():
        raise FileNotFoundError(f"TaskChunk schema not found at {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

_TASK_CHUNK_SCHEMA = _load_schema()


def validate_task_chunk(chunk_record: dict) -> bool:
    """
    Validate a ``TaskChunk`` dictionary against the official schema.

    Parameters
    ----------
    chunk_record : dict
        The record to validate.

    Returns
    -------
    bool
        ``True`` if the record conforms to the schema.  If validation
        fails a ``jsonschema.exceptions.ValidationError`` is raised.

    Raises
    ------
    jsonschema.exceptions.ValidationError
        If the record does not satisfy the schema.
    """
    jsonschema.validate(instance=chunk_record, schema=_TASK_CHUNK_SCHEMA)
    return True


# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------
class TaskChunkStore:
    """Simple writer for TaskChunk JSON‑Lines."""

    def __init__(self) -> None:
        # Base directory for task‑chunk persistence
        self.base_dir = paths.data("raw", "task_chunks")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _chunk_path(self, run_id: str) -> Path:
        """Return the Path for the given run's JSONL file."""
        filename = f"{run_id}.jsonl"
        return self.base_dir / filename

    # Compatibility alias used by the test suite
    def _jsonl_path(self, run_id: str) -> Path:
        """Alias for ``_chunk_path`` to keep backward compatibility with tests."""
        return self._chunk_path(run_id)

    def write_chunk(self, run_id: str, chunk_record: dict) -> None:
        """
        Append a single ``chunk_record`` to the JSONL file for ``run_id``.
        The record is written as a single line of JSON.

        Parameters
        ----------
        run_id : str
            Identifier for the current run (e.g., ``run_001``).
        chunk_record : dict
            The ``TaskChunk`` dictionary to persist.  It is **not**
            validated here; callers should invoke :func:`validate_task_chunk`
            beforehand if strict checking is required.
        """
        # Ensure the record is JSON‑serialisable
        line = json.dumps(chunk_record, ensure_ascii=False)
        path = self._chunk_path(run_id)
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        log.debug("TaskChunk written to %s: %s", path, line)
