"""
retention_check.py
------------------

This script verifies participant retention based on primary‑success
validation records.  It ensures that at least ``min_valid`` participants
out of a total of ``required_participants`` have recorded at least one
successful trial (primary success, i.e. exact vector match).

The validation records are expected to be stored in a JSON‑Lines file
``data/validation/semantic_validation.jsonl``.  Each line must contain
at minimum a participant identifier (``participant_id`` or ``session_id``)
and a boolean ``overall_success`` field indicating primary success.

The script is invoked via the module entry point:

    python -m src.analysis.retention_check \
        --log-dir <log_dir> \
        --min-valid <int> \
        --required-participants <int>

It prints a concise status line and exits with status 0 on success,
otherwise prints an error line and exits with status 1.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Set

def _parse_args() -> argparse.Namespace:
    """Parse command‑line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Check that a sufficient number of participants have at least "
            "one primary‑success trial."
        )
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        required=True,
        help="Directory containing the interaction logs (used to locate the validation file).",
    )
    parser.add_argument(
        "--min-valid",
        type=int,
        required=True,
        help="Minimum number of participants that must have a successful trial.",
    )
    parser.add_argument(
        "--required-participants",
        type=int,
        required=True,
        help="Total number of participants expected in the study.",
    )
    return parser.parse_args()

def _determine_validation_path(log_dir: Path) -> Path:
    """
    Resolve the path to the semantic validation JSON‑Lines file.

    The quick‑start documentation expects the file to live at:
        <project>/data/validation/semantic_validation.jsonl
    Given ``log_dir`` (e.g. ``data/logs/``), we climb one level to ``data/``
    and then descend into ``validation/semantic_validation.jsonl``.
    """
    # ``log_dir`` may be absolute or relative; ensure it is a Path object.
    log_dir = Path(log_dir)
    # Move up one directory (from logs/ to data/) and then to validation/.
    validation_path = log_dir.parent / "validation" / "semantic_validation.jsonl"
    return validation_path

def _load_successful_sessions(validation_path: Path) -> Set[str]:
    """
    Load the semantic validation file and return the set of participant
    identifiers that have at least one primary‑success record.

    The validation records are JSON objects with (at least) the fields:
        - ``overall_success`` (bool): primary success flag.
        - ``participant_id`` *or* ``session_id`` (str): identifier.

    Any record with ``overall_success`` truthy contributes the identifier
    to the returned set.
    """
    successful: Set[str] = set()
    try:
        with validation_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    # If a line cannot be parsed, abort loudly – the
                    # validation file is malformed.
                    sys.stderr.write(f"Malformed JSON line in {validation_path}\\n")
                    sys.exit(1)

                # Determine the participant identifier.
                participant_id = record.get("participant_id") or record.get(
                    "session_id"
                )
                if participant_id is None:
                    # Missing identifier – this is a contract violation.
                    sys.stderr.write(
                        f"Record missing participant identifier in {validation_path}\\n"
                    )
                    sys.exit(1)

                # Record success if the primary success flag is true.
                if bool(record.get("overall_success")):
                    successful.add(str(participant_id))
    except FileNotFoundError:
        sys.stderr.write(f"Validation file not found: {validation_path}\\n")
        sys.exit(1)

    return successful

def main() -> int:
    """Entry point for ``python -m src.analysis.retention_check``."""
    args = _parse_args()

    # Resolve the validation file location.
    validation_path = _determine_validation_path(args.log_dir)

    # Load the set of participants with at least one primary‑success trial.
    successful_sessions = _load_successful_sessions(validation_path)

    # Determine the total number of distinct participants present in the
    # validation file (whether they succeeded or not).  This is the
    # denominator for the retention ratio.
    try:
        with validation_path.open("r", encoding="utf-8") as f:
            all_participants: Set[str] = set()
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                pid = record.get("participant_id") or record.get("session_id")
                if pid is not None:
                    all_participants.add(str(pid))
    except FileNotFoundError:
        # Already handled earlier; this block is defensive.
        sys.stderr.write(f"Validation file not found: {validation_path}\\n")
        return 1

    total_participants = len(all_participants)

    # Verify the total matches the required participant count.
    if total_participants < args.required_participants:
        sys.stderr.write(
            f"Retention check failed: only {total_participants} participants "
            f"found, but {args.required_participants} required.\\n"
        )
        return 1

    # Count participants that satisfy the primary‑success criterion.
    valid_count = len(successful_sessions)

    if valid_count >= args.min_valid:
        print(
            f"Retention check passed: {valid_count}/{total_participants} participants meet criteria"
        )
        return 0
    else:
        sys.stderr.write(
            f"Retention check failed: {valid_count}/{total_participants} participants meet criteria (minimum required: {args.min_valid})\\n"
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())
