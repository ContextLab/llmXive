"""
Simple wrapper that runs the project's linting and formatting checks.
Returns exit code 0 on success, non‑zero otherwise.
"""
import subprocess
import sys
from pathlib import Path

# Project root is two levels up from this script (code/scripts/..)
project_root = Path(__file__).resolve().parents[2]

def _run_cmd(command: list[str]) -> int:
    """Run a command and stream its output."""
    result = subprocess.run(
        command,
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    sys.stdout.write(result.stdout)
    return result.returncode

def main() -> int:
    """Execute ruff and black checks."""
    # Ruff (lint)
    rc = _run_cmd(["ruff", "--quiet", "."])
    if rc != 0:
        return rc
    # Black (formatting)
    rc = _run_cmd(["black", "--check", "."])
    return rc

if __name__ == "__main__":
    sys.exit(main())