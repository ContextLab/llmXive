import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add code directory to path if running from tests
code_dir = Path(__file__).parent.parent / "code"
if code_dir.exists():
    sys.path.insert(0, str(code_dir))

from setup_linting import (
    check_file_exists,
    validate_pyproject_config,
    validate_flake8_config,
    validate_precommit_config
)

class TestLintingConfigValidation:
    """Tests for linting configuration validation functions."""

    def test_check_file_exists_existing_file(self, tmp_path):
        """Test that check_file_exists returns True for existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        assert check_file_exists(test_file) is True

    def test_check_file_exists_missing_file(self, tmp_path):
        """Test that check_file_exists returns False for missing file."""
        missing_file = tmp_path / "nonexistent.txt"
        
        assert check_file_exists(missing_file) is False

    def test_validate_pyproject_config_with_valid_config(self, tmp_path, monkeypatch):
        """Test validation of a valid pyproject.toml."""
        valid_config = """
        [build-system]
        requires = ["setuptools"]

        [tool.black]
        line-length = 88

        [tool.isort]
        profile = "black"
        """
        
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(valid_config)
        
        # Change to tmp directory
        monkeypatch.chdir(tmp_path)
        
        # This should not raise and should return True
        # Note: In real scenario, we'd need to mock file reading
        # For now, we test the logic exists
        assert validate_pyproject_config() is True

    def test_validate_pyproject_config_missing_black(self, tmp_path, monkeypatch):
        """Test validation fails when black config is missing."""
        invalid_config = """
        [build-system]
        requires = ["setuptools"]

        [tool.isort]
        profile = "black"
        """
        
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(invalid_config)
        
        monkeypatch.chdir(tmp_path)
        
        assert validate_pyproject_config() is False

    def test_validate_flake8_config_with_valid_config(self, tmp_path, monkeypatch):
        """Test validation of a valid .flake8 file."""
        valid_config = """
        [flake8]
        max-line-length = 88
        """
        
        flake8_path = tmp_path / ".flake8"
        flake8_path.write_text(valid_config)
        
        monkeypatch.chdir(tmp_path)
        
        assert validate_flake8_config() is True

    def test_validate_flake8_config_missing_section(self, tmp_path, monkeypatch):
        """Test validation fails when [flake8] section is missing."""
        invalid_config = """
        max-line-length = 88
        """
        
        flake8_path = tmp_path / ".flake8"
        flake8_path.write_text(invalid_config)
        
        monkeypatch.chdir(tmp_path)
        
        assert validate_flake8_config() is False

    def test_validate_precommit_config_with_valid_config(self, tmp_path, monkeypatch):
        """Test validation of a valid .pre-commit-config.yaml."""
        valid_config = """
        repos:
          - repo: https://github.com/psf/black
            rev: v23.0.0
            hooks:
              - id: black
          - repo: https://github.com/pycqa/flake8
            rev: 6.0.0
            hooks:
              - id: flake8
        """
        
        precommit_path = tmp_path / ".pre-commit-config.yaml"
        precommit_path.write_text(valid_config)
        
        monkeypatch.chdir(tmp_path)
        
        assert validate_precommit_config() is True

    def test_validate_precommit_config_missing_hooks(self, tmp_path, monkeypatch):
        """Test validation fails when required hooks are missing."""
        invalid_config = """
        repos:
          - repo: https://github.com/some/other
            rev: v1.0.0
            hooks:
              - id: other
        """
        
        precommit_path = tmp_path / ".pre-commit-config.yaml"
        precommit_path.write_text(invalid_config)
        
        monkeypatch.chdir(tmp_path)
        
        assert validate_precommit_config() is False
