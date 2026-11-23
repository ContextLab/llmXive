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
    def test_check_tool_installed(self, caplog):
        with patch("code.setup_linting.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="black, 23.1.0\n",
                stderr=""
            )
            result = check_tool("black")
            assert result is True
            mock_run.assert_called_once_with(
                ["black", "--version"],
                capture_output=True,
                text=True,
                check=True
            )

    def test_check_tool_not_installed(self, caplog):
        with patch("code.setup_linting.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("Command not found")
            result = check_tool("nonexistent_tool")
            assert result is False

    def test_check_tool_called_process_error(self, caplog):
        with patch("code.setup_linting.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
            result = check_tool("flake8")
            assert result is False

class TestCreateFlake8Config:
    def test_create_flake8_config(self, tmp_path):
        create_flake8_config(tmp_path)
        config_file = tmp_path / ".flake8"
        assert config_file.exists()
        content = config_file.read_text()
        assert "[flake8]" in content
        assert "max-line-length = 88" in content

class TestCreateBlackConfig:
    def test_create_black_config_new_file(self, tmp_path):
        create_black_config(tmp_path)
        config_file = tmp_path / "pyproject.toml"
        assert config_file.exists()
        content = config_file.read_text()
        assert "[tool.black]" in content
        assert "line-length = 88" in content

    def test_create_black_config_append(self, tmp_path):
        existing_content = "[some.other]\nkey = value\n"
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(existing_content)
        
        create_black_config(tmp_path)
        content = config_file.read_text()
        assert "[some.other]" in content
        assert "[tool.black]" in content

    def test_create_black_config_skip_existing(self, tmp_path):
        existing_content = "[tool.black]\nline-length = 88\n"
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(existing_content)
        
        create_black_config(tmp_path)
        # Should not duplicate the section
        assert content.count("[tool.black]") == 1

class TestInitPreCommit:
    def test_init_pre_commit(self, tmp_path):
        init_pre_commit(tmp_path)
        config_file = tmp_path / ".pre-commit-config.yaml"
        assert config_file.exists()
        content = config_file.read_text()
        assert "repos:" in content
        assert "black" in content
        assert "flake8" in content