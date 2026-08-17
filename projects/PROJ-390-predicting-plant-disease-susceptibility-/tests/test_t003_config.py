"""
Test for T003: Verify linting and formatting configuration files exist.
"""
import os
from pathlib import Path
import pytest

def test_ruff_config_exists():
    """Assert .ruff.toml exists in the project root."""
    project_root = Path(__file__).parent.parent
    config_path = project_root / ".ruff.toml"
    assert config_path.exists(), f"Configuration file {config_path} does not exist."
    assert config_path.stat().st_size > 0, f"Configuration file {config_path} is empty."

def test_black_config_exists():
    """Assert .black.toml exists in the project root."""
    project_root = Path(__file__).parent.parent
    config_path = project_root / ".black.toml"
    assert config_path.exists(), f"Configuration file {config_path} does not exist."
    assert config_path.stat().st_size > 0, f"Configuration file {config_path} is empty."

def test_requirements_includes_linters():
    """Assert requirements.txt includes ruff and black."""
    project_root = Path(__file__).parent.parent
    req_path = project_root / "requirements.txt"
    assert req_path.exists(), "requirements.txt is missing."
    
    content = req_path.read_text().lower()
    assert "ruff" in content, "ruff is not listed in requirements.txt"
    assert "black" in content, "black is not listed in requirements.txt"

def test_config_files_are_valid_toml():
    """Basic syntax check for TOML files using standard library if available, 
    or just checking they are not empty and contain expected keys."""
    project_root = Path(__file__).parent.parent
    
    # Check .ruff.toml
    ruff_path = project_root / ".ruff.toml"
    content = ruff_path.read_text()
    assert "[lint]" in content, "Missing [lint] section in .ruff.toml"
    
    # Check .black.toml
    black_path = project_root / ".black.toml"
    content = black_path.read_text()
    assert "[tool.black]" in content, "Missing [tool.black] section in .black.toml"