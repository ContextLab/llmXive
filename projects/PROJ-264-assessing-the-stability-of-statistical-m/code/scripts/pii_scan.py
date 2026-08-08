"""
PII Scan Script

This script executes ruff check with PII rules (PI) enabled against the codebase.
It satisfies Constitution Principle III (Data Hygiene) by failing the build if
potential PII patterns are detected.

Usage:
    python code/scripts/pii_scan.py

Exit Codes:
    0: No PII detected.
    1: PII detected, configuration missing, or ruff execution error.
"""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """
    Execute ruff check with PII rules enabled.

    Returns:
        int: 0 if no PII detected, 1 if PII detected or error occurs.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    ruff_config = project_root / ".ruff.toml"

    if not ruff_config.exists():
        print("Error: .ruff.toml configuration file not found.", file=sys.stderr)
        print("Please run task T003a to configure ruff first.", file=sys.stderr)
        return 1

    # Run ruff check with PII rules (PI) enabled
    # We explicitly enable PI rules to satisfy Constitution Principle III
    # Target the 'code' directory where source artifacts reside
    target_dir = project_root / "code"

    if not target_dir.exists():
        print(f"Error: Target directory '{target_dir}' not found.", file=sys.stderr)
        return 1

    cmd = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        str(target_dir),
        "--config",
        str(ruff_config),
        "--select",
        "PI",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        # Ruff returns non-zero exit code if violations are found or errors occur
        if result.returncode != 0:
            print("PII Detection Failed: Potential PII patterns found in codebase.", file=sys.stderr)
            if result.stdout:
                print(result.stdout, file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return 1

        print("No PII detected. Scan passed.")
        return 0

    except FileNotFoundError:
        print("Error: ruff is not installed or not found in PATH.", file=sys.stderr)
        print("Please install it via: pip install ruff", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error during PII scan: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())