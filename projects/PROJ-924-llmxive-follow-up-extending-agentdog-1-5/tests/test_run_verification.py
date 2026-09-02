import subprocess
import sys
import os
import pytest
from pathlib import Path

# Ensure the project root is in the path for imports if needed,
# though for this test we are primarily running pytest as a subprocess.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"

def test_ruff_config_exists():
    """
    Verify that the .ruff.toml configuration file exists and is non-empty.
    This test was defined in T010c.
    """
    ruff_config_path = PROJECT_ROOT / ".ruff.toml"
    assert ruff_config_path.exists(), f"File {ruff_config_path} does not exist."
    assert ruff_config_path.stat().st_size > 0, f"File {ruff_config_path} is empty."

def test_pyproject_config_exists():
    """
    Verify that the pyproject.toml configuration file exists and is non-empty.
    This test was defined in T010c.
    """
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), f"File {pyproject_path} does not exist."
    assert pyproject_path.stat().st_size > 0, f"File {pyproject_path} is empty."

def test_pytest_config_files_pass():
    """
    Run pytest specifically on the configuration verification tests
    to ensure they pass as per task T010d requirements.
    """
    # Construct the command to run pytest on the specific test file
    # We use sys.executable to ensure we run against the current environment
    pytest_cmd = [
        sys.executable, "-m", "pytest",
        str(TESTS_DIR / "test_config_files.py"),
        "-v",
        "--tb=short"
    ]

    # Execute the command
    result = subprocess.run(
        pytest_cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )

    # Assert that the exit code is 0 (success)
    assert result.returncode == 0, (
        f"Pytest failed with exit code {result.returncode}.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )