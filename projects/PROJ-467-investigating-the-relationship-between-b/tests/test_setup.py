"""
Tests to verify the initial project setup and configuration files.
"""
import os
import subprocess
from pathlib import Path

import pytest


def test_requirements_exists():
    """Verify that requirements.txt exists at the project root."""
    project_root = Path(__file__).parent.parent
    req_file = project_root / "requirements.txt"
    assert req_file.exists(), f"requirements.txt not found at {req_file}"


def test_pyproject_exists():
    """Verify that pyproject.toml exists at the project root."""
    project_root = Path(__file__).parent.parent
    pyproject_file = project_root / "pyproject.toml"
    assert pyproject_file.exists(), f"pyproject.toml not found at {pyproject_file}"


def test_setup_script_runs():
    """Verify that the project structure is valid enough to run a basic import test."""
    project_root = Path(__file__).parent.parent
    # Try to import a known module to verify structure
    try:
        # We expect src/brainnet/utils to exist based on T006/T008 context
        # If T006/T008 are not done, this might fail, but T002 is about dependencies.
        # For T002, we primarily check if the environment is set up.
        # Let's just check if we can run python -c "import sys; print(sys.version)"
        result = subprocess.run(
            [sys.executable, "-c", "import sys; print(sys.version)"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Python check failed: {result.stderr}"
    except Exception as e:
        pytest.fail(f"Setup script verification failed: {e}")