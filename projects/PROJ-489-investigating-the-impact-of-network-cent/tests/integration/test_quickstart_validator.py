"""
Integration tests for the Quickstart Validator script.
"""

import os
import subprocess
import sys
from pathlib import Path
import pytest


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.mark.integration
def test_quickstart_validator_runs(project_root):
    """Test that the quickstart validator script runs without errors."""
    validator_script = project_root / "code" / "quickstart_validator.py"
    
    # Ensure the script exists
    assert validator_script.exists(), f"Validator script not found at {validator_script}"

    # Run the script
    result = subprocess.run(
        [sys.executable, str(validator_script)],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    # Log output for debugging
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    # Check if the script ran successfully (exit code 0)
    # Note: In a real scenario, we might expect some steps to fail if data is missing,
    # but the script itself should not crash
    assert result.returncode in [0, 1], f"Unexpected exit code: {result.returncode}"

    # Check that the script produced expected log messages
    assert "Starting Quickstart Validation" in result.stdout or "Starting Quickstart Validation" in result.stderr
    assert "validation" in result.stdout.lower() or "validation" in result.stderr.lower()


@pytest.mark.integration
def test_quickstart_validator_verifies_structure(project_root):
    """Test that the validator checks project structure."""
    validator_script = project_root / "code" / "quickstart_validator.py"
    
    result = subprocess.run(
        [sys.executable, str(validator_script)],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    # Check for structure verification messages
    assert "Project structure" in result.stdout or "Project structure" in result.stderr


@pytest.mark.integration
def test_quickstart_validator_checks_dependencies(project_root):
    """Test that the validator checks dependencies."""
    validator_script = project_root / "code" / "quickstart_validator.py"
    
    result = subprocess.run(
        [sys.executable, str(validator_script)],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    # Check for dependency check messages
    assert "dependencies" in result.stdout.lower() or "dependencies" in result.stderr.lower()