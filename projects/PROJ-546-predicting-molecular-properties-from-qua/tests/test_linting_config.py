"""
Contract tests for T003: Verify that linting and formatting tools are configured.

This test ensures:
1. pyproject.toml exists and contains [tool.black] and [tool.ruff] sections.
2. .ruff.toml exists and is valid TOML.
3. The configuration files are syntactically correct.
"""
import os
import tomllib
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "code" / "pyproject.toml"
RUFF_CONFIG_PATH = PROJECT_ROOT / "code" / ".ruff.toml"

def test_pyproject_exists():
    """Verify pyproject.toml exists in the code directory."""
    assert PYPROJECT_PATH.exists(), f"pyproject.toml not found at {PYPROJECT_PATH}"

def test_ruff_config_exists():
    """Verify .ruff.toml exists in the code directory."""
    assert RUFF_CONFIG_PATH.exists(), f".ruff.toml not found at {RUFF_CONFIG_PATH}"

def test_pyproject_contains_black_config():
    """Verify pyproject.toml contains [tool.black] section."""
    with open(PYPROJECT_PATH, "rb") as f:
        config = tomllib.load(f)
    
    assert "tool" in config, "No [tool] section in pyproject.toml"
    assert "black" in config["tool"], "No [tool.black] section in pyproject.toml"
    
    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "[tool.black] missing line-length"
    assert black_config["line-length"] == 88, "Black line-length should be 88"
    assert "target-version" in black_config, "[tool.black] missing target-version"

def test_pyproject_contains_ruff_config():
    """Verify pyproject.toml contains [tool.ruff] section or extends .ruff.toml."""
    with open(PYPROJECT_PATH, "rb") as f:
        config = tomllib.load(f)
    
    assert "tool" in config, "No [tool] section in pyproject.toml"
    assert "ruff" in config["tool"], "No [tool.ruff] section in pyproject.toml"

def test_ruff_config_is_valid_toml():
    """Verify .ruff.toml is valid TOML syntax."""
    with open(RUFF_CONFIG_PATH, "rb") as f:
        try:
            config = tomllib.load(f)
            # Verify basic structure
            assert "lint" in config or "target-version" in config, \
                "Invalid ruff config structure"
        except tomllib.TOMLDecodeError as e:
            pytest.fail(f".ruff.toml is not valid TOML: {e}")

def test_requirements_includes_linting_tools():
    """Verify requirements.txt includes ruff and black."""
    req_path = PROJECT_ROOT / "code" / "requirements.txt"
    assert req_path.exists(), "requirements.txt not found"
    
    content = req_path.read_text()
    assert "ruff" in content.lower(), "ruff not in requirements.txt"
    assert "black" in content.lower(), "black not in requirements.txt"