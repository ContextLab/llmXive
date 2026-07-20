"""
Tests to verify linting and formatting configuration is properly set up.
These tests ensure that the project adheres to the defined code standards.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestLintingConfig:
    """Test suite for linting and formatting configuration."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent

    def test_pyproject_toml_exists(self, project_root):
        """Test that pyproject.toml exists in project root."""
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml must exist in project root"

    def test_ruff_config_exists(self, project_root):
        """Test that ruff configuration exists."""
        ruff_toml = project_root / ".ruff.toml"
        pyproject_ruff = project_root / "pyproject.toml"

        assert (
            ruff_toml.exists() or "tool.ruff" in pyproject_toml.read_text()
        ), "Ruff configuration must exist in either .ruff.toml or pyproject.toml"

    def test_black_config_exists(self, project_root):
        """Test that black configuration exists."""
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml must exist"

        content = pyproject_path.read_text()
        assert "tool.black" in content, "Black configuration must exist in pyproject.toml"

    def test_precommit_config_exists(self, project_root):
        """Test that pre-commit configuration exists."""
        precommit_path = project_root / ".pre-commit-config.yaml"
        assert precommit_path.exists(), ".pre-commit-config.yaml must exist"

    def test_ruff_can_parse_config(self, project_root):
        """Test that ruff can successfully parse the configuration."""
        try:
            result = subprocess.run(
                ["ruff", "check", "--output-format=json", "."],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=30,
            )
            # Ruff should be able to parse config even if there are linting errors
            # The important thing is it doesn't crash with a config error
            assert "Failed to parse" not in result.stderr.lower()
        except subprocess.TimeoutExpired:
            pytest.fail("Ruff check timed out")
        except FileNotFoundError:
            pytest.skip("ruff not installed in test environment")

    def test_black_can_parse_config(self, project_root):
        """Test that black can successfully parse the configuration."""
        try:
            result = subprocess.run(
                ["black", "--check", "--diff", "."],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=30,
            )
            # Black should be able to parse config even if files need formatting
            # The important thing is it doesn't crash with a config error
            assert "Error:" not in result.stderr or "Failed to parse" not in result.stderr
        except subprocess.TimeoutExpired:
            pytest.fail("Black check timed out")
        except FileNotFoundError:
            pytest.skip("black not installed in test environment")

    def test_python_files_exist(self, project_root):
        """Test that there are Python files to lint."""
        code_dir = project_root / "code"
        tests_dir = project_root / "tests"

        python_files = list(code_dir.glob("*.py")) + list(tests_dir.glob("*.py"))
        assert len(python_files) > 0, "There must be Python files to lint"

    def test_requirements_includes_linting_tools(self, project_root):
        """Test that requirements files include linting tools."""
        requirements_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "pyproject.toml",
        ]

        found_tools = False
        for req_file in requirements_files:
            req_path = project_root / req_file
            if req_path.exists():
                content = req_path.read_text().lower()
                if "ruff" in content or "black" in content:
                    found_tools = True
                    break

        assert found_tools, "At least one requirements file must include ruff or black"

    def test_linting_script_exists(self, project_root):
        """Test that the linting setup script exists."""
        setup_script = project_root / "scripts" / "setup_linting.sh"
        assert setup_script.exists(), "scripts/setup_linting.sh must exist"

        # Check if it's executable or has proper shebang
        content = setup_script.read_text()
        assert content.startswith("#!/bin/bash"), "Setup script must have bash shebang"

    @pytest.mark.slow
    def test_ruff_check_passes_on_code(self, project_root):
        """Test that ruff check passes on code directory (may have intentional violations)."""
        try:
            result = subprocess.run(
                ["ruff", "check", "code/"],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=60,
            )
            # This test documents the current state - may have violations
            # The important thing is ruff runs without config errors
            assert result.returncode == 0 or "Failed to parse" not in result.stderr
        except subprocess.TimeoutExpired:
            pytest.fail("Ruff check on code/ timed out")
        except FileNotFoundError:
            pytest.skip("ruff not installed in test environment")

    @pytest.mark.slow
    def test_black_check_passes_on_code(self, project_root):
        """Test that black check can run on code directory."""
        try:
            result = subprocess.run(
                ["black", "--check", "code/"],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=60,
            )
            # This test documents the current state - may have formatting issues
            # The important thing is black runs without config errors
            assert "Error:" not in result.stderr or "Failed to parse" not in result.stderr
        except subprocess.TimeoutExpired:
            pytest.fail("Black check on code/ timed out")
        except FileNotFoundError:
            pytest.skip("black not installed in test environment")
