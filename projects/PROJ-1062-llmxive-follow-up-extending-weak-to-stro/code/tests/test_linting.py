import subprocess
import sys
import os
from pathlib import Path
import pytest

def test_ruff_installed():
    """Test that ruff is installed and accessible."""
    try:
        subprocess.check_call([sys.executable, "-m", "ruff", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        pytest.fail("Ruff is not installed or not accessible.")

def test_black_installed():
    """Test that black is installed and accessible."""
    try:
        subprocess.check_call([sys.executable, "-m", "black", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        pytest.fail("Black is not installed or not accessible.")

def test_ruff_config_exists():
    """Test that ruff configuration file exists."""
    config_path = Path("code/.ruff.toml")
    assert config_path.exists(), f"Ruff config file not found at {config_path}"

def test_black_config_exists():
    """Test that black configuration file exists."""
    config_path = Path("code/py.toml")
    assert config_path.exists(), f"Black config file not found at {config_path}"

def test_precommit_config_exists():
    """Test that pre-commit configuration file exists."""
    config_path = Path("code/.pre-commit-config.yaml")
    assert config_path.exists(), f"Pre-commit config file not found at {config_path}"

def test_run_lint_script_exists():
    """Test that run_lint script exists."""
    script_path = Path("code/scripts/run_lint.py")
    assert script_path.exists(), f"Run lint script not found at {script_path}"

def test_run_format_script_exists():
    """Test that run_format script exists."""
    script_path = Path("code/scripts/run_format.py")
    assert script_path.exists(), f"Run format script not found at {script_path}"

def test_ruff_check_passes():
    """Test that ruff check passes on the codebase."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "code/"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_check_passes():
    """Test that black check passes on the codebase."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "code/"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"
