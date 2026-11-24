"""
Test that the project's requirements can be installed without errors.
This validates task T002 which requires that running:
    pip install -r requirements.txt
returns an exit code of 0.
"""

import subprocess
import sys
from pathlib import Path

def test_requirements_install():
    """
    Execute pip install on the project's requirements file and assert success.
    The requirements.txt file lives under the ``code/`` directory.
    """
    # Resolve the path to the requirements file relative to the repository root
    requirements_path = Path(__file__).resolve().parents[2] / "code" / "requirements.txt"

    # Ensure the file exists; pytest will surface a clear error if it does not.
    assert requirements_path.is_file(), f"requirements.txt not found at {requirements_path}"

    # Run pip install in a subprocess. ``-q`` silences output; ``--disable-pip-version-check``
    # avoids unrelated warnings that could interfere with CI logs.
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "--disable-pip-version-check", "-r", str(requirements_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Provide debugging information on failure.
    assert result.returncode == 0, (
        f"pip install exited with code {result.returncode}\\n"
        f"stdout: {result.stdout}\\n"
        f"stderr: {result.stderr}"
    )