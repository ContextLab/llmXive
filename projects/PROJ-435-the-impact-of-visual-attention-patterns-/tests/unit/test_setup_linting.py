import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

import pytest

# Add parent to path to import setup_linting
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from setup_linting import create_ruff_config, create_black_config, run_command

def test_run_command_success():
    """Test that run_command executes successfully."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = run_command(["echo", "test"], check=True)
        mock_run.assert_called_once()
        assert result.returncode == 0

def test_create_ruff_config_creates_file():
    """Test that create_ruff_config creates a .ruff.toml file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        config_path = project_root / ".ruff.toml"
        
        assert not config_path.exists()
        create_ruff_config(project_root)
        assert config_path.exists()
        
        content = config_path.read_text()
        assert "[lint]" in content
        assert "select" in content
        assert "E501" in content  # line too long ignored

def test_create_black_config_creates_file():
    """Test that create_black_config creates a pyproject.toml with Black config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        config_path = project_root / "pyproject.toml"
        
        assert not config_path.exists()
        create_black_config(project_root)
        assert config_path.exists()
        
        content = config_path.read_text()
        assert "[tool.black]" in content
        assert "line-length = 88" in content

def test_create_black_config_appends_to_existing():
    """Test that create_black_config appends to existing pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        config_path = project_root / "pyproject.toml"
        
        # Create a file with some content but no black section
        config_path.write_text("[project]\nname = 'test'\n")
        
        create_black_config(project_root)
        
        content = config_path.read_text()
        assert "[project]" in content
        assert "[tool.black]" in content
        assert "name = 'test'" in content

def test_create_black_config_skips_if_exists():
    """Test that create_black_config does not duplicate if section exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        config_path = project_root / "pyproject.toml"
        
        # Create a file with black section
        config_path.write_text("[tool.black]\nline-length = 88\n")
        
        create_black_config(project_root)
        
        content = config_path.read_text()
        # Should only appear once
        assert content.count("[tool.black]") == 1
        assert content.count("line-length = 88") == 1
