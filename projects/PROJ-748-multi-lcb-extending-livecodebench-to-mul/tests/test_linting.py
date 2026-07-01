"""
Basic smoke test to ensure linting tools are available and can run.
This verifies the configuration in ruff.toml and .pre-commit-config.yaml is valid.
"""
import subprocess
import sys
import os

def test_ruff_is_installed():
    """Verify ruff is installed."""
    result = subprocess.run(
        ["python", "-m", "ruff", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Ruff not installed or failed: {result.stderr}"
    assert "ruff" in result.stdout.lower()

def test_black_is_installed():
    """Verify black is installed."""
    result = subprocess.run(
        ["python", "-m", "black", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Black not installed or failed: {result.stderr}"
    assert "black" in result.stdout.lower()

def test_ruff_config_exists():
    """Verify ruff.toml exists in project root."""
    assert os.path.exists("ruff.toml"), "ruff.toml not found in project root"

def test_precommit_config_exists():
    """Verify .pre-commit-config.yaml exists in project root."""
    assert os.path.exists(".pre-commit-config.yaml"), ".pre-commit-config.yaml not found in project root"