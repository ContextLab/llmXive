"""
Tests to verify that linting and formatting configurations exist and are valid.
"""
import subprocess
import sys
import os
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).parent.parent.parent

def test_ruff_installed():
    """Test that ruff is available in the environment."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Ruff not installed or failed: {result.stderr}"
    except FileNotFoundError:
        pytest.fail("Ruff is not installed in the environment.")

def test_black_installed():
    """Test that black is available in the environment."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Black not installed or failed: {result.stderr}"
    except FileNotFoundError:
        pytest.fail("Black is not installed in the environment.")

def test_ruff_config_exists():
    """Test that ruff configuration file exists."""
    config_path = ROOT_DIR / "pyproject.toml"
    assert config_path.exists(), "pyproject.toml (ruff config) not found"
    content = config_path.read_text()
    assert "[tool.ruff]" in content, "Ruff configuration section missing in pyproject.toml"

def test_black_config_exists():
    """Test that black configuration file exists."""
    config_path = ROOT_DIR / "pyproject.toml"
    assert config_path.exists(), "pyproject.toml (black config) not found"
    content = config_path.read_text()
    assert "[tool.black]" in content, "Black configuration section missing in pyproject.toml"

def test_precommit_config_exists():
    """Test that pre-commit configuration file exists."""
    config_path = ROOT_DIR / ".pre-commit-config.yaml"
    assert config_path.exists(), ".pre-commit-config.yaml not found"
    content = config_path.read_text()
    assert "ruff" in content, "Ruff not in pre-commit config"
    assert "black" in content, "Black not in pre-commit config"

def test_run_lint_script_exists():
    """Test that the run_lint.py script exists."""
    script_path = ROOT_DIR / "code" / "scripts" / "run_lint.py"
    assert script_path.exists(), "code/scripts/run_lint.py not found"

def test_run_format_script_exists():
    """Test that the run_format.py script exists."""
    script_path = ROOT_DIR / "code" / "scripts" / "run_format.py"
    assert script_path.exists(), "code/scripts/run_format.py not found"

def test_ruff_check_passes():
    """Test that ruff check passes on the codebase."""
    script_path = ROOT_DIR / "code" / "scripts" / "run_lint.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        timeout=60
    )
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_check_passes():
    """Test that black --check passes on the codebase."""
    script_path = ROOT_DIR / "code" / "scripts" / "run_format.py"
    # We run the format script, but we need to ensure it acts as a check if we want strict CI behavior.
    # For this test, we just verify the script runs successfully.
    # A stricter test would run `black --check` directly.
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(ROOT_DIR / "code")],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        timeout=60
    )
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"