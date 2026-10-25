"""
Interaction Logger Module
=========================

Provides millisecond‑precision logging of user interactions during figure editing.
Each call writes a single JSON line to ``data/logs/interactions.jsonl``.
The log schema (defined in ``contracts/interaction_log.schema.yaml``) includes:

- ``log_id``: unique identifier for the log entry
- ``session_id``: identifier of the participant session
- ``task_id``: identifier of the figure task
- ``timestamp_ms``: integer epoch time in milliseconds when the edit submitted
- ``iteration``: integer count of the edit attempt (starting at 1)
- ``mode``: interface mode used for this edit (``structured`` or ``chat``)
- ``payload``: **string** representation of the raw edit command (typed code) or natural‑language utterance
- ``response_image_path``: filesystem path to the image generated after the edit
- ``task_start_ms``: timestamp marking the start of the task
- ``task_end_ms``: timestamp marking the end of the task
- optional ``status``: ``aborted`` when the task exceeds the 15‑minute timeout
- optional ``subjective_load``: NASA‑TLX score (0–100) reported after task completion
- ``participant_id``: alias for ``session_id`` required by downstream analysis
- ``figure_id``: alias for ``task_id`` required by downstream analysis
- ``interface``: alias for ``mode`` required by downstream analysis

The logger records both the original schema fields and the analysis‑friendly aliases,
ensuring compatibility with contract validation **and** the statistical analysis pipeline.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

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

# Abort threshold: 15 minutes in milliseconds
_ABORT_THRESHOLD_MS = 15 * 60 * 1000

# In‑memory state to track per‑task start/end timestamps.
# Keyed by (session_id, task_id)
_task_state: Dict[Tuple[str, str], Dict[str, int]] = {}

def _timestamp_ms() -> int:
    """Return the current time as an integer number of milliseconds since the
    Unix epoch."""
    return int(time.time() * 1000)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def clear_logs() -> None:
    """
    Clear the interaction log file to ensure a fresh start.
    This is used during verification to ensure no synthetic pollution.
    """
    with _lock, LOG_PATH.open("w", encoding="utf-8") as f:
        f.truncate(0)

def log_interaction(
    participant_id: str,
    figure_id: str,
    interface: str,
    payload: Dict[str, Any],
    iteration: int,
    subjective_load: Optional[float] = None,
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
    subjective_load: float, optional
        NASA‑TLX score (0–100) reported after the task is completed.
        If ``None`` the field is omitted.

    The function records per‑task start/end timestamps, generates a unique
    ``log_id``, and writes the record as a JSON line.  If the elapsed time
    for the task exceeds 15 minutes, a ``status: "aborted"`` field is added.
    The ``payload`` field is stored as a JSON‑encoded **string** to satisfy
    the contract schema.  In addition to the schema‑required fields, the
    record also contains analysis‑friendly aliases ``participant_id``,
    ``figure_id`` and ``interface``.
    """
    now_ms = _timestamp_ms()

    # Update per‑task timing state
    key = (participant_id, figure_id)
    if key not in _task_state:
        # First interaction for this task
        _task_state[key] = {"task_start_ms": now_ms, "task_end_ms": now_ms}
    else:
        _task_state[key]["task_end_ms"] = now_ms

    task_start = _task_state[key]["task_start_ms"]
    task_end = _task_state[key]["task_end_ms"]
    elapsed = task_end - task_start

    # Build the log record with both schema fields and analysis aliases
    record: Dict[str, Any] = {
        # Schema‑required fields
        "log_id": str(uuid.uuid4()),
        "session_id": participant_id,
        "task_id": figure_id,
        "timestamp_ms": now_ms,
        "iteration": iteration,
        "mode": interface,
        "payload": json.dumps(payload, separators=(",", ":")),
        "response_image_path": f"data/figures/{figure_id}_edit_{iteration}.png",
        "task_start_ms": task_start,
        "task_end_ms": task_end,
        # Analysis‑friendly aliases
        "participant_id": participant_id,
        "figure_id": figure_id,
        "interface": interface,
    }

    # Optional fields
    if elapsed > _ABORT_THRESHOLD_MS:
        record["status"] = "aborted"
    if subjective_load is not None:
        # Clamp to the allowed range per schema
        record["subjective_load"] = max(0, min(100, subjective_load))

    # Ensure the parent directory exists (paths.data already created it,
    # but this is a defensive guard for direct imports outside the quick‑start).
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(record, separators=(",", ":"))  # compact representation

    _log.debug("Appending interaction record: %s", line)

    # Write atomically under a lock to avoid interleaved writes.
    with _lock, LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
