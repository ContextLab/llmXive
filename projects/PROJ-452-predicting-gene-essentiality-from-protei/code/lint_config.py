"""
Linting configuration for the project.
This module provides a simple wrapper to run flake8 and other linters.
"""
import subprocess
import sys
from pathlib import Path


def run_flake8(max_complexity: int = 10) -> None:
    """
    Run flake8 on the code directory with specified complexity limit.

    Args:
        max_complexity: Maximum allowed cyclomatic complexity.
    """
    code_dir = Path(__file__).parent
    cmd = [
        "flake8",
        str(code_dir),
        f"--max-complexity={max_complexity}",
        "--ignore=E501,W503",  # Ignore line length and line break before binary operator
        "--exclude=__pycache__"
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        sys.exit(1)


def run_black() -> None:
    """Run black formatter on the code directory."""
    code_dir = Path(__file__).parent
    cmd = ["black", str(code_dir)]

    try:
        subprocess.run(cmd, check=True)
        print("Black formatting complete.")
    except subprocess.CalledProcessError as e:
        print(f"Black formatting failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_flake8()
    run_black()