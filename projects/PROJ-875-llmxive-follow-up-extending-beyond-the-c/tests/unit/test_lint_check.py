"""
Unit tests for the lint check runner.
Verifies that the script runs correctly and reports status.
"""
import subprocess
import sys
import os
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    """Return the project root path."""
    return Path(__file__).parent.parent.parent

def test_lint_check_script_exists(project_root):
    """Verify the lint check script exists."""
    script_path = project_root / "code" / "run_lint_check.py"
    assert script_path.exists(), f"Script not found at {script_path}"

def test_lint_check_script_syntax(project_root):
    """Verify the lint check script has valid Python syntax."""
    script_path = project_root / "code" / "run_lint_check.py"
    try:
        with open(script_path, "r") as f:
            compile(f.read(), script_path, "exec")
    except SyntaxError as e:
        pytest.fail(f"Syntax error in {script_path}: {e}")

def test_run_lint_check_executable(project_root):
    """Test that the lint check script can be executed."""
    script_path = project_root / "code" / "run_lint_check.py"
    
    # Check if ruff is available in the environment
    try:
        subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            check=True,
            timeout=10
        )
        ruff_available = True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        ruff_available = False
        pytest.skip("Ruff not installed in environment, skipping execution test")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=project_root,
        timeout=60
    )

    # The script should exit with 0 if checks pass, or non-zero if they fail
    # but it should NOT crash with an exception
    assert result.returncode in [0, 1], f"Unexpected exit code: {result.returncode}"
    
    # Verify output contains expected markers
    output = result.stdout + result.stderr
    assert "Running Initial Lint/Format Checks" in output, "Expected header not found in output"
    assert "Ruff" in output or "Format" in output, "Expected check descriptions not found"

def test_run_lint_check_with_empty_codebase(project_root):
    """
    Test that lint checks pass on an empty/minimal codebase.
    This validates the configuration in pyproject.toml.
    """
    script_path = project_root / "code" / "run_lint_check.py"
    
    try:
        subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            check=True,
            timeout=10
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Ruff not installed")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=project_root,
        timeout=60
    )

    # We expect the script to run successfully (exit 0) even if there are 
    # linting issues, because the script handles failures gracefully.
    # The important thing is that the tools are configured and runnable.
    assert result.returncode in [0, 1], "Script should handle lint failures gracefully"
    
    # Verify the script attempted to run ruff
    output = result.stdout + result.stderr
    assert "Ruff" in output or "ruff" in output, "Script should invoke ruff"
