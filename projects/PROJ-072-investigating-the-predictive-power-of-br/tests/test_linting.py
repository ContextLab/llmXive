"""
Smoke test to verify that ruff and black configurations are valid
and that the codebase passes basic linting rules defined in the task.
"""
import subprocess
import sys
import os

def test_ruff_config_exists():
    """Verify ruff configuration file exists."""
    assert os.path.exists("code/.ruff.toml"), "code/.ruff.toml must exist"

def test_pyproject_config_exists():
    """Verify pyproject.toml exists with tool configurations."""
    assert os.path.exists("pyproject.toml"), "pyproject.toml must exist"
    with open("pyproject.toml", "r") as f:
        content = f.read()
        assert "[tool.black]" in content, "pyproject.toml must contain [tool.black]"
        assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff]"

def test_scripts_exist():
    """Verify helper scripts exist."""
    assert os.path.exists("scripts/format.sh"), "scripts/format.sh must exist"
    assert os.path.exists("scripts/lint.sh"), "scripts/lint.sh must exist"

def test_ruff_check_passes():
    """Run ruff check on the codebase to ensure no immediate violations."""
    # We run ruff check specifically on the code directory
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "code/", "tests/"],
        capture_output=True,
        text=True
    )
    # If ruff is not installed, this test might fail, but that's an env issue, not code
    # We assume the environment has ruff installed as per T002 requirements
    if result.returncode != 0 and "No module named 'ruff'" in result.stderr:
        # Skip if ruff not installed in test environment
        import pytest
        pytest.skip("ruff not installed in test environment")
    
    # We expect returncode 0 for a clean pass. 
    # If there are issues, we fail the test to alert the developer.
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_check_passes():
    """Run black check (diff mode) on the codebase."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "code/", "tests/"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0 and "No module named 'black'" in result.stderr:
        import pytest
        pytest.skip("black not installed in test environment")

    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"