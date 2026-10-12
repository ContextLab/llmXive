"""
Integration test to verify that the project's pinned dependencies can be installed
via the requirements.txt file without errors.

The test invokes the current Python interpreter's pip module to install the
requirements into the active virtual environment. It asserts that the subprocess
exits with a zero return code, indicating a successful installation.

This test is deliberately lightweight: it relies on pip's ability to recognize
already‑installed packages and skip them, so it runs quickly even in environments
where the dependencies are pre‑installed.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
def test_requirements_install_success():
    """
    Run ``python -m pip install -r requirements.txt`` and ensure it succeeds.
    """
    # Resolve the path to the requirements.txt file relative to the project root.
    # The test runner's current working directory is the repository root.
    requirements_path = Path("requirements.txt")
    assert requirements_path.is_file(), "requirements.txt not found at repository root"

    # Build the pip install command.
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        str(requirements_path),
        "--quiet",
    ]

    # Execute the command and capture output.
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # If pip fails, include stdout and stderr in the assertion message for debugging.
    assert result.returncode == 0, (
        f"Pip install failed with exit code {result.returncode}\\n"
        f"STDOUT:\\n{result.stdout}\\nSTDERR:\\n{result.stderr}"
    )