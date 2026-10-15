"""
Test that the project's pinned requirements can be installed without error.
This validates the T002 artifact by exercising `pip install -r code/requirements.txt`
in the current environment (which mimics a fresh virtual environment for the CI).
"""

import subprocess
import sys


def test_requirements_install():
    """
    Run pip install on the pinned requirements file.
    The command should exit with a zero status code.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "code/requirements.txt"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # Debug output can be helpful if the test fails
    assert result.returncode == 0, (
        f"pip install failed with exit code {result.returncode}\\n"
        f"stdout:\\n{result.stdout}\\nstderr:\\n{result.stderr}"
    )