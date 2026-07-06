"""
Tests for the linting and formatting configuration module.
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from linting_config import (
    FLAKE8_CONFIG,
    BLACK_CONFIG,
    get_flake8_command,
    get_black_command,
    create_config_files,
)


class TestLintingConfig:
    """Test cases for linting configuration."""

    def test_flake8_config_has_required_keys(self):
        """Verify flake8 configuration contains required keys."""
        assert "max_line_length" in FLAKE8_CONFIG
        assert "ignore" in FLAKE8_CONFIG
        assert "extend_exclude" in FLAKE8_CONFIG

    def test_flake8_max_line_length(self):
        """Verify max line length is set to 88."""
        assert FLAKE8_CONFIG["max_line_length"] == 88

    def test_flake8_ignore_conflicts_with_black(self):
        """Verify flake8 ignores settings that conflict with black."""
        ignore = FLAKE8_CONFIG["ignore"]
        assert "E203" in ignore
        assert "W503" in ignore

    def test_black_config_has_required_keys(self):
        """Verify black configuration contains required keys."""
        assert "line_length" in BLACK_CONFIG
        assert "target_version" in BLACK_CONFIG
        assert "exclude" in BLACK_CONFIG

    def test_black_line_length_matches_flake8(self):
        """Verify black line length matches flake8 max line length."""
        assert BLACK_CONFIG["line_length"] == FLAKE8_CONFIG["max_line_length"]

    def test_black_target_version(self):
        """Verify black targets Python 3.11."""
        assert "py311" in BLACK_CONFIG["target_version"]

    def test_get_flake8_command_structure(self):
        """Verify flake8 command structure."""
        cmd = get_flake8_command()
        assert "flake8" in cmd
        assert "--ignore" in cmd
        assert "--max-line-length" in cmd
        assert "code/" in cmd
        assert "tests/" in cmd

    def test_get_black_command_structure(self):
        """Verify black command structure."""
        cmd = get_black_command()
        assert "black" in cmd
        assert "--line-length" in cmd
        assert "code/" in cmd
        assert "tests/" in cmd

    def test_get_black_command_check_mode(self):
        """Verify black command includes check flags in check mode."""
        cmd = get_black_command(check_mode=True)
        assert "--check" in cmd
        assert "--diff" in cmd

    def test_config_excludes_data_and_results(self):
        """Verify configuration excludes data and results directories."""
        assert "data/" in FLAKE8_CONFIG["extend_exclude"]
        assert "results/" in FLAKE8_CONFIG["extend_exclude"]

class TestCreateConfigFiles:
    """Test cases for configuration file creation."""

    def test_create_config_files_runs_without_error(self):
        """Verify create_config_files runs without raising exceptions."""
        # This should not raise any exceptions
        result = create_config_files()
        assert result is True

    def test_config_files_created_or_exist(self):
        """Verify config files exist after creation."""
        create_config_files()

        flake8_path = Path(__file__).parent.parent / ".flake8"
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

        assert flake8_path.exists()
        assert pyproject_path.exists()