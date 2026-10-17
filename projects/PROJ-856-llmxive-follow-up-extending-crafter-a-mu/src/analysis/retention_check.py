"""
Retention check script.

This script verifies that a minimum number of participant sessions contain at
least one successful trial, where a trial is considered successful only if
both ``vector_match`` and ``semantic_pass`` are true in the semantic validation
records.

The script is invoked from the quick‑start as::

    python -m src.utils.check_retention --log-dir data/logs/ --min-valid 25

It determines the location of the validation file based on the provided
``log_dir`` (assumes a sibling ``validation`` directory containing a file named
``semantic_validation.jsonl``).  The validation records are expected to be JSON
lines with at least the following keys:

- ``session_id`` (or ``participant_id``): identifier of the participant/session.
- ``vector_match`` (bool): result of the exact vector comparison.
- ``semantic_pass`` (bool): result of the semantic similarity check.

If the number of distinct sessions that have at least one successful record is
lower than ``min_valid``, the script prints a warning and exits with a non‑zero
status code, causing the pipeline to halt.

The implementation is deliberately lightweight and has no external
dependencies beyond the Python standard library.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Set

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check that enough sessions contain at least one successful trial."
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        required=True,
        help="Path to the directory containing per‑session interaction logs (e.g., data/logs/).",
    )
    parser.add_argument(
        "--min-valid",
        type=int,
        default=25,
        help="Minimum number of sessions that must have at least one successful trial.",
    )
    return parser.parse_args()

def _determine_validation_path(log_dir: Path) -> Path:
    """
    The quick‑start expects the validation file to be located at:
    ``<project>/data/validation/semantic_validation.jsonl``.
    Given ``log_dir`` (e.g., ``data/logs/``), we climb one level to ``data/``
    and then descend into ``validation/semantic_validation.jsonl``.
    """
    return log_dir.parent / "validation" / "semantic_validation.jsonl"

def _load_successful_sessions(validation_path: Path) -> Set[str]:
    """
    Load the semantic validation file and return the set of session identifiers
    that have at least one successful record (both checks pass).
    """
    successful_sessions: Set[str] = set()
    with validation_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON line in {validation_path}: {e}") from e

            # Expected keys: ``vector_match`` and ``semantic_pass`` (both bool).
            # Session identifier may appear under ``session_id`` or ``participant_id``.
            vector_match = record.get("vector_match")
            semantic_pass = record.get("semantic_pass")
            if vector_match is True and semantic_pass is True:
                session_id = (
                    record.get("session_id")
                    or record.get("participant_id")
                    or record.get("session")  # fallback key
                )
                if session_id is None:
                    raise KeyError(
                        f"Successful validation record missing session identifier: {record}"
                    )
                successful_sessions.add(str(session_id))
    return successful_sessions

def main() -> int:
    """
    Entry point for ``python -m src.analysis.retention_check``.
    Returns ``0`` on success, ``1`` otherwise.
    """
    args = _parse_args()
    validation_path = _determine_validation_path(args.log_dir)

    if not validation_path.is_file():
        print(f"Validation file not found: {validation_path}", file=sys.stderr)
        return 1

    try:
        successful_sessions = _load_successful_sessions(validation_path)
    except (ValueError, KeyError) as e:
        print(f"Error processing validation file: {e}", file=sys.stderr)
        return 1

    count = len(successful_sessions)
    if count >= args.min_valid:
        print(f"Retention threshold met: {count} sessions with at least one successful trial.")
        return 0
    else:
        print(
            f"Retention threshold not met: only {count} sessions have a successful trial "
            f"(required >= {args.min_valid}).",
            file=sys.stderr,
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())
