"""
test_requirements.py

Integration test for ``src.verify_requirements``.  It runs the verification
script as a subprocess, checks that it exits with status 0, and asserts that
the expected ``requirements_freeze.txt`` artifact has been written.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def test_verify_requirements_script():
    """
    Execute ``python -m src.verify_requirements`` and verify success.
    """
    # Run the verification module.
    result = subprocess.run(
        [sys.executable, "-m", "src.verify_requirements"],
        capture_output=True,
        text=True,
    )
    # The script must exit cleanly.
    assert result.returncode == 0, (
        f"verify_requirements failed (exit {result.returncode}). "
        f"Stderr: {result.stderr}"
    )

    # The freeze file must exist in the ``data`` directory.
    freeze_path = paths.data("requirements_freeze.txt")
    assert freeze_path.is_file(), f"Expected freeze file at {freeze_path} not found."

    # Optional sanity‑check: ensure the freeze file contains at least one pinned package.
    content = freeze_path.read_text()
    assert "datasets==" in content, "Frozen output does not contain expected packages."