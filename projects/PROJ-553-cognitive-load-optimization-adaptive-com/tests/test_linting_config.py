"""
Tests for linting and formatting configuration.

These tests verify that the configuration files are valid and that
the expected commands can be generated correctly.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from code.linting_config import (
    RUFF_CONFIG,
    BLACK_CONFIG,
    get_ruff_command,
    get_black_command,
    get_format_check_command,
    get_lint_check_command,
)


class TestLintingConfig:
    """Test suite for linting configuration."""

    def test_ruff_config_keys(self):
        """Verify that RUFF_CONFIG contains all required keys."""
        required_keys = ["target-version", "line-length", "exclude", "select", "ignore"]
        for key in required_keys:
            assert key in RUFF_CONFIG, f"Missing key: {key}"

    def test_black_config_keys(self):
        """Verify that BLACK_CONFIG contains all required keys."""
        required_keys = ["line-length", "target-version", "include", "exclude"]
        for key in required_keys:
            assert key in BLACK_CONFIG, f"Missing key: {key}"

    def test_line_length_consistency(self):
        """Verify that ruff and black use the same line length."""
        assert RUFF_CONFIG["line-length"] == BLACK_CONFIG["line-length"]

    def test_target_version(self):
        """Verify that both tools target Python 3.11."""
        assert RUFF_CONFIG["target-version"] == "py311"
        assert "py311" in BLACK_CONFIG["target-version"]

    def test_get_ruff_command(self):
        """Verify that get_ruff_command returns a valid command string."""
        cmd = get_ruff_command()
        assert isinstance(cmd, str)
        assert "ruff" in cmd
        assert "check" in cmd
        assert "code/" in cmd
        assert "tests/" in cmd

    def test_get_black_command(self):
        """Verify that get_black_command returns a valid command string."""
        cmd = get_black_command()
        assert isinstance(cmd, str)
        assert "black" in cmd
        assert "code/" in cmd
        assert "tests/" in cmd

    def test_get_format_check_command(self):
        """Verify that get_format_check_command returns a valid check command."""
        cmd = get_format_check_command()
        assert isinstance(cmd, str)
        assert "black" in cmd
        assert "--check" in cmd

    def test_get_lint_check_command(self):
        """Verify that get_lint_check_command returns a valid check command."""
        cmd = get_lint_check_command()
        assert isinstance(cmd, str)
        assert "ruff" in cmd
        assert "check" in cmd
        assert "--fix" not in cmd

    def test_exclude_paths_consistency(self):
        """Verify that both tools exclude common directories."""
        common_excludes = [".git", "__pycache__", "data", "figures"]
        ruff_excludes = RUFF_CONFIG["exclude"]
        black_exclude_str = BLACK_CONFIG["exclude"]
        
        for exclude in common_excludes:
            assert exclude in ruff_excludes
            assert exclude in black_exclude_str

    def test_pyproject_toml_exists(self):
        """Verify that pyproject.toml exists in the project root."""
        project_root = Path(__file__).parent.parent
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml should exist"

    def test_pyproject_toml_contains_ruff_config(self):
        """Verify that pyproject.toml contains ruff configuration."""
        project_root = Path(__file__).parent.parent
        pyproject_path = project_root / "pyproject.toml"
        
        content = pyproject_path.read_text()
        assert "[tool.ruff]" in content, "pyproject.toml should contain [tool.ruff]"
        assert "target-version" in content, "pyproject.toml should specify target version"

    def test_pyproject_toml_contains_black_config(self):
        """Verify that pyproject.toml contains black configuration."""
        project_root = Path(__file__).parent.parent
        pyproject_path = project_root / "pyproject.toml"
        
        content = pyproject_path.read_text()
        assert "[tool.black]" in content, "pyproject.toml should contain [tool.black]"
        assert "line-length" in content, "pyproject.toml should specify line length"

    def test_ruff_toml_exists(self):
        """Verify that .ruff.toml exists in the project root."""
        project_root = Path(__file__).parent.parent
        ruff_toml_path = project_root / ".ruff.toml"
        assert ruff_toml_path.exists(), ".ruff.toml should exist"

    def test_linting_config_syntax_valid(self):
        """Verify that linting_config.py is syntactically valid."""
        project_root = Path(__file__).parent.parent
        config_path = project_root / "code" / "linting_config.py"
        
        try:
            compile(config_path.read_text(), config_path, "exec")
        except SyntaxError as e:
            pytest.fail(f"linting_config.py has a syntax error: {e}")
