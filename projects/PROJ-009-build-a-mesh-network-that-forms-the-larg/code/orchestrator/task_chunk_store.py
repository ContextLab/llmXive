"""
Persistence helper for ``TaskChunk`` records.

The store writes each ``TaskChunk`` as a JSON line into a file under
``data/raw/task_chunks/<run_id>.jsonl``.  The implementation is deliberately
lightweight – it does not perform schema validation (that is handled by
separate contract tests) but ensures that the directory structure exists
and that each record is written atomically.
"""

import json
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

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

    def write_chunk(self, run_id: str, chunk_record: dict) -> None:
        """
        Append a single ``chunk_record`` to the JSONL file for ``run_id``.
        The record is written as a single line of JSON.
        """
        path = self._chunk_path(run_id)
        line = json.dumps(chunk_record, ensure_ascii=False)
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        log.debug("TaskChunk written to %s: %s", path, line)