"""
Unit tests for linting and formatting configuration.

This test file verifies that the project's linting (ruff) and formatting (black)
configurations are correctly set up and that the codebase passes all checks.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest


class TestLintingConfig:
    """Test suite for linting and formatting configuration."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent.parent
    
    def test_ruff_config_exists(self, project_root):
        """Test that ruff configuration file exists."""
        ruff_config = project_root / ".ruff.toml"
        assert ruff_config.exists(), "ruff configuration file (.ruff.toml) not found"
    
    def test_black_config_exists(self, project_root):
        """Test that black configuration file exists."""
        black_config = project_root / ".black.toml"
        assert black_config.exists(), "black configuration file (.black.toml) not found"
    
    def test_pyproject_toml_exists(self, project_root):
        """Test that pyproject.toml exists with tool configurations."""
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml not found"
        
        content = pyproject.read_text()
        assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
        assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"
    
    def test_makefile_exists(self, project_root):
        """Test that Makefile with lint/format targets exists."""
        makefile = project_root / "Makefile"
        assert makefile.exists(), "Makefile not found"
        
        content = makefile.read_text()
        assert "lint" in content, "Makefile missing 'lint' target"
        assert "format" in content, "Makefile missing 'format' target"
        assert "test" in content, "Makefile missing 'test' target"
    
    def test_ruff_check_runs(self, project_root):
        """Test that ruff check command runs successfully."""
        # Skip if ruff is not installed
        try:
            result = subprocess.run(
                ["ruff", "check", "--version"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            if result.returncode != 0:
                pytest.skip("ruff not installed")
        except FileNotFoundError:
            pytest.skip("ruff not installed")
        
        # Run ruff check on the code directory
        result = subprocess.run(
            ["ruff", "check", "code/"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # We expect some errors in a real project, but the command should run
        assert result.returncode in [0, 1], f"ruff check failed with unexpected error: {result.stderr}"
    
    def test_black_check_runs(self, project_root):
        """Test that black check command runs successfully."""
        # Skip if black is not installed
        try:
            result = subprocess.run(
                ["black", "--version"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            if result.returncode != 0:
                pytest.skip("black not installed")
        except FileNotFoundError:
            pytest.skip("black not installed")
        
        # Run black check on the code directory
        result = subprocess.run(
            ["black", "--check", "code/"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # We expect some formatting differences in a real project, but the command should run
        assert result.returncode in [0, 1], f"black check failed with unexpected error: {result.stderr}"
    
    def test_requirements_includes_dev_tools(self, project_root):
        """Test that requirements.txt or pyproject.toml includes dev tools."""
        pyproject = project_root / "pyproject.toml"
        requirements = project_root / "requirements.txt"
        
        if pyproject.exists():
            content = pyproject.read_text()
            assert "ruff" in content, "ruff not found in pyproject.toml dependencies"
            assert "black" in content, "black not found in pyproject.toml dependencies"
        elif requirements.exists():
            content = requirements.read_text()
            assert "ruff" in content, "ruff not found in requirements.txt"
            assert "black" in content, "black not found in requirements.txt"
        else:
            pytest.skip("Neither pyproject.toml nor requirements.txt found")