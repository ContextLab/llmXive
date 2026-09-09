"""
Unit tests for linting configuration validation.
"""
import os
import sys
import tomllib
import configparser
from pathlib import Path
import pytest

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.setup_linting import (
    validate_ruff_config,
    validate_pyproject_black,
    validate_flake8_config,
    PROJECT_ROOT,
    PYPROJECT_PATH,
    RUFF_CONFIG_PATH,
    FLAKE8_CONFIG_PATH,
)


class TestLintingConfigValidation:
    """Tests for linting configuration validation functions."""

    def test_ruff_config_exists(self):
        """Test that ruff.toml exists after setup."""
        assert RUFF_CONFIG_PATH.exists(), "ruff.toml should exist"

    def test_ruff_config_valid_toml(self):
        """Test that ruff.toml is valid TOML."""
        assert RUFF_CONFIG_PATH.exists()
        with open(RUFF_CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
        assert "lint" in config or "select" in config

    def test_pyproject_black_section(self):
        """Test that pyproject.toml contains [tool.black]."""
        assert PYPROJECT_PATH.exists(), "pyproject.toml should exist"
        with open(PYPROJECT_PATH, "rb") as f:
            config = tomllib.load(f)
        assert "tool" in config
        assert "black" in config["tool"]
        assert config["tool"]["black"]["line-length"] == 88

    def test_flake8_config_exists(self):
        """Test that .flake8 exists after setup."""
        assert FLAKE8_CONFIG_PATH.exists(), ".flake8 should exist"

    def test_flake8_config_valid(self):
        """Test that .flake8 is valid and contains [flake8] section."""
        assert FLAKE8_CONFIG_PATH.exists()
        config = configparser.ConfigParser()
        config.read(FLAKE8_CONFIG_PATH)
        assert "flake8" in config
        assert "max-line-length" in config["flake8"]

    def test_validate_ruff_config_returns_true(self):
        """Test that validate_ruff_config returns True when config is valid."""
        result = validate_ruff_config()
        assert result is True

    def test_validate_pyproject_black_returns_true(self):
        """Test that validate_pyproject_black returns True when config is valid."""
        result = validate_pyproject_black()
        assert result is True

    def test_validate_flake8_config_returns_true(self):
        """Test that validate_flake8_config returns True when config is valid."""
        result = validate_flake8_config()
        assert result is True