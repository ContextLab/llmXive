"""
Unit tests for linting and formatting tool configuration.
These tests verify that the project is correctly set up with ruff and black.
"""
import os
import subprocess
import pytest
from pathlib import Path


class TestLintingConfiguration:
    """Tests for verifying linting and formatting tool setup."""

    def test_pyproject_toml_exists(self):
        """Verify that pyproject.toml exists in the project root."""
        config_path = Path("pyproject.toml")
        assert config_path.exists(), "pyproject.toml must exist in project root"

    def test_black_configuration_present(self):
        """Verify that [tool.black] section exists in pyproject.toml."""
        config_path = Path("pyproject.toml")
        content = config_path.read_text()
        assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"

    def test_ruff_configuration_present(self):
        """Verify that [tool.ruff] section exists in pyproject.toml."""
        config_path = Path("pyproject.toml")
        content = config_path.read_text()
        assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"

    def test_black_line_length_configured(self):
        """Verify that line-length is configured for black."""
        config_path = Path("pyproject.toml")
        content = config_path.read_text()
        assert "line-length" in content, "line-length must be configured in pyproject.toml"

    def test_ruff_rule_selection_present(self):
        """Verify that ruff has rule selection configured."""
        config_path = Path("pyproject.toml")
        content = config_path.read_text()
        assert "select" in content, "ruff must have 'select' configuration for rules"

    def test_pre_commit_config_exists(self):
        """Verify that .pre-commit-config.yaml exists."""
        pre_commit_path = Path(".pre-commit-config.yaml")
        assert pre_commit_path.exists(), ".pre-commit-config.yaml must exist"

    def test_pre_commit_contains_black(self):
        """Verify that pre-commit config includes black hook."""
        pre_commit_path = Path(".pre-commit-config.yaml")
        content = pre_commit_path.read_text()
        assert "black" in content, "pre-commit config must include black hook"

    def test_pre_commit_contains_ruff(self):
        """Verify that pre-commit config includes ruff hook."""
        pre_commit_path = Path(".pre-commit-config.yaml")
        content = pre_commit_path.read_text()
        assert "ruff" in content or "astral-sh/ruff" in content, "pre-commit config must include ruff hook"

    def test_black_check_command_available(self):
        """Verify that black --check command runs without import errors."""
        result = subprocess.run(
            ["black", "--check", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, "black --check --help should succeed"

    def test_ruff_check_command_available(self):
        """Verify that ruff check command runs without import errors."""
        result = subprocess.run(
            ["ruff", "check", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, "ruff check --help should succeed"

    def test_setup_linting_script_exists(self):
        """Verify that the setup_linting.py script exists in code/."""
        script_path = Path("code/setup_linting.py")
        assert script_path.exists(), "code/setup_linting.py must exist"

    def test_setup_linting_script_is_valid_python(self):
        """Verify that setup_linting.py is valid Python syntax."""
        script_path = Path("code/setup_linting.py")
        with open(script_path, "r") as f:
            source = f.read()
        # This will raise SyntaxError if the file is invalid
        compile(source, str(script_path), "exec")