"""
Constitutional Gate Check Module for llmXive PROJ-297.

This module enforces the Constitutional Amendment regarding the
Benjamini-Yekutieli (BY) procedure. It verifies the ratification status
before any statistical analysis involving FDR correction proceeds.
"""

import sys
import os
from pathlib import Path

# Path to the ratification status file relative to project root
# The project root is expected to be the parent of 'code'
_RATIFICATION_FILE_NAME = "amendment_ratification.json"
_RATIFICATION_STATUS_KEY = "is_ratified"
_REQUIRED_AMENDMENT_ID = "BY_PROCEDURE_2024"


def _get_ratification_file_path() -> Path:
    """
    Locates the amendment ratification file.
    Looks in the project root (parent of 'code' directory).
    """
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    return project_root / _RATIFICATION_FILE_NAME


def check_by_amendment_ratification() -> bool:
    """
    Verifies if the Constitutional Amendment for the Benjamini-Yekutieli
    procedure has been ratified.

    Returns:
        True if the amendment is ratified.

    Raises:
        SystemExit: If the amendment is NOT ratified or if the status file
                    is missing/corrupt. The system halts immediately with
                    a fatal error message as required by the Constitution.
    """
    ratification_path = _get_ratification_file_path()

    if not ratification_path.exists():
        error_msg = (
            f"Execution blocked: Constitutional Amendment for BY procedure not ratified. "
            f"Ratification status file '{ratification_path}' not found."
        )
        print(error_msg, file=sys.stderr)
        raise SystemExit(1)

    try:
        import json
        with open(ratification_path, 'r', encoding='utf-8') as f:
            status_data = json.load(f)

        if not isinstance(status_data, dict):
            raise ValueError("Ratification file format invalid.")

        is_ratified = status_data.get(_RATIFICATION_STATUS_KEY, False)
        amendment_id = status_data.get("amendment_id", "UNKNOWN")

        if amendment_id != _REQUIRED_AMENDMENT_ID:
            error_msg = (
                f"Execution blocked: Constitutional Amendment for BY procedure not ratified. "
                f"Found amendment ID '{amendment_id}', expected '{_REQUIRED_AMENDMENT_ID}'."
            )
            print(error_msg, file=sys.stderr)
            raise SystemExit(1)

        if not is_ratified:
            error_msg = (
                "Execution blocked: Constitutional Amendment for BY procedure not ratified."
            )
            print(error_msg, file=sys.stderr)
            raise SystemExit(1)

        return True

    except (json.JSONDecodeError, ValueError) as e:
        error_msg = (
            f"Execution blocked: Constitutional Amendment for BY procedure not ratified. "
            f"Error parsing ratification file: {e}"
        )
        print(error_msg, file=sys.stderr)
        raise SystemExit(1)


def enforce_gate():
    """
    Wrapper to enforce the gate check. This is intended to be called
    at the very beginning of the pipeline execution (e.g., in main.py).
    """
    check_by_amendment_ratification()
