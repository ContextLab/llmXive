"""
Task T003b: Verify pyproject.toml exists and contains valid configuration sections for black and ruff.

This script checks the existence of `pyproject.toml` in the project root and validates
that it contains the required configuration sections for Black (line-length=88) and
Ruff (lint.select = ["E", "F"]) as specified in T003a.

It exits with code 0 if valid, or code 1 if missing/invalid, printing a clear error.
"""

import os
import sys
import toml
from pathlib import Path

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"

def main():
    """Verify pyproject.toml configuration."""
    print(f"Checking: {PYPROJECT_PATH}")

    if not PYPROJECT_PATH.exists():
        print("ERROR: pyproject.toml not found in project root.")
        sys.exit(1)

    try:
        with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
            config = toml.load(f)
    except Exception as e:
        print(f"ERROR: Failed to parse pyproject.toml: {e}")
        sys.exit(1)

    errors = []

    # Check Black configuration
    tool_black = config.get("tool", {}).get("black", {})
    if not tool_black:
        errors.append("Missing [tool.black] section.")
    else:
        line_length = tool_black.get("line-length")
        if line_length != 88:
            errors.append(f"Invalid [tool.black] line-length: expected 88, got {line_length}.")
        else:
            print("OK: [tool.black] configured with line-length=88.")

    # Check Ruff configuration
    tool_ruff = config.get("tool", {}).get("ruff", {})
    if not tool_ruff:
        errors.append("Missing [tool.ruff] section.")
    else:
        lint = tool_ruff.get("lint", {})
        if not lint:
            errors.append("Missing [tool.ruff.lint] section.")
        else:
            select = lint.get("select", [])
            required = {"E", "F"}
            if not required.issubset(set(select)):
                errors.append(
                    f"Invalid [tool.ruff.lint.select]: expected to include {required}, got {select}."
                )
            else:
                print(f"OK: [tool.ruff.lint] configured with select={select}.")

    if errors:
        print("\nVALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("\nVALIDATION PASSED: pyproject.toml is correctly configured.")
    sys.exit(0)

if __name__ == "__main__":
    main()
