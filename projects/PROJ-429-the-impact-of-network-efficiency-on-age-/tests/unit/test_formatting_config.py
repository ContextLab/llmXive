"""
Unit tests for code formatting configuration.
Verifies that black and isort are properly configured.
"""

import os
from pathlib import Path

import pytest


class TestFormattingConfiguration:
    """Tests for code formatting tool configuration."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_black_line_length_in_pyproject(self, project_root):
        """Test that black line-length is configured in pyproject.toml."""
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()

        # Check for line-length configuration
        assert "line-length = 88" in content or 'line-length=88' in content, (
            "Black line-length must be set to 88"
        )

    def test_black_target_version(self, project_root):
        """Test that black target-version is set to Python 3.11."""
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()

        assert "target-version = ['py311']" in content, (
            "Black target-version must include py311"
        )

    def test_ruff_line_length(self, project_root):
        """Test that ruff line-length is configured."""
        ruff_config = project_root / ".ruff.toml"
        content = ruff_config.read_text()

        assert "line-length = 88" in content, "Ruff line-length must be set to 88"

    def test_isort_profile_black(self, project_root):
        """Test that isort is configured to work with black."""
        pre_commit_config = project_root / ".pre-commit-config.yaml"
        content = pre_commit_config.read_text()

        assert "--profile=black" in content, "isort must use black profile"

    def test_formatting_exclude_data_directory(self, project_root):
        """Test that data directory is excluded from formatting checks."""
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()

        assert "data" in content, "data directory should be in exclude list"

    def test_ruff_ignore_e501(self, project_root):
        """Test that ruff ignores E501 (line too long) as black handles it."""
        ruff_config = project_root / ".ruff.toml"
        content = ruff_config.read_text()

        assert "E501" in content, "Ruff must ignore E501 (handled by black)"

    def test_consistent_line_length_across_tools(self, project_root):
        """Test that all tools use consistent line length (88)."""
        pyproject = project_root / "pyproject.toml"
        ruff_config = project_root / ".ruff.toml"
        flake8_config = project_root / ".flake8"

        pyproject_content = pyproject.read_text()
        ruff_content = ruff_config.read_text()
        flake8_content = flake8_config.read_text()

        # Check pyproject.toml for black
        assert "line-length = 88" in pyproject_content

        # Check .ruff.toml
        assert "line-length = 88" in ruff_content

        # Check .flake8
        assert "max-line-length = 88" in flake8_content