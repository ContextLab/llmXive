"""
Integration test for linting and formatting compliance (Task T003).

This test ensures that the project's codebase passes both Ruff linting and Black
formatting checks without any violations. It is executed as part of the CI test
suite, providing the required evidence that ``ruff check .`` and ``black --check .``
both return an exit code of 0.
"""

import subprocess
from pathlib import Path

import pytest

# Locate the project root (the directory containing this test file's parent directories)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

@pytest.mark.integration
def test_ruff_linting_passes():
    """Run ``ruff check .`` and assert it exits with code 0."""
    result = subprocess.run(
        ["ruff", "check", "."],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert result.returncode == 0, (
        f"Ruff linting failed with exit code {result.returncode}.\n"
        f"Output:\n{result.stdout}"
    )

@pytest.mark.integration
def test_black_formatting_passes():
    """Run ``black --check .`` and assert it exits with code 0."""
    result = subprocess.run(
        ["black", "--check", "."],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert result.returncode == 0, (
        f"Black formatting check failed with exit code {result.returncode}.\n"
        f"Output:\n{result.stdout}"
    )