"""
Integration test for Task T002: Verify that the project's pinned dependencies can be
installed without version conflicts.

The test runs ``pip install -r code/requirements.txt`` in a subprocess and asserts
that the command exits with status code 0. Any non‑zero exit code indicates a
dependency conflict or installation failure, causing the test to fail.

This test provides the required verification evidence for the task description:
“pip install -r code/requirements.txt succeeds without version conflicts.”
"""

import subprocess
import sys
from pathlib import Path

import pytest

@pytest.mark.integration
def test_requirements_installation():
    """
    Run ``pip install -r code/requirements.txt`` and ensure it completes successfully.
    """
    # Resolve the path to the requirements file relative to the project root
    req_path = Path("code") / "requirements.txt"
    assert req_path.is_file(), f"Requirements file not found at {req_path}"

    # Execute pip install in a subprocess; use the same Python executable
    # to ensure the environment is consistent.
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # For debugging purposes, include the captured output in the assertion message.
    assert result.returncode == 0, (
        f"pip install failed with exit code {result.returncode}. "
        f"Output:\n{result.stdout}"
    )