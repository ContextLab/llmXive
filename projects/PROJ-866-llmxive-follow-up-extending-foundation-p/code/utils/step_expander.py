"""
code.utils.step_expander
------------------------

Expand execution logs (full‑context and compressed‑context) to a flat
step‑level outcome dataset.

Each entry in the output JSON corresponds to a single *step* (here we treat
each execution log as one step).  The fields are:

  - workflow_id: identifier of the workflow
  - step_index: integer index of the step within the workflow (always 0
    for this simplified implementation)
  - outcome: 0 if the workflow had no policy violations, 1 otherwise
  - context_reduction_pct: numeric percentage or the string "[deferred]"
  - policy_complexity: the ``complexity`` field from the original log
  - delegation_depth: the ``depth`` field from the original log
  - exclude_from_regression: true when ``context_reduction_pct`` is the
    string "[deferred]" (these rows must be ignored by the GEE analysis)

The script reads the two canonical log files produced by the pipeline:

  * data/processed/full_context_logs.json
  * data/processed/compressed_context_logs.json

and writes the aggregated step‑level records to:

  * data/processed/step_outcomes.json

The implementation is deliberately lightweight and uses only the standard
library plus the project's ``llmxive_toolkit`` helpers for path management
and logging.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _load_logs(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON array of execution‑log dictionaries.

    Parameters
    ----------
    file_path: Path
        Path to the JSON file.

    Returns
    -------
    List[Dict[str, Any]]
        List of log entries; an empty list is returned if the file does not
        exist or cannot be parsed.
    """
    if not file_path.is_file():
        log.error("Log file not found: %s", file_path)
        return []

    try:
        with file_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            log.error("Expected a list of logs in %s, got %s", file_path, type(data))
            return []
        return data
    except (OSError, json.JSONDecodeError) as exc:
        log.error("Failed to read %s: %s", file_path, exc)
        return []

def _log_to_step(log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a single execution‑log entry to a step‑level outcome record.

    The outcome is binary: 1 if any policy violations were reported,
    otherwise 0.

    Parameters
    ----------
    log_entry: Dict[str, Any]
        One execution‑log dictionary.

    Returns
    -------
    Dict[str, Any]
        Step‑level record with the required fields.
    """
    # Determine binary outcome
    violations = log_entry.get("policy_violations", [])
    outcome = 1 if violations else 0

    # Extract fields; use defaults if missing
    context_reduction = log_entry.get("context_reduction_pct", 0)
    policy_complexity = log_entry.get("complexity", log_entry.get("policy_complexity", 0))
    delegation_depth = log_entry.get("depth", log_entry.get("delegation_depth", 0))

    # Flag rows that should be excluded from regression
    exclude = isinstance(context_reduction, str) and context_reduction == "[deferred]"

    # Basic sanity check for numeric percentages
    if not exclude and isinstance(context_reduction, (int, float)):
        if context_reduction < 0 or context_reduction > 100:
            log.warning(
                "Context reduction pct out of expected range [0,100]: %s (workflow %s)",
                context_reduction,
                log_entry.get("workflow_id", "unknown"),
            )

    step_record = {
        "workflow_id": log_entry.get("workflow_id", "unknown"),
        "step_index": 0,  # single‑step representation
        "outcome": outcome,
        "context_reduction_pct": context_reduction,
        "policy_complexity": policy_complexity,
        "delegation_depth": delegation_depth,
        "exclude_from_regression": exclude,
    }
    return step_record

def expand_logs(
    full_log_path: Path,
    compressed_log_path: Path,
    output_path: Path,
) -> None:
    """Read both log files, expand them to step‑level outcomes, and write JSON.

    Parameters
    ----------
    full_log_path: Path
        Path to ``full_context_logs.json``.
    compressed_log_path: Path
        Path to ``compressed_context_logs.json``.
    output_path: Path
        Destination for the step‑outcome JSON array.
    """
    log.info("Loading full‑context logs from %s", full_log_path)
    full_logs = _load_logs(full_log_path)

    log.info("Loading compressed‑context logs from %s", compressed_log_path)
    compressed_logs = _load_logs(compressed_log_path)

    all_logs = full_logs + compressed_logs
    if not all_logs:
        log.error("No logs available to process; aborting step expansion.")
        return

    step_records: List[Dict[str, Any]] = []
    for entry in all_logs:
        step_records.append(_log_to_step(entry))

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as out_fh:
        json.dump(step_records, out_fh, indent=2)

    log.info(
        "Wrote %d step‑level outcome records to %s",
        len(step_records),
        output_path,
    )

def main(argv: List[str] | None = None) -> int:
    """CLI entry point used by the pipeline.

    The script does not accept any command‑line arguments; it always reads
    the canonical locations under ``data/processed/`` and writes the result
    to the same directory.
    """
    full_path = paths.data("processed", "full_context_logs.json")
    compressed_path = paths.data("processed", "compressed_context_logs.json")
    output_path = paths.data("processed", "step_outcomes.json")

    expand_logs(full_path, compressed_path, output_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
