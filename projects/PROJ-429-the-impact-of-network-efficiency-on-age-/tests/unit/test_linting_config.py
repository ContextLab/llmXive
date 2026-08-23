"""
Unit tests to verify linting and formatting configuration.
These tests ensure that the project's linting tools are properly configured
and can be executed without errors.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestLintingConfiguration:
    """Tests for linting and formatting tool configuration."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_pyproject_toml_exists(self, project_root):
        """Test that pyproject.toml exists with tool configurations."""
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml must exist"

        content = pyproject.read_text()
        assert "[tool.black]" in content, "Black configuration missing"
        assert "[tool.ruff]" in content, "Ruff configuration missing"

    def test_ruff_config_exists(self, project_root):
        """Test that .ruff.toml exists."""
        ruff_config = project_root / ".ruff.toml"
        assert ruff_config.exists(), ".ruff.toml must exist"

    def test_flake8_config_exists(self, project_root):
        """Test that .flake8 exists."""
        flake8_config = project_root / ".flake8"
        assert flake8_config.exists(), ".flake8 must exist"

        content = flake8_config.read_text()
        assert "max-line-length" in content, "max-line-length must be configured"

    def test_pre_commit_config_exists(self, project_root):
        """Test that .pre-commit-config.yaml exists."""
        pre_commit_config = project_root / ".pre-commit-config.yaml"
        assert pre_commit_config.exists(), ".pre-commit-config.yaml must exist"

        content = pre_commit_config.read_text()
        assert "black" in content, "Black hook must be configured"
        assert "ruff" in content, "Ruff hook must be configured"
        assert "flake8" in content, "flake8 hook must be configured"

    def test_requirements_dev_includes_linters(self, project_root):
        """Test that requirements-dev.txt includes linting tools."""
        req_dev = project_root / "requirements-dev.txt"
        if not req_dev.exists():
            pytest.skip("requirements-dev.txt not found")

        content = req_dev.read_text()
        assert "ruff" in content, "ruff must be in requirements-dev.txt"
        assert "black" in content, "black must be in requirements-dev.txt"
        assert "flake8" in content, "flake8 must be in requirements-dev.txt"

    @pytest.mark.skipif(
        not shutil.which("ruff"), reason="ruff not installed in environment"
    )
    def test_ruff_can_run(self, project_root):
        """Test that ruff can be executed on the code directory."""
        import shutil

        code_dir = project_root / "code"
        if not code_dir.exists():
            pytest.skip("code directory not found")

        result = subprocess.run(
            ["ruff", "check", str(code_dir)],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        # We expect ruff to run without crashing, even if there are linting errors
        assert result.returncode in [
            0,
            1,
        ], f"ruff crashed: {result.stderr}"

    @pytest.mark.skipif(
        not shutil.which("black"), reason="black not installed in environment"
    )
    def test_black_can_run(self, project_root):
        """Test that black can be executed in check mode."""
        import shutil

        code_dir = project_root / "code"
        if not code_dir.exists():
            pytest.skip("code directory not found")

        result = subprocess.run(
            ["black", "--check", "--diff", str(code_dir)],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        # We expect black to run without crashing, even if files need formatting
        assert result.returncode in [
            0,
            1,
        ], f"black crashed: {result.stderr}"

    @pytest.mark.skipif(
        not shutil.which("flake8"), reason="flake8 not installed in environment"
    )
    def test_flake8_can_run(self, project_root):
        """Test that flake8 can be executed on the code directory."""
        import shutil

        code_dir = project_root / "code"
        if not code_dir.exists():
            pytest.skip("code directory not found")

        result = subprocess.run(
            ["flake8", str(code_dir)],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        # We expect flake8 to run without crashing, even if there are linting errors
        assert result.returncode in [
            0,
            1,
        ], f"flake8 crashed: {result.stderr}"