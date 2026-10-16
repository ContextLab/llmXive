"""
Integration test to verify that the project's pinned requirements can be installed
without version conflicts.

The test invokes ``python -m pip install -r requirements.txt`` using the same
interpreter that runs the test suite. It asserts a zero exit code and reports
any stdout/stderr on failure.
"""

import subprocess
import sys
from pathlib import Path

def test_requirements_install():
    # Resolve the path to the project's root requirements.txt
    project_root = Path(__file__).resolve().parents[2]
    requirements_file = project_root / "requirements.txt"

    # Run pip install in a subprocess to avoid affecting the current interpreter state
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # If installation fails, include stdout and stderr in the assertion message
    assert result.returncode == 0, (
        f"pip install failed with return code {result.returncode}\\n"
        f"STDOUT:\\n{result.stdout}\\n"
        f"STDERR:\\n{result.stderr}"
    )