import subprocess
import sys
from pathlib import Path
import tempfile
import os

def test_check_tool_installed():
    """Test that check_tool returns True for installed tools."""
    from setup_linting import check_tool
    # Black and ruff should be installed if requirements are met
    assert check_tool("python") is True

def test_check_tool_missing():
    """Test that check_tool returns False for missing tools."""
    from setup_linting import check_tool
    assert check_tool("nonexistent_tool_xyz123") is False

def test_pyproject_exists():
    """Test that pyproject.toml exists in the project root."""
    project_root = Path(__file__).parent.parent.parent
    assert (project_root / "pyproject.toml").exists()

def test_black_config_present():
    """Test that [tool.black] section exists in pyproject.toml."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_content = (project_root / "pyproject.toml").read_text()
    assert "[tool.black]" in pyproject_content
    assert "line-length" in pyproject_content

def test_ruff_config_present():
    """Test that [tool.ruff] section exists in pyproject.toml."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_content = (project_root / "pyproject.toml").read_text()
    assert "[tool.ruff]" in pyproject_content
    assert "select" in pyproject_content