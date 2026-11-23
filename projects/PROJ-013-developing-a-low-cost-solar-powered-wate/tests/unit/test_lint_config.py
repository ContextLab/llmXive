"""
Unit tests for linting configuration validation.

These tests verify that the lint configuration is properly set up
and that the validation logic works correctly.
"""

import pytest
import tempfile
import os
from pathlib import Path
import shutil

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from lint_config import get_ruff_config, get_black_config, validate_config


class TestLintConfig:
    """Tests for lint configuration functions."""

    def test_get_ruff_config_exists(self):
        """Test that Ruff configuration can be retrieved."""
        # This test assumes pyproject.toml exists in the project root
        config = get_ruff_config()
        assert isinstance(config, dict)
        assert "select" in config

    def test_get_black_config_exists(self):
        """Test that Black configuration can be retrieved."""
        config = get_black_config()
        assert isinstance(config, dict)
        assert "line-length" in config

    def test_validate_config_success(self):
        """Test that validation passes with correct configuration."""
        # This assumes the actual pyproject.toml is correctly configured
        result = validate_config()
        assert result is True

    def test_validate_config_missing_file(self, tmp_path):
        """Test validation fails when pyproject.toml is missing."""
        # Create a temporary directory without pyproject.toml
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Temporarily modify the module's PROJECT_ROOT
            import lint_config
            original_root = lint_config.PROJECT_ROOT
            lint_config.PROJECT_ROOT = tmp_path
            
            with pytest.raises(ValueError) as exc_info:
                validate_config()
            
            assert "Configuration file missing" in str(exc_info.value)
        finally:
            os.chdir(original_cwd)
            lint_config.PROJECT_ROOT = original_root

    def test_ruff_has_required_rules(self):
        """Test that Ruff configuration includes essential rules."""
        config = get_ruff_config()
        assert "select" in config
        rules = config["select"]
        # Check for at least some essential rule categories
        assert any(rule.startswith(("E", "F", "W")) for rule in rules)

    def test_black_has_line_length(self):
        """Test that Black configuration has line-length set."""
        config = get_black_config()
        assert "line-length" in config
        assert isinstance(config["line-length"], int)
        assert config["line-length"] > 0
        assert config["line-length"] <= 120
