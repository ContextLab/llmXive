"""Test that the project's requirements.txt can be installed without conflicts.

This test runs ``python -m pip install -r requirements.txt`` from the project
root and asserts that the command exits with a zero status. It provides the
execution evidence required for task T002.
"""
import subprocess
import sys
from pathlib import Path


def test_requirements_install():
    # Resolve the project root (two levels up from this test file)
    project_root = Path(__file__).resolve().parents[2]
    requirements_path = project_root / "requirements.txt"

    # Run pip install in a subprocess; capture output for debugging
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
        capture_output=True,
        text=True,
    )

    # If the installation fails, include stdout and stderr in the assertion message
    assert result.returncode == 0, (
        f"Pip install failed with exit code {result.returncode}\\n"
        f"STDOUT:\\n{result.stdout}\\n"
        f"STDERR:\\n{result.stderr}"
    )
