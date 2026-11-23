"""
Test suite to verify that the codebase passes the ruff linter.
This script executes 'ruff --check' on the code/ directory.
It asserts that the exit code is 0.
"""
import subprocess
import sys
from pathlib import Path

def test_ruff_lint_passes():
    """
    Runs ruff --check on the code/ directory.
    Raises AssertionError if the exit code is not 0.
    """
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        raise FileNotFoundError(f"Code directory not found at {code_dir}")

    result = subprocess.run(
        ["ruff", "check", str(code_dir)],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        error_msg = (
            f"Ruff linting failed with exit code {result.returncode}.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
        raise AssertionError(error_msg)

    print("Ruff linting passed successfully.")

if __name__ == "__main__":
    test_ruff_lint_passes()
    print("Test completed: T035a (ruff check) verified.")
