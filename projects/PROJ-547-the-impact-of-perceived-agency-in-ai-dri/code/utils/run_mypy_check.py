"""
Script to run MyPy type checking on the utils module.

This script invokes MyPy to check the type hints in the utils module and
ensures there are no type errors.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_mypy_check() -> int:
    """
    Run MyPy on the utils module.

    Returns:
        Exit code: 0 if MyPy passes, 1 if there are errors.
    """
    project_root = Path(__file__).parent.parent.parent
    utils_path = project_root / "code" / "utils"

    mypy_cmd = [
        sys.executable,
        "-m",
        "mypy",
        "--strict",
        "--ignore-missing-imports",
        "--no-error-summary",
        str(utils_path),
    ]

    print(f"Running MyPy on {utils_path}...")
    result = subprocess.run(mypy_cmd, cwd=project_root)

    if result.returncode == 0:
        print("MyPy check passed successfully!")
    else:
        print("MyPy check failed. Please fix the type errors above.")

    return result.returncode


if __name__ == "__main__":
    sys.exit(run_mypy_check())
