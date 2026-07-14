"""
Script to run MyPy static type checking on the code/utils/ package.

This script is used to verify that all utility modules have proper
type hints and pass MyPy checks with no errors.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Run MyPy on the code/utils/ directory."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    utils_dir = root_dir / "code" / "utils"

    if not utils_dir.exists():
        print(f"Error: Directory not found: {utils_dir}")
        sys.exit(1)

    print(f"Running MyPy on {utils_dir}...")
    result = subprocess.run(
        [sys.executable, "-m", "mypy", str(utils_dir)],
        cwd=root_dir,
    )

    if result.returncode == 0:
        print("MyPy check passed: No errors found.")
        sys.exit(0)
    else:
        print("MyPy check failed. Please fix the type errors above.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()