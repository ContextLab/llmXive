"""
Unit tests to verify linting and formatting configuration files exist and are valid.
"""
import os
import toml
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent.parent

def test_ruff_config_exists(project_root):
    """Test that .ruff.toml exists in the code directory."""
    config_path = project_root / "code" / ".ruff.toml"
    assert config_path.exists(), f"Configuration file not found: {config_path}"

def test_black_config_exists(project_root):
    """Test that .black.toml exists in the code directory."""
    config_path = project_root / "code" / ".black.toml"
    assert config_path.exists(), f"Configuration file not found: {config_path}"

def test_ruff_config_valid(project_root):
    """Test that .ruff.toml is valid TOML."""
    config_path = project_root / "code" / ".ruff.toml"
    try:
        with open(config_path) as f:
            toml.load(f)
    except toml.TomlDecodeError:
        pytest.fail("Invalid TOML in .ruff.toml")

def test_black_config_valid(project_root):
    """Test that .black.toml is valid TOML."""
    config_path = project_root / "code" / ".black.toml"
    try:
        with open(config_path) as f:
            toml.load(f)
    except toml.TomlDecodeError:
        pytest.fail("Invalid TOML in .black.toml")

def test_requirements_has_ruff(project_root):
    """Test that requirements.txt includes ruff."""
    req_path = project_root / "requirements.txt"
    assert req_path.exists(), "requirements.txt not found"
    content = req_path.read_text().lower()
    assert "ruff" in content, "ruff not found in requirements.txt"

def test_requirements_has_black(project_root):
    """Test that requirements.txt includes black."""
    req_path = project_root / "requirements.txt"
    assert req_path.exists(), "requirements.txt not found"
    content = req_path.read_text().lower()
    assert "black" in content, "black not found in requirements.txt"