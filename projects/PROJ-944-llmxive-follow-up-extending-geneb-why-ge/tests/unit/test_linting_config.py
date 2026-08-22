"""
Unit tests to verify that the linting and formatting configuration files
are generated correctly and contain expected sections.
"""
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import pytest

# Add the code directory to the path so we can import the config script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from config_linting import write_pyproject_toml, create_install_script

def test_pyproject_toml_creation(tmp_path):
    """Test that pyproject.toml is created with correct sections."""
    # Run the writer
    write_pyproject_toml(tmp_path)
    
    toml_path = tmp_path / "pyproject.toml"
    assert toml_path.exists(), "pyproject.toml was not created"
    
    content = toml_path.read_text()
    assert "[tool.black]" in content, "Missing [tool.black] section"
    assert "[tool.ruff]" in content, "Missing [tool.ruff] section"
    assert "line-length = 88" in content, "Default line length not set"
    assert "target-version = 'py311'" in content or 'target-version = "py311"' in content, "Target version not set"

def test_pyproject_toml_update(tmp_path):
    """Test that existing pyproject.toml is updated without duplication."""
    # Create a dummy existing file
    existing = tmp_path / "pyproject.toml"
    existing.write_text("# Existing config\n[project]\nname = 'test'\n")
    
    write_pyproject_toml(tmp_path)
    
    content = existing.read_text()
    assert "[tool.black]" in content
    assert "[tool.ruff]" in content
    
    # Count occurrences to ensure no duplication
    assert content.count("[tool.black]") == 1
    assert content.count("[tool.ruff]") == 1

def test_install_script_creation(tmp_path):
    """Test that the install script is created and is executable."""
    create_install_script(tmp_path)
    
    script_path = tmp_path / "scripts" / "setup_linting.sh"
    assert script_path.exists(), "Install script was not created"
    assert os.access(script_path, os.X_OK), "Install script is not executable"
    
    content = script_path.read_text()
    assert "pip install black ruff" in content
    assert "black code/ tests/" in content
    assert "ruff check code/ tests/" in content