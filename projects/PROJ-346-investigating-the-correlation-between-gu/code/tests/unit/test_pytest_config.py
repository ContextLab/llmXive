"""
Unit tests to verify the pytest configuration and basic runner functionality.
These tests ensure that the test environment is correctly set up.
"""
import os
import sys
import subprocess
from pathlib import Path
import pytest

def test_pytest_ini_exists(project_root):
    """Verify that pytest.ini exists in the code directory."""
    config_path = project_root / "code" / "pytest.ini"
    assert config_path.exists(), f"pytest.ini not found at {config_path}"

def test_run_tests_script_exists(project_root):
    """Verify that run_tests.sh exists in the code directory."""
    script_path = project_root / "code" / "run_tests.sh"
    assert script_path.exists(), f"run_tests.sh not found at {script_path}"

def test_run_tests_script_is_executable(project_root):
    """Verify that run_tests.sh has execute permissions."""
    script_path = project_root / "code" / "run_tests.sh"
    # On Windows, permissions are different, but we check the file exists
    # and is a script. The actual execution might depend on the shell.
    assert os.access(script_path, os.X_OK) or sys.platform.startswith('win'), \
        "run_tests.sh does not have execute permissions"

def test_conftest_py_exists(project_root):
    """Verify that the local conftest.py exists."""
    conftest_path = project_root / "code" / "tests" / "conftest.py"
    assert conftest_path.exists(), f"conftest.py not found at {conftest_path}"

def test_pytest_collects_tests(project_root):
    """Verify that pytest can discover tests in the tests directory."""
    # Run pytest in collection mode to check if it finds tests
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    # We expect it to find at least this test file
    assert result.returncode == 0, f"Pytest collection failed: {result.stderr}"
    assert "test_pytest_config.py" in result.stdout or "test_pytest_config" in result.stdout, \
        f"Pytest did not discover tests in the expected location. Output: {result.stdout}"