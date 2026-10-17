"""
Interaction Logger Module
=========================

Provides millisecond‑precision logging of user interactions during figure editing.
Each call writes a single JSON line to ``data/logs/interactions.jsonl``.
The log schema (defined in ``contracts/interaction_log.schema.yaml``) includes:

- ``timestamp_ms``: integer epoch time in milliseconds
- ``participant_id``: string identifier for the participant
- ``figure_id``: string identifier for the figure being edited
- ``interface``: either ``structured`` or ``chat``
- ``iteration``: integer count of the edit attempt (starting at 1)
- ``payload``: the raw request payload (dict) sent to the edit endpoint
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict

from llmxive_toolkit import get_logger, paths

# ----------------------------------------------------------------------
# Constants & helpers
# ----------------------------------------------------------------------
LOG_PATH: Path = paths.data("logs", "interactions.jsonl")
"""Path to the JSON‑Lines interaction log file. ``paths.data`` ensures the
``data/logs`` directory exists."""

_lock = threading.Lock()
"""A simple lock to avoid interleaved writes when the logger is used from
multiple threads (e.g., a FastAPI server handling concurrent requests)."""

_log = get_logger(__name__)

def _timestamp_ms() -> int:
    """Return the current time as an integer number of milliseconds since the
    Unix epoch."""
    return int(time.time() * 1000)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def log_interaction(
    participant_id: str,
    figure_id: str,
    interface: str,
    payload: Dict[str, Any],
    iteration: int,
) -> None:
    """
    Append a single interaction record to the interaction log.

    Parameters
    ----------
    participant_id: str
        Identifier for the participant (e.g., a UUID or anonymised hash).
    figure_id: str
        Identifier of the figure/task being edited.
    interface: str
        Which interface was used – ``structured`` or ``chat``.
    payload: dict
        The raw request payload sent to the edit endpoint.
    iteration: int
        The 1‑based edit attempt number for this figure.

    The function is deliberately lightweight: it builds a dictionary,
    serialises it as a JSON line, and appends it to ``LOG_PATH`` under a
    thread‑safe lock.  No return value is needed; failures propagate as
    exceptions so that calling code can react appropriately.
    """
    record = {
        "timestamp_ms": _timestamp_ms(),
        "participant_id": participant_id,
        "figure_id": figure_id,
        "interface": interface,
        "iteration": iteration,
        "payload": payload,
    }

    # Ensure the parent directory exists (paths.data already created it,
    # but this is a defensive guard for direct imports outside the quick‑start).
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(record, separators=(",", ":"))  # compact representation

    _log.debug("Appending interaction record: %s", line)

    # Write atomically under a lock to avoid interleaved writes.
    with _lock, LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
