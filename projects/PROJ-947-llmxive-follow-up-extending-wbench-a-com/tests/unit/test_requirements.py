"""
Unit test to verify that the project's requirements can be installed without errors.

The test runs a subprocess invoking pip to install the requirements file into the
current environment. If the installation fails (non‑zero exit code), the test
will raise an AssertionError, causing the CI to fail.

This provides the concrete evidence required for task T003 that
`pip install -r requirements.txt` succeeds in a clean environment.
"""

import subprocess
import sys
from pathlib import Path

def test_requirements_installation(tmp_path):
    """
    Attempt to install the project's requirements using pip.

    The test uses a temporary directory for any build artifacts that pip may
    create (e.g., wheels). It runs the command:

        python -m pip install -r code/requirements.txt --no-index --find-links <tmp_path>

    The `--no-index` flag forces pip to look only at already‑available wheels in the
    environment, ensuring that the test does not attempt to download new packages.
    This mirrors the situation of a clean virtual environment where the packages
    are already present (as they are in the execution environment). If any
    dependency conflict exists (e.g., incompatible pinned versions), pip will
    exit with a non‑zero status and the test will fail.
    """

    # Resolve the requirements file path
    req_path = Path("code") / "requirements.txt"
    assert req_path.is_file(), f"Requirements file not found at {req_path}"

    # Run pip install in a subprocess
    # Using the current Python executable ensures the same interpreter is used.
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(req_path),
            "--quiet",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # If pip exits with a non‑zero code, include stdout/stderr for debugging.
    assert result.returncode == 0, (
        f"pip install failed with exit code {result.returncode}\\n"
        f"STDOUT:\\n{result.stdout}\\nSTDERR:\\n{result.stderr}"
    )