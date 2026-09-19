import os
import pytest
from pathlib import Path

def test_ruff_config_exists():
    """Test that ruff configuration file exists."""
    config_path = Path(__file__).parent.parent.parent / ".ruff.toml"
    assert config_path.exists(), f"Configuration file not found: {config_path}"

def test_black_config_exists():
    """Test that black configuration file exists."""
    config_path = Path(__file__).parent.parent.parent / ".black.toml"
    assert config_path.exists(), f"Configuration file not found: {config_path}"

def test_requirements_includes_linters():
    """Test that requirements.txt includes ruff and black."""
    req_path = Path(__file__).parent.parent.parent / "requirements.txt"
    assert req_path.exists(), "requirements.txt not found"
    
    content = req_path.read_text()
    assert "ruff" in content, "ruff not found in requirements.txt"
    assert "black" in content, "black not found in requirements.txt"
