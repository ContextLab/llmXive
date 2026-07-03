"""Quickstart validator module."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Entry point for quickstart validation."""
    # Delegate to the main script in the same directory
    script_path = Path(__file__).parent / "run_quickstart_validation.py"
    if script_path.exists():
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=script_path.parent.parent,
        )
        return result.returncode
    else:
        print(f"ERROR: Script not found at {script_path}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
