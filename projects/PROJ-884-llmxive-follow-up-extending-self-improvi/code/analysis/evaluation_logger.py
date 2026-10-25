"""
Evaluation logger for Bidirectional Evolutionary Search (BES).

This module provides a simple API to record the outcome of each solution
attempt.  Each entry is written as a single JSON line to
``data/processed/evaluation_log.jsonl`` and validated against the JSON‑Schema
defined in ``contracts/evaluation_log.schema.yaml``.
"""

import json
import uuid
import datetime
from pathlib import Path
from jsonschema import validate, ValidationError

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Load the JSON‑Schema once at import time
_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "contracts" / "evaluation_log.schema.yaml"
try:
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as _f:
        _EVALUATION_SCHEMA = json.load(_f)
except FileNotFoundError as exc:
    log.error(f"Evaluation log schema not found at {_SCHEMA_PATH}: {exc}")
    raise

class EvaluationLogger:
    """
    Helper class that appends validated evaluation entries to the log file.
    """

    def __init__(self, output_path: Path = None):
        """
        Parameters
        ----------
        output_path: Path, optional
            Destination file for the JSON‑Lines log.  If omitted the default
            ``data/processed/evaluation_log.jsonl`` is used.
        """
        self.path = output_path or paths.data("processed", "evaluation_log.jsonl")
        # Ensure the parent directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Touch the file so it exists (empty file is fine)
        self.path.touch(exist_ok=True)

    def log(
        self,
        attempt_id: str,
        puzzle_id: str,
        method: str,
        is_valid: bool,
        error_code: str = None,
        timestamp: str = None,
    ) -> dict:
        """
        Append a single, schema‑validated entry to the log.

        Returns the dictionary that was written (useful for testing).

        Raises
        ------
        jsonschema.ValidationError
            If the constructed entry does not conform to the schema.
        """
        entry = {
            "attempt_id": attempt_id,
            "puzzle_id": puzzle_id,
            "method": method,
            "is_valid": is_valid,
            "error_code": error_code,
            "timestamp": timestamp
            or datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        }

        # Validate against the schema – any problem is a hard error
        try:
            validate(instance=entry, schema=_EVALUATION_SCHEMA)
        except ValidationError as exc:
            log.error(f"Evaluation log entry failed validation: {exc.message}")
            raise

        # Append as a single JSON line
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        log.debug(f"Wrote evaluation entry {attempt_id} for puzzle {puzzle_id}")
        return entry

# ----------------------------------------------------------------------
# Convenience functional API used by the rest of the code base
# ----------------------------------------------------------------------
def log_evaluation(
    attempt_id: str,
    puzzle_id: str,
    method: str,
    is_valid: bool,
    error_code: str = None,
    timestamp: str = None,
) -> dict:
    """
    Log a single evaluation entry.

    This function creates an :class:`EvaluationLogger` instance on‑demand
    (lightweight) and forwards the call.  It returns the entry dictionary
    for easy inspection in tests.
    """
    logger = EvaluationLogger()
    return logger.log(attempt_id, puzzle_id, method, is_valid, error_code, timestamp)

# ----------------------------------------------------------------------
# CLI entry point – useful for ad‑hoc manual checks
# ----------------------------------------------------------------------
def _parse_bool(value: str) -> bool:
    """Parse a truthy string from the command line."""
    return value.lower() in {"true", "1", "yes", "y"}

def main() -> None:
    """
    Simple command‑line wrapper.

    Example
    -------
    python -m code.analysis.evaluation_logger \\
        --puzzle-id puzzle_42 \\
        --method symbolic \\
        --is-valid true
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Append a single evaluation entry to the BES log."
    )
    parser.add_argument(
        "--attempt-id",
        default=str(uuid.uuid4()),
        help="Unique identifier for the attempt (default: generated UUID).",
    )
    parser.add_argument(
        "--puzzle-id", required=True, help="Identifier of the puzzle being evaluated."
    )
    parser.add_argument(
        "--method", required=True, help="Method name (e.g., 'symbolic' or 'neural')."
    )
    parser.add_argument(
        "--is-valid",
        required=True,
        type=_parse_bool,
        help="Whether the solution was valid (true/false).",
    )
    parser.add_argument(
        "--error-code",
        default=None,
        help="Error code returned by the verifier when invalid.",
    )
    parser.add_argument(
        "--timestamp",
        default=None,
        help="ISO‑8601 UTC timestamp; if omitted the current time is used.",
    )

    args = parser.parse_args()
    log_evaluation(
        attempt_id=args.attempt_id,
        puzzle_id=args.puzzle_id,
        method=args.method,
        is_valid=args.is_valid,
        error_code=args.error_code,
        timestamp=args.timestamp,
    )
    log.info("Evaluation entry written successfully.")

if __name__ == "__main__":
    main()
