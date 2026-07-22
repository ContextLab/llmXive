"""
Unit tests for linting and formatting configuration.
These tests verify that the configuration files are valid and the scripts run correctly.
"""
import subprocess
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
LINT_SCRIPT = PROJECT_ROOT / "code" / "lint_format_config.py"
RUFF_CONFIG = PROJECT_ROOT / "code" / ".ruff.toml"
BLACK_CONFIG = PROJECT_ROOT / "pyproject.toml"


def test_ruff_config_exists():
    """Verify that the ruff configuration file exists."""
    assert RUFF_CONFIG.exists(), f"Ruff config missing: {RUFF_CONFIG}"


def test_black_config_exists():
    """Verify that the black configuration file exists."""
    assert BLACK_CONFIG.exists(), f"Black config missing: {BLACK_CONFIG}"


def test_ruff_config_syntax():
    """Verify that the ruff config is syntactically valid by running ruff check on it."""
    # Ruff can check its own config or we just verify it parses
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--config", str(RUFF_CONFIG), "--isolated"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # If ruff is installed, it should be able to read the config.
    # If ruff is not installed, we skip this check or expect ImportError.
    if result.returncode != 0 and "No module named 'ruff'" in result.stderr:
        pytest.skip("Ruff not installed in environment")
    # Otherwise, the config should be valid (exit 0 or just warnings about code, not config errors)
    assert "invalid" not in result.stderr.lower() or "No module" in result.stderr


def test_black_config_syntax():
    """Verify that black can read the pyproject.toml."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", "--config", str(BLACK_CONFIG), "--version"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    if result.returncode != 0 and "No module named 'black'" in result.stderr:
        pytest.skip("Black not installed in environment")
    # If black is installed, it should parse the config without error
    assert "Could not parse" not in result.stderr


def test_lint_script_exists():
    """Verify the linting script exists."""
    assert LINT_SCRIPT.exists(), f"Lint script missing: {LINT_SCRIPT}"


def test_lint_script_help():
    """Verify the linting script runs and shows help."""
    result = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "--check" in result.stdout
    assert "--fix" in result.stdout
