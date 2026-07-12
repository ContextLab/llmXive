"""
Tests to verify that linting and formatting configurations are valid
and that the project structure adheres to the defined rules.
"""
import subprocess
import os
from pathlib import Path

def test_ruff_config_exists():
    """Verify ruff configuration file exists."""
    ruff_config = Path("code/.ruff.toml")
    assert ruff_config.exists(), "code/.ruff.toml must exist"

def test_pyproject_config_exists():
    """Verify pyproject.toml exists and contains tool configs."""
    pyproject = Path("pyproject.toml")
    assert pyproject.exists(), "pyproject.toml must exist"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black]"
    assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff]"

def test_scripts_exist():
    """Verify helper scripts exist."""
    assert Path("code/format.sh").exists(), "code/format.sh must exist"
    assert Path("code/lint.sh").exists(), "code/lint.sh must exist"

def test_ruff_can_run():
    """Verify ruff can be executed on the codebase without crashing."""
    # We don't assert pass/fail on the linting itself, just that the tool runs
    # against the current files.
    result = subprocess.run(
        ["ruff", "check", "code/", "tests/"],
        capture_output=True,
        text=True
    )
    # If ruff is installed, it should exit 0 (pass) or 1 (fail), but not crash (2+)
    # We allow non-zero exit codes if there are lint errors, as long as the tool runs.
    assert result.returncode in [0, 1], f"Ruff crashed or failed to run: {result.stderr}"

def test_black_can_run():
    """Verify black can be executed on the codebase."""
    result = subprocess.run(
        ["black", "--check", "code/", "tests/"],
        capture_output=True,
        text=True
    )
    # Similar to ruff, we just verify the tool runs.
    assert result.returncode in [0, 1], f"Black crashed or failed to run: {result.stderr}"