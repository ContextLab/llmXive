"""
Unit tests for linting and formatting configuration.
Verifies that .ruff.toml and pyproject.toml (Black) exist and are valid.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

class TestLintingConfig:
    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_ruff_config_exists(self, project_root):
        """Test that .ruff.toml configuration file exists."""
        ruff_config = project_root / ".ruff.toml"
        assert ruff_config.exists(), "Missing .ruff.toml configuration file"

    def test_black_config_exists(self, project_root):
        """Test that pyproject.toml contains Black configuration."""
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "Missing pyproject.toml file"
        
        content = pyproject.read_text()
        assert "[tool.black]" in content, "Missing [tool.black] section in pyproject.toml"

    def test_ruff_syntax_check(self, project_root):
        """Test that ruff can parse the configuration without errors."""
        ruff_config = project_root / ".ruff.toml"
        if ruff_config.exists():
            result = subprocess.run(
                ["ruff", "check", "--config", str(ruff_config), "--select", "E999"],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            # E999 checks for syntax errors in config. Exit code 0 means no errors.
            # We ignore actual linting errors, just checking config validity.
            assert "syntax error" not in result.stderr.lower(), f"Ruff config syntax error: {result.stderr}"

    def test_black_syntax_check(self, project_root):
        """Test that black can parse the configuration without errors."""
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            result = subprocess.run(
                ["black", "--check", "--config", str(pyproject), "--diff", "."],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            # We only care that black didn't crash due to config issues
            assert "configuration error" not in result.stderr.lower(), f"Black config error: {result.stderr}"

    def test_requirements_includes_linting_tools(self, project_root):
        """Test that requirements.txt includes ruff."""
        requirements = project_root / "requirements.txt"
        assert requirements.exists(), "Missing requirements.txt"
        
        content = requirements.read_text()
        assert "ruff" in content.lower(), "Missing ruff in requirements.txt"