"""
Script to create the project-wide `code/` directory in an idempotent manner
and verify that it is writable.

This script satisfies task T001a by:
  1. Creating the `code/` directory with `parents=True, exist_ok=True`.
  2. Asserting that the directory is writable using `os.access`.
  3. Exiting with a non‑zero status if any step fails (the runtime will
     capture the exception and mark the task as failed).

The script is safe to run multiple times; it will not raise an error on
subsequent executions because the directory creation is idempotent.
"""

import os
from pathlib import Path
import sys

def create_and_verify_code_dir() -> None:
    """Create the `code/` directory and verify write access."""
    # Resolve the project root relative to this script's location.
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    # Idempotent creation.
    try:
        code_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise RuntimeError(f"Failed to create directory {code_dir}: {exc}") from exc

    # Verify writability.
    if not os.access(str(code_dir), os.W_OK):
        raise PermissionError(f"Directory {code_dir} is not writable.")

if __name__ == "__main__":
    try:
        create_and_verify_code_dir()
    except Exception as e:
        # Print the error to stderr and exit with a non‑zero code so the
        # execution framework can detect failure.
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    else:
        # Successful execution; exit with zero status.
        sys.exit(0)