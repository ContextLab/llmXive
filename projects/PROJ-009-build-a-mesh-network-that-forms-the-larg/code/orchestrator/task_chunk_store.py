"""
Persistence helper for ``TaskChunk`` records.

This module has been refactored so that the storage location can be
monkey‑patched by the test suite.  The mutable ``base_dir`` attribute is
provided by ``runtime.paths.TaskChunkStore``.  All write operations now
reference that attribute, allowing isolated tests to redirect output
without touching the production directory.
"""

import json
import logging
from pathlib import Path
from typing import Dict

import yaml
import jsonschema

from llmxive_toolkit import get_logger
from runtime.paths import TaskChunkStore as RuntimeTaskChunkStore

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
    """
    jsonschema.validate(instance=chunk_record, schema=_TASK_CHUNK_SCHEMA)
    return True


# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------
class TaskChunkStore:
    """
    Simple writer for TaskChunk JSON‑Lines.

    The class uses the mutable ``RuntimeTaskChunkStore.base_dir`` as the
    destination directory.  Tests can monkey‑patch that attribute to a
    temporary location, ensuring no side‑effects on the real data store.
    """

    @classmethod
    def _chunk_path(cls, run_id: str) -> Path:
        """Return the Path for the given run's JSONL file."""
        filename = f"{run_id}.jsonl"
        return RuntimeTaskChunkStore.base_dir / filename

    @classmethod
    def write_chunk(cls, run_id: str, chunk_record: dict) -> None:
        """
        Append a single ``chunk_record`` to the JSONL file for ``run_id``.

        Parameters
        ----------
        run_id : str
            Identifier for the current run (e.g., ``run_001``).
        chunk_record : dict
            The ``TaskChunk`` dictionary to persist.  The caller should
            invoke :func:`validate_task_chunk` beforehand if strict
            checking is required.
        """
        # Ensure the record is JSON‑serialisable
        line = json.dumps(chunk_record, ensure_ascii=False)
        path = cls._chunk_path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        log.debug("TaskChunk written to %s: %s", path, line)

    @classmethod
    def append(cls, chunk_record: dict) -> None:
        """
        Convenience wrapper used by the scheduler.

        The ``chunk_record`` must contain a ``run_id`` field.  The method
        extracts that identifier and forwards the record to
        :meth:`write_chunk`.
        """
        if not isinstance(chunk_record, dict):
            raise TypeError("chunk_record must be a dict")
        if "run_id" not in chunk_record:
            raise ValueError("chunk_record must contain a 'run_id' key")
        run_id = chunk_record["run_id"]
        cls.write_chunk(run_id, chunk_record)