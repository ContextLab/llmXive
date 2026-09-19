"""
Trace Logger for Scheduler Metrics.

Implements Constitution Principle VI: Logging for metrics_triggered.
Records specific state variable names and their transition values
that triggered the scheduler selection to data/processed/scheduler_trace.json.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import logging utilities from the established API surface
from utils.logging import get_logger, log_with_context, log_error

logger = get_logger(__name__)

TRACE_FILE_PATH = "data/processed/scheduler_trace.json"

def ensure_trace_file_exists() -> Path:
    """
    Ensures the trace file and its parent directory exist.
    Initializes the file with an empty list if it does not exist.
    """
    trace_path = Path(TRACE_FILE_PATH)
    trace_path.parent.mkdir(parents=True, exist_ok=True)

    if not trace_path.exists():
        logger.info(f"Initializing new trace file at {trace_path}")
        with open(trace_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
    return trace_path

def load_trace_entries() -> List[Dict[str, Any]]:
    """
    Loads existing trace entries from the JSON file.
    Returns an empty list if the file is empty or doesn't exist.
    """
    trace_path = ensure_trace_file_exists()
    try:
        with open(trace_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except json.JSONDecodeError as e:
        log_error(logger, "Failed to decode existing trace file", e)
        return []

def append_trace_entry(entry: Dict[str, Any]) -> bool:
    """
    Appends a new entry to the trace file.
    The entry MUST include 'metrics_triggered' details as per Constitution Principle VI.
    """
    trace_path = ensure_trace_file_exists()
    entries = load_trace_entries()
    entries.append(entry)
    try:
        with open(trace_path, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2)
        logger.debug(f"Appended trace entry to {trace_path}")
        return True
    except Exception as e:
        log_error(logger, f"Failed to write trace entry to {trace_path}", e)
        return False

def log_metrics_triggered(
    state_variable: str,
    transition_value: Any,
    metric_name: str,
    metric_value: float,
    selection_reason: str,
    batch_id: Optional[str] = None,
    phase: Optional[str] = None
) -> Dict[str, Any]:
    """
    Logs a specific metric trigger event to the scheduler trace.

    This function fulfills T018:
    - Logs to data/processed/scheduler_trace.json
    - Includes specific state variable names (e.g., 'dark_mode')
    - Includes their transition values that triggered selection.

    Args:
        state_variable: The name of the state variable (e.g., 'dark_mode', 'unread_count').
        transition_value: The value of the state variable that triggered the event.
        metric_name: The name of the metric being evaluated.
        metric_value: The numerical value of the metric.
        selection_reason: Human-readable explanation of why this triggered selection.
        batch_id: Optional identifier for the current batch.
        phase: Optional current phase of the curriculum (e.g., 'low_coverage', 'sweet_spot').

    Returns:
        The constructed log entry dictionary.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    entry = {
        "timestamp": timestamp,
        "event_type": "metrics_triggered",
        "phase": phase,
        "batch_id": batch_id,
        "trigger": {
            "state_variable": state_variable,
            "transition_value": transition_value,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "reason": selection_reason
        },
        "metadata": {
            "constitution_principle": "VI",
            "description": "Logged specific state variable transition triggering scheduler selection"
        }
    }

    success = append_trace_entry(entry)
    if success:
        log_with_context(
            logger,
            f"Logged metrics_triggered for state '{state_variable}' (val: {transition_value})",
            extra={"state_var": state_variable, "metric": metric_name}
        )
    return entry

def main():
    """
    Demo/Validation entry point for T018.
    Simulates a scenario where a state variable triggers a scheduler selection
    and writes it to the trace file.
    """
    logger.info("Running T018: Trace Logger Validation")

    # Simulate a trigger event
    # In a real run, this would be called by curriculum_scheduler.py
    # when a specific state variable (e.g., dark_mode) changes and meets criteria.
    sample_entry = log_metrics_triggered(
        state_variable="dark_mode",
        transition_value=True,
        metric_name="coverage_ratio",
        metric_value=0.04,
        selection_reason="Coverage below 5% threshold, triggering Phase 1 exploration.",
        batch_id="batch_001",
        phase="low_coverage"
    )

    print(f"Successfully logged entry: {sample_entry['event_type']}")
    print(f"State Variable: {sample_entry['trigger']['state_variable']}")
    print(f"Transition Value: {sample_entry['trigger']['transition_value']}")
    print(f"Trace File: {TRACE_FILE_PATH}")

    # Verify file content
    entries = load_trace_entries()
    logger.info(f"Total entries in trace file: {len(entries)}")

if __name__ == "__main__":
    main()