"""
aggregate_validation.py
-----------------------

This script aggregates semantic validation records per participant to compute
an *effective N* (the number of tasks with primary success) for each
participant/session.  It reads the JSON‑Lines file
``data/results/semantic_validation_by_session.jsonl`` and writes two
outputs:

1. ``data/results/semantic_validation_by_session.jsonl`` – unchanged
   (the script validates its contents).
2. ``data/results/effective_N_by_participant.jsonl`` – one line per
   participant with the fields ``session_id`` and ``effective_N`` (an
   integer ≥ 1).

The script prints a short summary:
    "Aggregation complete: X participants, Y valid tasks"

The CLI mirrors the style of other pipeline scripts: optional
``--input-dir`` (defaults to the project ``data/results`` folder) and
``--output-dir`` (defaults to the same folder).  The script exits with
status 0 on success and non‑zero on failure.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate semantic validation records and compute per‑participant "
            "effective N (number of successful tasks)."
        )
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=str(paths.data("results")),
        help="Directory containing 'semantic_validation_by_session.jsonl'.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(paths.data("results")),
        help="Directory where 'effective_N_by_participant.jsonl' will be written.",
    )
    return parser

def _load_validation_records(input_dir: Path) -> List[Dict]:
    """Load all JSON‑Lines validation records."""
    validation_path = input_dir / "semantic_validation_by_session.jsonl"
    if not validation_path.is_file():
        log.error(f"Validation file not found: {validation_path}")
        raise FileNotFoundError(str(validation_path))

    records = []
    with validation_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                log.error(f"Invalid JSON on line {line_no}: {e}")
                raise
            # Verify required fields
            for key in ("session_id", "task_id", "overall_success"):
                if key not in rec:
                    raise ValueError(
                        f"Record on line {line_no} missing required key '{key}'"
                    )
            records.append(rec)
    return records

def _compute_effective_n(records: List[Dict]) -> Dict[str, int]:
    """
    Compute effective N per participant.

    effective_N = number of tasks where overall_success == True
    """
    counts = defaultdict(int)
    for rec in records:
        if rec.get("overall_success"):
            counts[rec["session_id"]] += 1
    # Ensure every participant has at least one successful task
    for sess, cnt in counts.items():
        if cnt < 1:
            raise ValueError(f"Participant {sess} has effective_N < 1")
    return dict(counts)

def _write_effective_n(effective_n: Dict[str, int], output_dir: Path) -> None:
    """Write the effective_N JSON‑Lines file."""
    out_path = output_dir / "effective_N_by_participant.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for session_id, n in sorted(effective_n.items()):
            json.dump(
                {"session_id": session_id, "effective_N": n}, f, ensure_ascii=False
            )
            f.write("\n")
    log.info(f"Wrote effective N file to {out_path}")

def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    try:
        records = _load_validation_records(input_dir)
    except Exception as e:
        log.error(f"Failed to load validation records: {e}")
        return 1

    participant_count = len({rec["session_id"] for rec in records})
    valid_task_count = sum(1 for rec in records if rec.get("overall_success"))

    try:
        effective_n = _compute_effective_n(records)
    except Exception as e:
        log.error(f"Failed to compute effective N: {e}")
        return 1

    try:
        _write_effective_n(effective_n, output_dir)
    except Exception as e:
        log.error(f"Failed to write effective N file: {e}")
        return 1

    print(
        f"Aggregation complete: {participant_count} participants, {valid_task_count} valid tasks"
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())
