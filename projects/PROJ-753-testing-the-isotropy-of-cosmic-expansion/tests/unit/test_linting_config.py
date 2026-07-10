"""
Unit tests for linting configuration.

These tests verify that the linting configuration module works correctly
and that the configuration values are valid.
"""

import pytest
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.linting_config import (
    RUFF_CONFIG,
    BLACK_CONFIG,
    get_ruff_command,
    get_black_command,
    get_ruff_format_command,
)

class TestRuffConfig:
    """Tests for ruff configuration."""

    def test_ruff_target_version(self):
        """Verify ruff target version is Python 3.11."""
        assert RUFF_CONFIG["target_version"] == "py311"

    def test_ruff_line_length(self):
        """Verify ruff line length matches black."""
        assert RUFF_CONFIG["line_length"] == 88

    def test_ruff_select_rules(self):
        """Verify ruff selects essential linting rules."""
        required_rules = {"E", "W", "F", "I", "B", "C4", "UP"}
        selected_rules = set(RUFF_CONFIG["select"])
        assert required_rules.issubset(selected_rules)

    def test_ruff_excludes_data(self):
        """Verify ruff excludes data directory."""
        assert "data" in RUFF_CONFIG["exclude"]

class TestBlackConfig:
    """Tests for black configuration."""

    def test_black_line_length(self):
        """Verify black line length is 88."""
        assert BLACK_CONFIG["line_length"] == 88

    def test_black_target_version(self):
        """Verify black targets Python 3.11."""
        assert "py311" in BLACK_CONFIG["target_version"]

    def test_black_string_normalization(self):
        """Verify string normalization is enabled."""
        assert BLACK_CONFIG["skip_string_normalization"] is False

class TestCommandGenerators:
    """Tests for command generation functions."""

    def test_ruff_command_structure(self):
        """Verify ruff command includes correct paths."""
        cmd = get_ruff_command()
        assert "ruff" in cmd
        assert "code/" in cmd
        assert "tests/" in cmd

    def test_black_command_structure(self):
        """Verify black command includes correct paths."""
        cmd = get_black_command()
        assert "black" in cmd
        assert "code/" in cmd
        assert "tests/" in cmd

    def test_ruff_format_command(self):
        """Verify ruff format command is correct."""
        cmd = get_ruff_format_command()
        assert "ruff" in cmd
        assert "format" in cmd
        assert "code/" in cmd

class TestConfigurationFiles:
    """Tests for configuration file existence."""

    def test_ruff_toml_exists(self):
        """Verify .ruff.toml exists in project root."""
        ruff_path = os.path.join(
            os.path.dirname(__file__), "..", "..", ".ruff.toml"
        )
        assert os.path.exists(ruff_path), ".ruff.toml not found"

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists in project root."""
        pyproject_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "pyproject.toml"
        )
        assert os.path.exists(pyproject_path), "pyproject.toml not found"

    def test_pyproject_has_black_section(self):
        """Verify pyproject.toml contains black configuration."""
        pyproject_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "pyproject.toml"
        )
        with open(pyproject_path, "r") as f:
            content = f.read()
        assert "[tool.black]" in content, "Black section missing in pyproject.toml"

    def test_pyproject_has_ruff_section(self):
        """Verify pyproject.toml contains ruff configuration."""
        pyproject_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "pyproject.toml"
        )
        with open(pyproject_path, "r") as f:
            content = f.read()
        assert "[tool.ruff]" in content, "Ruff section missing in pyproject.toml"

    def test_pyproject_has_dev_dependencies(self):
        """Verify pyproject.toml includes dev dependencies."""
        pyproject_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "pyproject.toml"
        )
        with open(pyproject_path, "r") as f:
            content = f.read()
        assert "ruff" in content, "ruff not in dependencies"
        assert "black" in content, "black not in dependencies"
        assert "pytest" in content, "pytest not in dependencies"
