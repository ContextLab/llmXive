import os
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from code.setup_linting import (
    check_tool,
    create_flake8_config,
    create_black_config,
    init_pre_commit
)

class TestCheckTool:
    def test_check_tool_exists(self, tmp_path):
        """Test that check_tool returns True for existing tools."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="23.12.0")
            result = check_tool("black", "--version")
            assert result is True
            mock_run.assert_called_once()

    def test_check_tool_missing(self, tmp_path):
        """Test that check_tool returns False for missing tools."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("Command not found")
            result = check_tool("nonexistent_tool", "--version")
            assert result is False

class TestCreateFlake8Config:
    def test_create_flake8_config_creates_file(self, tmp_path):
        """Test that create_flake8_config creates .flake8 file."""
        flake8_path = tmp_path / ".flake8"
        create_flake8_config(str(tmp_path))
        assert flake8_path.exists()
        content = flake8_path.read_text()
        assert "[flake8]" in content
        assert "max-line-length" in content

class TestCreateBlackConfig:
    def test_create_black_config_creates_file(self, tmp_path):
        """Test that create_black_config creates pyproject.toml [tool.black] section."""
        pyproject_path = tmp_path / "pyproject.toml"
        create_black_config(str(tmp_path))
        assert pyproject_path.exists()
        content = pyproject_path.read_text()
        assert "[tool.black]" in content
        assert "line-length" in content

class TestInitPreCommit:
    def test_init_pre_commit_creates_config(self, tmp_path):
        """Test that init_pre_commit creates .pre-commit-config.yaml."""
        config_path = tmp_path / ".pre-commit-config.yaml"
        init_pre_commit(str(tmp_path))
        assert config_path.exists()
        content = config_path.read_text()
        assert "repos:" in content
        assert "black" in content
        assert "flake8" in content