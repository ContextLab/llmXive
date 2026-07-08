"""
Linting and formatting tests for the project codebase.
Ensures adherence to ruff and black standards.
"""
import subprocess
import sys
import os


def test_ruff_check_syntax():
    """Run ruff check on the code directory."""
    code_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
    result = subprocess.run(
        ["ruff", "check", code_dir],
        capture_output=True,
        text=True
    )
    # If there are errors, the test fails
    if result.returncode != 0:
        print("Ruff check failed:")
        print(result.stdout)
        print(result.stderr)
        assert False, "Ruff check failed"


def test_black_check_formatting():
    """Run black --check on the code directory."""
    code_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
    result = subprocess.run(
        ["black", "--check", code_dir],
        capture_output=True,
        text=True
    )
    # If there are formatting issues, the test fails
    if result.returncode != 0:
        print("Black check failed:")
        print(result.stdout)
        print(result.stderr)
        assert False, "Black check failed"
