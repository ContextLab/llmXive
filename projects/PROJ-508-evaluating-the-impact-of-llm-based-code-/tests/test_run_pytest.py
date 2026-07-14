"""
Test suite for T057: Run pytest suite and ensure pass rate.

This module verifies that the project's pytest configuration is valid
and that the existing test scaffolding (T016) passes.
"""
import subprocess
import sys
import os
import json
from pathlib import Path

import pytest

# Ensure we are in the project root context for imports
# In a real CI environment, the working directory would be set correctly.
# Here we adjust sys.path to allow importing from code/
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_pytest_configuration_exists():
    """Verify that pytest configuration files exist (pyproject.toml or pytest.ini)."""
    config_files = ["pyproject.toml", "pytest.ini", "setup.cfg"]
    exists = any((PROJECT_ROOT / f).exists() for f in config_files)
    assert exists, "No pytest configuration file found (pyproject.toml, pytest.ini, or setup.cfg)."

def test_pytest_can_discover_tests():
    """Verify that pytest can successfully discover tests in the tests/ directory."""
    tests_dir = PROJECT_ROOT / "tests"
    if not tests_dir.exists():
        pytest.skip("Tests directory does not exist yet.")
    
    # Run pytest with --collect-only to check discovery without execution
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tests_dir), "--collect-only", "-q"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    # If it returns 0 or 5 (no tests collected but no error), it's okay.
    # 5 means "no tests collected", which is valid if the directory is empty.
    # 0 means tests were found.
    # Any other code implies a configuration or import error.
    assert result.returncode in (0, 5), (
        f"Pytest collection failed.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

def test_pytest_execution_success():
    """
    Run the full pytest suite and assert that the pass rate is 100%
    (or that no failures occur).
    
    This simulates the T057 requirement: 'Run pytest suite and ensure [deferred] pass rate'.
    """
    tests_dir = PROJECT_ROOT / "tests"
    if not tests_dir.exists():
        pytest.skip("Tests directory does not exist yet.")

    # Run pytest with verbose output to capture results
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tests_dir), "-v", "--tb=short"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    # Check for failures (return code 1)
    # Return code 0 = success
    # Return code 5 = no tests collected (valid if empty)
    if result.returncode not in (0, 5):
        # Log the failure for debugging
        print(f"Pytest execution failed with code {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        # Assert to fail the test
        assert False, "Pytest suite execution failed. See output above."
    
    # If we get here, the suite ran without errors or had no tests (which is acceptable for scaffolding)
    assert True, "Pytest suite executed successfully."

def test_required_dependencies_importable():
    """
    Verify that the core dependencies listed in requirements.txt are importable.
    This ensures the environment is set up correctly for T057.
    """
    required_packages = [
        "pandas",
        "requests",
        "scikit-learn",
        "statsmodels",
        "matplotlib",
        "seaborn",
        "pyyaml",
        "scipy"
    ]
    
    missing = []
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    assert not missing, f"Missing required dependencies: {missing}"
