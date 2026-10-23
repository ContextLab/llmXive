"""Parse τ‑bench task definitions into a canonical CSV.

This script reads the raw ``tasks.json`` file produced by
:pymod:`download_tau_c_bench`, extracts the fields required by the
``Task`` schema, and writes them to ``data/derived/task_definitions.csv``.
Rows where ``optimal_path_length`` is missing are left as empty (null)
values.  Any missing ``optimal_path_length`` is logged with the warning
code ``OPTIMAL_PATH_MISSING`` for downstream handling.
"""

import csv
import json
import logging
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration – list of columns that must appear in the output CSV.
# The Task schema (see ``specs/.../task.schema.yaml``) requires at least
# the following fields.  Additional fields present in the raw JSON are
# passed through unchanged so that downstream steps retain any extra
# information.
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = [
    "task_id",
    "goal",
    "environment",
    "optimal_path_length",
    "tool_diversity_k",
]

def _load_raw_tasks() -> list[dict]:
    """Load the raw JSON array from the expected location."""
    raw_path = paths.data("raw", "τc_bench", "tasks.json")
    if not raw_path.is_file():
        raise FileNotFoundError(f"Expected tasks.json at {raw_path}")
    with raw_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("tasks.json does not contain a JSON array.")
    return data

def _extract_row(task: dict) -> dict:
    """Extract a CSV row containing the required columns.

    Missing optional columns are set to ``None`` (which pandas/csv will
    render as an empty field).  Any extra keys are retained verbatim.
    """
    row = {}
    for col in REQUIRED_COLUMNS:
        # Use ``dict.get`` so missing keys become ``None``.
        row[col] = task.get(col, None)

    # Log missing optimal_path_length as a warning code.
    if row["optimal_path_length"] is None:
        task_id = row.get("task_id", "<unknown>")
        log.warning(
            f"Task {task_id} missing optimal_path_length – "
            f"logging warning code OPTIMAL_PATH_MISSING."
        )
    # Preserve any additional fields present in the raw record.
    for k, v in task.items():
        if k not in row:
            row[k] = v
    return row

def parse_and_write(csv_path: Path) -> None:
    """Parse raw tasks and write the canonical CSV."""
    raw_tasks = _load_raw_tasks()
    if not raw_tasks:
        raise RuntimeError("No tasks found in tasks.json.")

    # Build rows preserving order of REQUIRED_COLUMNS first.
    rows = [_extract_row(t) for t in raw_tasks]

    # Determine the full set of column names (required + any extra).
    all_columns = list(dict.fromkeys(
        [c for c in REQUIRED_COLUMNS] +
        [k for row in rows for k in row.keys() if k not in REQUIRED_COLUMNS]
    ))

    # Ensure the destination directory exists.
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_columns)
        writer.writeheader()
        writer.writerows(rows)

    log.info(f"Wrote {len(rows)} task definitions to {csv_path}")

def main() -> None:
    """CLI entry point."""
    output_path = paths.data("derived", "task_definitions.csv")
    parse_and_write(output_path)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(f"Failed to parse task definitions: {exc}")
        raise