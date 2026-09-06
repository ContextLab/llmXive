"""
Tests to verify linting and formatting configuration compliance.
These tests ensure that the project adheres to the defined style guide.
"""
import subprocess
import sys
import os

import pytest


class TestLintingConfig:
    """Tests for ruff and black configuration."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure we are in the project root."""
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        os.chdir(self.project_root)

    def test_ruff_check_passes(self):
        """Verify that ruff check passes on the codebase."""
        # Run ruff check on the code directory
        result = subprocess.run(
            ["ruff", "check", "code", "tests"],
            capture_output=True,
            text=True,
        )
        # If ruff is not installed, skip (user needs to install dev deps)
        if result.returncode == 127:
            pytest.skip("ruff not installed in environment")
        
        # We expect 0 (success) or specific ignore violations if any
        # For this initial config, we expect success on empty/new code
        assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

    def test_black_check_passes(self):
        """Verify that black check passes on the codebase."""
        result = subprocess.run(
            ["black", "--check", "code", "tests"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 127:
            pytest.skip("black not installed in environment")

        assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists and contains black/ruff config."""
        config_path = os.path.join(self.project_root, "pyproject.toml")
        assert os.path.exists(config_path), "pyproject.toml not found"
        
        with open(config_path, "r") as f:
            content = f.read()
        
        assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
        assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"

    def test_pre_commit_config_exists(self):
        """Verify .pre-commit-config.yaml exists."""
        config_path = os.path.join(self.project_root, ".pre-commit-config.yaml")
        assert os.path.exists(config_path), ".pre-commit-config.yaml not found"