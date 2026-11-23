"""
Integration tests for the CI/CD pipeline.
These tests simulate the CI environment to ensure the pipeline
can successfully run the test suites without errors.
"""
import subprocess
import os
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent.parent

def test_unit_tests_run_successfully(project_root):
    """Verify that unit tests can be executed and pass."""
    result = subprocess.run(
        ["pytest", "tests/unit/", "-v", "--tb=short"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Unit tests failed:\n{result.stdout}\n{result.stderr}"

def test_integration_tests_run_successfully(project_root):
    """Verify that integration tests can be executed and pass."""
    result = subprocess.run(
        ["pytest", "tests/integration/", "-v", "--tb=short"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Integration tests failed:\n{result.stdout}\n{result.stderr}"

def test_contract_tests_run_successfully(project_root):
    """Verify that contract tests can be executed and pass."""
    result = subprocess.run(
        ["pytest", "tests/contract/", "-v", "--tb=short"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Contract tests failed:\n{result.stdout}\n{result.stderr}"

def test_all_tests_run_together(project_root):
    """Verify that all test suites can be run in sequence."""
    result = subprocess.run(
        ["pytest", "tests/unit/", "tests/integration/", "tests/contract/", "-v", "--tb=short"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Combined tests failed:\n{result.stdout}\n{result.stderr}"
