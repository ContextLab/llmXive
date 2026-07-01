import os
import pytest
import subprocess
import sys

def test_requirements_dry_run():
    """
    Test that requirements.txt can be successfully dry-run installed.
    This verifies T002 completion.
    """
    # Determine the project root (two levels up from tests/unit)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    requirements_path = os.path.join(project_root, "requirements.txt")

    assert os.path.exists(requirements_path), f"requirements.txt missing at {requirements_path}"

    # Run pip install --dry-run
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", requirements_path, "--dry-run"],
        capture_output=True,
        text=True
    )

    # A dry-run failure usually indicates unresolvable dependencies or missing packages
    assert result.returncode == 0, f"pip dry-run failed:\n{result.stderr}"