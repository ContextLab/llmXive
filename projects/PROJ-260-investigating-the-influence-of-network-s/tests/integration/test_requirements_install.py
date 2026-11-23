"""
Integration test to verify that the project's requirements can be installed
without version conflicts.

The test invokes the current Python interpreter's pip module to install the
packages listed in ``requirements.txt``. It asserts that the subprocess
exits with a zero return code, indicating a successful installation.

This provides concrete evidence for task T003's verification step:
``pip install -r requirements.txt`` succeeds.
"""
import subprocess
import sys
from pathlib import Path

import pytest

@pytest.mark.timeout(300)
def test_requirements_install():
    """
    Run ``pip install -r requirements.txt`` using the same interpreter that
    runs the tests and ensure it exits successfully.
    """
    # Resolve the path to requirements.txt relative to the project root
    project_root = Path(__file__).resolve().parents[2]  # tests/integration/..
    requirements_path = project_root / "requirements.txt"

    # Build the pip install command
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        str(requirements_path),
        "--quiet",          # suppress normal output; errors still raise non-zero exit
    ]

    # Execute the command
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # If pip fails, include stdout/stderr in the assertion message for debugging
    assert result.returncode == 0, (
        f"pip install failed with exit code {result.returncode}\\n"
        f"STDOUT:\\n{result.stdout}\\n"
        f"STDERR:\\n{result.stderr}"
    )