"""
Pipeline logging utilities.

Provides a simple JSON‑lines logger that writes events to
``logs/pipeline.jsonl``.  Each event is a dictionary that will be
serialized as a single line of JSON.  The logger is deliberately
lightweight – it does not perform schema validation (that is handled
elsewhere) but guarantees that the output file exists and that each
line is valid JSON.

Usage
-----
>>> from src.pipeline.logging_utils import log_event
>>> log_event({"event": "pipeline_start", "timestamp": "2024-01-01T00:00:00Z"})
"""
import json
from pathlib import Path
from llmxive_toolkit import paths

# Resolve the log file location once at import time.
_PIPELINE_LOG_PATH: Path = paths.logs("pipeline.jsonl")
_PIPELINE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def log_event(event: dict) -> None:
    """
    Append a JSON‑encoded event to the pipeline log.

    Parameters
    ----------
    event: dict
        Arbitrary mapping that will be JSON‑serialised.  The function
        does **not** enforce any particular schema – callers are
        responsible for providing a conformant payload.

    The function creates ``logs/pipeline.jsonl`` if it does not exist
    and writes a single line terminated by a newline character.
    """
    if not isinstance(event, dict):
        raise TypeError("log_event expects a dictionary payload")
    # Ensure the file exists; ``open`` with ``a`` creates it if missing.
    with _PIPELINE_LOG_PATH.open("a", encoding="utf-8") as fp:
        json.dump(event, fp, ensure_ascii=False)
        fp.write("\n")
