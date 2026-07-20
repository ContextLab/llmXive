import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from code.setup_linting import (
    check_tool,
    install_dev_dependencies,
    create_flake8_config,
    create_black_config,
    init_pre_commit
)

class TestCheckTool:
    def test_check_tool_installed(self):
        """Test checking for an installed tool."""
        with patch('code.setup_linting.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="4.0.1", returncode=0)
            result = check_tool("flake8")
            assert result is True
            mock_run.assert_called_once_with(
                ["flake8", "--version"],
                capture_output=True,
                text=True,
                check=True
            )

    def test_check_tool_not_installed(self):
        """Test checking for a non-installed tool."""
        with patch('code.setup_linting.subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("Command not found")
            result = check_tool("nonexistent_tool")
            assert result is False

class TestCreateFlake8Config:
    def test_create_flake8_config_new(self, tmp_path):
        """Test creating a new .flake8 config file."""
        config_path = tmp_path / ".flake8"
        create_flake8_config(tmp_path)
        assert config_path.exists()
        content = config_path.read_text()
        assert "[flake8]" in content
        assert "max-line-length = 88" in content

    def test_create_flake8_config_exists(self, tmp_path):
        """Test that existing .flake8 config is not overwritten."""
        config_path = tmp_path / ".flake8"
        config_path.write_text("existing content")
        create_flake8_config(tmp_path)
        assert config_path.read_text() == "existing content"

class TestCreateBlackConfig:
    def test_create_black_config_new(self, tmp_path):
        """Test creating pyproject.toml with Black config."""
        toml_path = tmp_path / "pyproject.toml"
        create_black_config(tmp_path)
        assert toml_path.exists()
        content = toml_path.read_text()
        assert "[tool.black]" in content
        assert "line-length = 88" in content

    def test_create_black_config_exists_no_section(self, tmp_path):
        """Test adding Black config to existing pyproject.toml without [tool.black]."""
        toml_path = tmp_path / "pyproject.toml"
        toml_path.write_text("[project]\nname = \"test\"")
        create_black_config(tmp_path)
        content = toml_path.read_text()
        assert "[tool.black]" in content
        assert "[project]" in content

    def test_create_black_config_exists_with_section(self, tmp_path):
        """Test that existing [tool.black] section is not duplicated."""
        toml_path = tmp_path / "pyproject.toml"
        toml_path.write_text("[tool.black]\nline-length = 88")
        create_black_config(tmp_path)
        content = toml_path.read_text()
        assert content.count("[tool.black]") == 1

class TestInitPreCommit:
    def test_init_pre_commit_new(self, tmp_path):
        """Test creating a new .pre-commit-config.yaml."""
        config_path = tmp_path / ".pre-commit-config.yaml"
        init_pre_commit(tmp_path)
        assert config_path.exists()
        content = config_path.read_text()
        assert "repo: https://github.com/psf/black" in content
        assert "repo: https://github.com/pycqa/flake8" in content

    def test_init_pre_commit_exists(self, tmp_path):
        """Test that existing .pre-commit-config.yaml is not overwritten."""
        config_path = tmp_path / ".pre-commit-config.yaml"
        config_path.write_text("existing content")
        init_pre_commit(tmp_path)
        assert config_path.read_text() == "existing content"

    def test_init_pre_commit_no_git(self, tmp_path):
        """Test pre-commit initialization when .git does not exist."""
        with patch('code.setup_linting.subprocess.run') as mock_run:
            init_pre_commit(tmp_path)
            # pre-commit install should not be called if .git doesn't exist
            mock_run.assert_not_called()

    def test_init_pre_commit_with_git(self, tmp_path):
        """Test pre-commit initialization when .git exists."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        with patch('code.setup_linting.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            init_pre_commit(tmp_path)
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args == ["pre-commit", "install"]
            assert mock_run.call_args[1]['cwd'] == tmp_path