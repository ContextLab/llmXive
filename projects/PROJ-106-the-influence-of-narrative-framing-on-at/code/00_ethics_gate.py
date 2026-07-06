"""
Ethics Gate Module for llmXive Project PROJ-106.

This module implements Constitution VI: Ethics and IRB Compliance.
It checks for the existence of an IRB approval file in the data/ethics/ directory.
If the approval file is missing, it raises a RuntimeError to block execution.
"""

import os
import sys
from pathlib import Path

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ETHICS_DIR = PROJECT_ROOT / "data" / "ethics"
APPROVAL_FILE_NAME = "IRB_APPROVAL.txt"

def check_ethics_approval() -> bool:
    """
    Checks if the IRB approval file exists in the designated ethics directory.

    Returns:
        bool: True if the approval file exists and is readable.

    Raises:
        RuntimeError: If the IRB approval file is missing, blocking execution.
        FileNotFoundError: If the ethics directory itself is missing.
    """
    if not ETHICS_DIR.exists():
        raise FileNotFoundError(
            f"Ethics directory not found at {ETHICS_DIR}. "
            "Please ensure the directory structure is created per T001."
        )

    approval_path = ETHICS_DIR / APPROVAL_FILE_NAME

    if not approval_path.exists():
        raise RuntimeError(
            f"CRITICAL: IRB approval file '{APPROVAL_FILE_NAME}' is missing from "
            f"{ETHICS_DIR}. "
            "Execution blocked per Constitution VI. "
            "Please upload the signed IRB approval document to this location before proceeding."
        )

    # Optional: Check if file is empty (sanity check)
    if approval_path.stat().st_size == 0:
        raise RuntimeError(
            f"CRITICAL: IRB approval file at {approval_path} is empty. "
            "Execution blocked per Constitution VI."
        )

    return True


def main():
    """
    Entry point for running the ethics gate check as a script.
    Used to verify compliance before running the main pipeline.
    """
    print("Checking IRB Approval status...")
    try:
        if check_ethics_approval():
            print("SUCCESS: IRB approval verified. Proceeding with execution.")
            sys.exit(0)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during ethics check: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
