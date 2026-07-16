"""
Unit tests for linting and formatting configuration.

These tests verify that the linting configuration files are valid
and that the helper functions work correctly.
"""

import pytest
import os
import tomli

from code.linting_config import (
    get_ruff_command,
    get_ruff_fix_command,
    get_black_command,
    get_black_check_command,
    RUFF_CONFIG,
    BLACK_CONFIG,
)


class TestLintingConfig:
    """Test cases for linting configuration."""

    def test_ruff_command_returns_string(self):
        """Test that get_ruff_command returns a string."""
        result = get_ruff_command()
        assert isinstance(result, str)
        assert "ruff" in result

    def test_ruff_fix_command_returns_string(self):
        """Test that get_ruff_fix_command returns a string."""
        result = get_ruff_fix_command()
        assert isinstance(result, str)
        assert "ruff" in result
        assert "--fix" in result

    def test_black_command_returns_string(self):
        """Test that get_black_command returns a string."""
        result = get_black_command()
        assert isinstance(result, str)
        assert "black" in result

    def test_black_check_command_returns_string(self):
        """Test that get_black_check_command returns a string."""
        result = get_black_check_command()
        assert isinstance(result, str)
        assert "black" in result
        assert "--check" in result

    def test_ruff_config_has_required_keys(self):
        """Test that RUFF_CONFIG has required keys."""
        required_keys = ["target-version", "line-length", "select"]
        for key in required_keys:
            assert key in RUFF_CONFIG

    def test_black_config_has_required_keys(self):
        """Test that BLACK_CONFIG has required keys."""
        required_keys = ["line-length", "target-version"]
        for key in required_keys:
            assert key in BLACK_CONFIG

    def test_ruff_config_excludes_data_directory(self):
        """Test that RUFF_CONFIG excludes the data directory."""
        assert "data" in RUFF_CONFIG.get("exclude", [])

    def test_black_config_excludes_data_directory(self):
        """Test that BLACK_CONFIG excludes the data directory."""
        # Check if exclude pattern contains data
        exclude = BLACK_CONFIG.get("exclude", "")
        assert "data" in exclude

class TestConfigFiles:
    """Test cases for configuration file existence and validity."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    def test_ruff_toml_exists(self, project_root):
        """Test that .ruff.toml exists in the project root."""
        ruff_path = os.path.join(project_root, ".ruff.toml")
        assert os.path.exists(ruff_path)

    def test_pyproject_toml_exists(self, project_root):
        """Test that pyproject.toml exists in the project root."""
        pyproject_path = os.path.join(project_root, "pyproject.toml")
        assert os.path.exists(pyproject_path)

    def test_pyproject_toml_is_valid(self, project_root):
        """Test that pyproject.toml is a valid TOML file."""
        pyproject_path = os.path.join(project_root, "pyproject.toml")
        with open(pyproject_path, "rb") as f:
            try:
                tomli.load(f)
            except Exception as e:
                pytest.fail(f"pyproject.toml is not valid TOML: {e}")

    def test_ruff_toml_is_valid(self, project_root):
        """Test that .ruff.toml is a valid TOML file."""
        ruff_path = os.path.join(project_root, ".ruff.toml")
        with open(ruff_path, "rb") as f:
            try:
                tomli.load(f)
            except Exception as e:
                pytest.fail(f".ruff.toml is not valid TOML: {e}")

    def test_black_in_pyproject(self, project_root):
        """Test that Black configuration exists in pyproject.toml."""
        pyproject_path = os.path.join(project_root, "pyproject.toml")
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
            assert "tool" in config
            assert "black" in config["tool"]

    def test_ruff_in_pyproject(self, project_root):
        """Test that Ruff configuration exists in pyproject.toml."""
        pyproject_path = os.path.join(project_root, "pyproject.toml")
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
            assert "tool" in config
            assert "ruff" in config["tool"]

    def test_pytest_config_exists(self, project_root):
        """Test that pytest configuration exists in pyproject.toml."""
        pyproject_path = os.path.join(project_root, "pyproject.toml")
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
            assert "tool" in config
            assert "pytest" in config["tool"]
            assert "ini_options" in config["tool"]["pytest"]