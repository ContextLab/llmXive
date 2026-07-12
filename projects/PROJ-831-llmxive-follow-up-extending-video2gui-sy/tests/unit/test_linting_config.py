"""
Unit tests for linting configuration generation.

Tests that the linting configuration files are generated correctly
and contain the expected settings.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config.linting import (
    create_ruff_config,
    create_black_config,
    create_precommit_config,
    get_project_root
)


class TestRuffConfig:
    """Tests for Ruff configuration generation."""

    def test_ruff_config_contains_select_rules(self):
        """Test that ruff config includes required rule sets."""
        config = create_ruff_config()
        
        required_rules = ["E", "W", "F", "I", "B", "C4", "UP", "RUF"]
        for rule in required_rules:
            assert f'"{rule}"' in config or f"'{rule}'" in config, \
                f"Rule {rule} should be in select list"

    def test_ruff_config_excludes_e501(self):
        """Test that E501 (line too long) is ignored (handled by Black)."""
        config = create_ruff_config()
        assert '"E501"' in config or "'E501'" in config

    def test_ruff_config_has_correct_line_length(self):
        """Test that line length is set to 88."""
        config = create_ruff_config()
        assert "line-length = 88" in config

    def test_ruff_config_excludes_standard_directories(self):
        """Test that standard directories are excluded."""
        config = create_ruff_config()
        excluded_dirs = [".git", ".tox", "venv", "__pycache__"]
        for directory in excluded_dirs:
            assert f'"{directory}"' in config or f"'{directory}'" in config


class TestBlackConfig:
    """Tests for Black configuration generation."""

    def test_black_config_line_length(self):
        """Test that Black line length is 88."""
        config = create_black_config()
        assert "line-length = 88" in config

    def test_black_config_target_version(self):
        """Test that target version is py311."""
        config = create_black_config()
        assert "py311" in config

    def test_black_config_quote_style(self):
        """Test that quote style is double quotes."""
        config = create_black_config()
        # Note: Black config is in pyproject.toml format, not TOML section here
        # The function returns the section content
        assert "quote-style" not in config  # Black uses pyproject.toml, not separate file
        # But our config includes it for completeness
        assert 'quote-style = "double"' in config


class TestPrecommitConfig:
    """Tests for pre-commit configuration generation."""

    def test_precommit_includes_ruff(self):
        """Test that pre-commit config includes Ruff."""
        config = create_precommit_config()
        assert "ruff" in config.lower()

    def test_precommit_includes_black(self):
        """Test that pre-commit config includes Black."""
        config = create_precommit_config()
        assert "black" in config.lower()

    def test_precommit_includes_standard_hooks(self):
        """Test that standard pre-commit hooks are included."""
        config = create_precommit_config()
        standard_hooks = [
            "trailing-whitespace",
            "end-of-file-fixer",
            "check-yaml",
            "detect-private-key"
        ]
        for hook in standard_hooks:
            assert hook in config, f"Hook {hook} should be in pre-commit config"


class TestProjectRoot:
    """Tests for project root detection."""

    def test_get_project_root_returns_path(self):
        """Test that get_project_root returns a Path object."""
        root = get_project_root()
        assert isinstance(root, Path)

    def test_get_project_root_exists(self):
        """Test that the returned path exists."""
        root = get_project_root()
        assert root.exists()

    def test_get_project_root_is_parent_of_code(self):
        """Test that project root is the parent of the code directory."""
        root = get_project_root()
        code_dir = root / "code"
        assert code_dir.exists()
        assert root == code_dir.parent