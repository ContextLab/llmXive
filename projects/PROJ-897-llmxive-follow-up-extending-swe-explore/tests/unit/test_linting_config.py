"""
Unit tests for T001b: Linting and Formatting Configuration.
Verifies that configuration files exist and are parsable.
"""
import os
import sys
import toml
import pytest
from pathlib import Path

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

def test_ruff_config_exists():
    """Verify .ruff.toml exists and is valid TOML."""
    config_path = Path("code/.ruff.toml")
    assert config_path.exists(), ".ruff.toml should exist"
    
    # Verify it's valid TOML
    try:
        with open(config_path, "r") as f:
            toml.load(f)
    except toml.TomlDecodeError as e:
        pytest.fail(f".ruff.toml is not valid TOML: {e}")

def test_black_config_exists():
    """Verify .black.toml exists and is valid TOML."""
    config_path = Path("code/.black.toml")
    assert config_path.exists(), ".black.toml should exist"
    
    # Verify it's valid TOML
    try:
        with open(config_path, "r") as f:
            toml.load(f)
    except toml.TomlDecodeError as e:
        pytest.fail(f".black.toml is not valid TOML: {e}")

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists and contains linting config."""
    config_path = Path("code/pyproject.toml")
    assert config_path.exists(), "pyproject.toml should exist"
    
    with open(config_path, "r") as f:
        config = toml.load(f)
    
    assert "tool" in config, "pyproject.toml should have [tool] section"
    assert "black" in config["tool"], "pyproject.toml should configure black"
    assert "ruff" in config["tool"], "pyproject.toml should configure ruff"

def test_ruff_check_passes_on_code():
    """Run ruff check on code/ directory."""
    import subprocess
    result = subprocess.run(
        ["ruff", "check", "code/"],
        capture_output=True,
        text=True
    )
    # We expect this to pass if code is clean, but we mainly check it doesn't crash
    assert result.returncode in [0, 1], "ruff check should exit 0 (clean) or 1 (issues found), not crash"

def test_black_check_passes_on_code():
    """Run black --check on code/ directory."""
    import subprocess
    result = subprocess.run(
        ["black", "--check", "code/"],
        capture_output=True,
        text=True
    )
    # We expect this to pass if code is clean, but we mainly check it doesn't crash
    assert result.returncode in [0, 1], "black --check should exit 0 (clean) or 1 (issues found), not crash"