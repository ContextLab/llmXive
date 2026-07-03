"""
Unit tests for linting configuration utilities.
"""
import os
import sys
import tempfile
import json

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "code"))

from config.linting_config import (
    RUFF_CONFIG,
    BLACK_CONFIG,
    get_ruff_config_file_content,
    get_black_config_file_content,
    get_ruff_command,
    get_black_command,
    get_black_check_command,
    get_ruff_fix_command,
)


class TestRuffConfig:
    """Tests for Ruff configuration."""

    def test_ruff_target_version(self):
        """Test that target version is correctly set."""
        assert RUFF_CONFIG["target-version"] == "py39"

    def test_ruff_line_length(self):
        """Test that line length is set to 88 (black compatible)."""
        assert RUFF_CONFIG["line-length"] == 88

    def test_ruff_select_rules(self):
        """Test that required linting rules are selected."""
        required_rules = ["E", "W", "F", "I", "B", "C4", "UP"]
        for rule in required_rules:
            assert rule in RUFF_CONFIG["select"]

    def test_ruff_ignore_e501(self):
        """Test that E501 (line too long) is ignored (handled by black)."""
        assert "E501" in RUFF_CONFIG["ignore"]

    def test_ruff_exclude_data_models(self):
        """Test that data and models directories are excluded."""
        assert "data/" in RUFF_CONFIG["exclude"]
        assert "models/" in RUFF_CONFIG["exclude"]

    def test_ruff_config_content_generation(self):
        """Test that config content generation produces valid TOML-like structure."""
        content = get_ruff_config_file_content()
        assert "[tool.ruff]" in content
        assert "target-version" in content
        assert "line-length" in content
        assert "select" in content

class TestBlackConfig:
    """Tests for Black configuration."""

    def test_black_line_length(self):
        """Test that Black line length matches Ruff."""
        assert BLACK_CONFIG["line-length"] == 88

    def test_black_target_versions(self):
        """Test that Black targets correct Python versions."""
        assert "py39" in BLACK_CONFIG["target-version"]
        assert "py310" in BLACK_CONFIG["target-version"]
        assert "py311" in BLACK_CONFIG["target-version"]

    def test_black_exclude_regex(self):
        """Test that Black excludes necessary directories."""
        assert "data/" in BLACK_CONFIG["exclude"]
        assert ".git" in BLACK_CONFIG["exclude"]
        assert "__pycache__" in BLACK_CONFIG["exclude"]

    def test_black_config_content_generation(self):
        """Test that Black config content is generated correctly."""
        content = get_black_config_file_content()
        assert "[tool.black]" in content
        assert "line-length" in content
        assert "target-version" in content

class TestCommandGenerators:
    """Tests for command generation functions."""

    def test_ruff_command(self):
        """Test ruff check command."""
        assert get_ruff_command() == "ruff check ."

    def test_ruff_fix_command(self):
        """Test ruff fix command."""
        assert get_ruff_fix_command() == "ruff check --fix ."

    def test_black_command(self):
        """Test black format command."""
        assert get_black_command() == "black ."

    def test_black_check_command(self):
        """Test black check command."""
        assert get_black_check_command() == "black --check ."

class TestConfigIntegration:
    """Integration tests for configuration consistency."""

    def test_line_length_consistency(self):
        """Test that Ruff and Black use the same line length."""
        assert RUFF_CONFIG["line-length"] == BLACK_CONFIG["line-length"]

    def test_no_conflicting_excludes(self):
        """Test that excluded directories are consistent."""
        ruff_excludes = set(RUFF_CONFIG["exclude"])
        black_excludes = set(BLACK_CONFIG["exclude"])
        
        # Both should exclude data and models
        assert "data/" in ruff_excludes
        assert "data/" in black_excludes
        assert "models/" in ruff_excludes
        assert "models/" in black_excludes
