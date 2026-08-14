"""
Contract tests for linting configuration validation.
Verifies that flake8 and black configurations are present and valid.
"""
import subprocess
import os
import pytest
from pathlib import Path
import tomli
import sys

# Add the project root to the path to allow imports if needed,
# though this test file primarily uses subprocess.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def test_flake8_config_exists():
    """Verify that .flake8 configuration file exists at the repository root."""
    flake8_path = PROJECT_ROOT / ".flake8"
    assert flake8_path.exists(), f"Configuration file .flake8 not found at {flake8_path}"
    assert flake8_path.stat().st_size > 0, "Configuration file .flake8 is empty"

def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists at the repository root."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), f"Configuration file pyproject.toml not found at {pyproject_path}"
    assert pyproject_path.stat().st_size > 0, "Configuration file pyproject.toml is empty"

def test_black_can_parse_config():
    """Verify that black can successfully parse the pyproject.toml configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    try:
        # Run black with --config to verify it can read the file
        result = subprocess.run(
            ["black", "--config", str(pyproject_path), "--check", "--diff", str(CODE_DIR)],
            capture_output=True,
            text=True,
            timeout=30
        )
        # Black returns 0 if files are already formatted, 1 if they need formatting.
        # We only care that it didn't crash with a config error (returncode 2).
        assert result.returncode != 2, f"Black failed to parse config: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Black is not installed in the environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Black check timed out")

def test_flake8_can_parse_config():
    """Verify that flake8 can successfully parse the .flake8 configuration."""
    flake8_path = PROJECT_ROOT / ".flake8"
    try:
        # Run flake8 with --config to verify it can read the file
        # We run it on a small subset or the whole code dir, expecting it to not crash.
        result = subprocess.run(
            ["flake8", "--config", str(flake8_path), str(CODE_DIR)],
            capture_output=True,
            text=True,
            timeout=60
        )
        # flake8 returns 0 if no issues, 1 if issues found, 2 if error.
        # We assert it did not return 2 (configuration error).
        assert result.returncode != 2, f"Flake8 failed to parse config: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Flake8 is not installed in the environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Flake8 check timed out")

def test_linting_rules_are_reasonable():
    """Verify that the linting configurations contain expected rules (e.g., max-line-length)."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    flake8_path = PROJECT_ROOT / ".flake8"

    # Check pyproject.toml for black settings
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomli.load(f)
    
    black_config = pyproject_data.get("tool", {}).get("black", {})
    assert "line-length" in black_config, "Black configuration missing 'line-length' in pyproject.toml"
    assert black_config["line-length"] == 88, f"Black line-length should be 88, got {black_config['line-length']}"

    # Check .flake8 for settings
    with open(flake8_path, "r") as f:
        content = f.read()
    
    assert "max-line-length" in content, ".flake8 configuration missing 'max-line-length'"
    assert "ignore" in content, ".flake8 configuration missing 'ignore' directive"
    
    # Verify specific ignores mentioned in T003a
    assert "E203" in content, ".flake8 must ignore E203"
    assert "W503" in content, ".flake8 must ignore W503"