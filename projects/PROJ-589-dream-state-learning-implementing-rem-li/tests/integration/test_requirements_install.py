"""
Integration test that ensures the project's pinned dependencies can be
installed without errors.

The test runs ``pip install -r code/requirements.txt`` in a subprocess
and asserts that the command exits with status code 0.
"""

import subprocess
import sys
from pathlib import Path

def test_requirements_install():
    requirements_path = Path("code") / "requirements.txt"
    assert requirements_path.is_file(), f"{requirements_path} does not exist"

    # Run pip install in a subprocess; use the same Python executable
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # For debugging, you can print result.stdout / result.stderr if needed
    assert result.returncode == 0, (
        f"pip install failed with exit code {result.returncode}\\n"
        f"stdout: {result.stdout}\\nstderr: {result.stderr}"
    )