"""
Unit tests for linting configuration.

These tests verify that the linting configuration
functions work correctly and return expected values.
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config.linting import (
    get_ruff_config,
    get_black_config,
    validate_linting_setup,
)


class TestLintingConfig:
    """Test cases for linting configuration functions."""

    def test_get_ruff_config_returns_dict(self):
        """Test that get_ruff_config returns a dictionary."""
        config = get_ruff_config()
        assert isinstance(config, dict)
        assert "target-version" in config
        assert "line-length" in config
        assert "select" in config
        assert "ignore" in config
        assert "exclude" in config

    def test_ruff_config_line_length(self):
        """Test that ruff config has correct line length."""
        config = get_ruff_config()
        assert config["line-length"] == 88

    def test_ruff_config_target_version(self):
        """Test that ruff config targets Python 3.11."""
        config = get_ruff_config()
        assert config["target-version"] == "py311"

    def test_get_black_config_returns_dict(self):
        """Test that get_black_config returns a dictionary."""
        config = get_black_config()
        assert isinstance(config, dict)
        assert "line-length" in config
        assert "target-version" in config
        assert "exclude" in config

    def test_black_config_line_length(self):
        """Test that black config has correct line length."""
        config = get_black_config()
        assert config["line-length"] == 88

    def test_black_config_target_version(self):
        """Test that black config targets Python 3.11."""
        config = get_black_config()
        assert "py311" in config["target-version"]

    def test_validate_linting_setup_structure(self):
        """Test that validate_linting_setup returns a tuple."""
        result = validate_linting_setup()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    @patch("config.linting.validate_linting_setup")
    def test_validate_linting_setup_with_mocked_imports(self, mock_validate):
        """Test validate_linting_setup with mocked imports."""
        mock_validate.return_value = (True, "All good")
        is_valid, message = validate_linting_setup()
        assert is_valid is True
        assert message == "All good"
