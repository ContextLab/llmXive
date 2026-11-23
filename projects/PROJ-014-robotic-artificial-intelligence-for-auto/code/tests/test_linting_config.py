import os
import subprocess
import pytest
from pathlib import Path

def test_ruff_config_exists():
    """Verify ruff configuration file exists."""
    ruff_config = Path("code/.ruff.toml")
    pyproject = Path("code/pyproject.toml")
    assert ruff_config.exists() or pyproject.exists(), "Ruff config (.ruff.toml or pyproject.toml) must exist"

def test_black_config_exists():
    """Verify black configuration exists in pyproject.toml."""
    pyproject = Path("code/pyproject.toml")
    assert pyproject.exists(), "pyproject.toml must exist for Black configuration"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration section must exist in pyproject.toml"

def test_ruff_can_run():
    """Verify ruff can execute on the codebase."""
    try:
        result = subprocess.run(
            ["ruff", "check", "code/src", "code/scripts", "code/tests"],
            capture_output=True,
            text=True,
            timeout=60
        )
        # We expect it to run without crashing; lint errors are acceptable at this stage
        assert result.returncode in (0, 1), f"Ruff failed to run: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Ruff not installed in environment")

def test_black_can_run():
    """Verify black can execute on the codebase."""
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", "code/src", "code/scripts", "code/tests"],
            capture_output=True,
            text=True,
            timeout=60
        )
        # We expect it to run without crashing; formatting issues are acceptable
        assert result.returncode in (0, 1), f"Black failed to run: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Black not installed in environment")