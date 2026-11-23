"""
Tests for the setup_linting.py script.
These tests verify that the linting and formatting configuration is correctly set up.
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path so we can import setup_linting
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_linting import update_requirements, create_pyproject_toml

class TestUpdateRequirements:
    def test_adds_missing_packages(self, tmp_path):
        """Test that update_requirements adds missing packages to requirements.txt."""
        # Create a temporary requirements.txt with some content
        requirements_file = tmp_path / "requirements.txt"
        requirements_file.write_text("pandas\nnumpy\n")
        
        # Change to the temp directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            update_requirements()
            
            # Read the updated file
            content = requirements_file.read_text()
            
            # Check that ruff and black were added
            assert "ruff" in content
            assert "black" in content
            
            # Check that original content is preserved
            assert "pandas" in content
            assert "numpy" in content
        finally:
            os.chdir(original_cwd)

    def test_does_not_duplicate_packages(self, tmp_path):
        """Test that update_requirements doesn't add packages that are already present."""
        requirements_file = tmp_path / "requirements.txt"
        requirements_file.write_text("pandas\nnumpy\nruff\nblack\n")
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Count occurrences before
            content_before = requirements_file.read_text()
            ruff_count_before = content_before.count("ruff")
            black_count_before = content_before.count("black")
            
            update_requirements()
            
            # Count occurrences after
            content_after = requirements_file.read_text()
            ruff_count_after = content_after.count("ruff")
            black_count_after = content_after.count("black")
            
            # Counts should be the same
            assert ruff_count_after == ruff_count_before
            assert black_count_after == black_count_before
        finally:
            os.chdir(original_cwd)

class TestCreatePyprojectToml:
    def test_creates_file_with_config(self, tmp_path):
        """Test that create_pyproject_toml creates a file with correct configuration."""
        pyproject_file = tmp_path / "pyproject.toml"
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            create_pyproject_toml()
            
            # Check that file was created
            assert pyproject_file.exists()
            
            content = pyproject_file.read_text()
            
            # Check for key configuration sections
            assert "[tool.black]" in content
            assert "[tool.ruff]" in content
            assert "line-length = 88" in content
            assert "target-version" in content
            
            # Check for black specific settings
            assert "py311" in content
            
            # Check for ruff specific settings
            assert "select" in content
            assert "ignore" in content
        finally:
            os.chdir(original_cwd)

    def test_does_not_overwrite_existing(self, tmp_path):
        """Test that create_pyproject_toml doesn't overwrite existing file."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("# Existing content\n")
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            create_pyproject_toml()
            
            # Check that file still has original content
            content = pyproject_file.read_text()
            assert "# Existing content" in content
        finally:
            os.chdir(original_cwd)

class TestRunCommand:
    def test_successful_command(self, tmp_path):
        """Test that run_command returns True for successful command."""
        from setup_linting import run_command
        
        result = run_command(
            [sys.executable, "-c", "print('hello')"],
            "test command"
        )
        
        assert result is True

    def test_failed_command(self, tmp_path):
        """Test that run_command returns False for failed command."""
        from setup_linting import run_command
        
        result = run_command(
            [sys.executable, "-c", "raise Exception('error')"],
            "test command"
        )
        
        assert result is False