"""
Tests for the linting configuration setup script.
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_linting import (
    check_config_files,
    create_flake8_config,
    create_black_config,
    get_project_root
)

class TestLintingSetup:
    """Test cases for linting configuration setup."""

    def test_create_flake8_config(self, tmp_path):
        """Test that .flake8 config file is created correctly."""
        # Create a temporary directory to act as project root
        original_root = get_project_root()
        
        # Mock get_project_root to return our temp directory
        import setup_linting
        original_get_project_root = setup_linting.get_project_root
        setup_linting.get_project_root = lambda: tmp_path
        
        try:
            create_flake8_config(tmp_path)
            
            flake8_path = tmp_path / ".flake8"
            assert flake8_path.exists(), ".flake8 file should be created"
            
            with open(flake8_path, "r") as f:
                content = f.read()
            
            # Check for required configuration
            assert "[flake8]" in content, "Should contain [flake8] section"
            assert "max-line-length = 88" in content, "Should set max-line-length"
            assert "ignore = E501, W503, E203" in content, "Should ignore black-incompatible errors"
            assert "max-complexity = 10" in content, "Should set max-complexity"
        finally:
            # Restore original function
            setup_linting.get_project_root = original_get_project_root

    def test_create_black_config_new_file(self, tmp_path):
        """Test that pyproject.toml is created with black config when it doesn't exist."""
        import setup_linting
        original_get_project_root = setup_linting.get_project_root
        setup_linting.get_project_root = lambda: tmp_path
        
        try:
            create_black_config(tmp_path)
            
            pyproject_path = tmp_path / "pyproject.toml"
            assert pyproject_path.exists(), "pyproject.toml should be created"
            
            with open(pyproject_path, "r") as f:
                content = f.read()
            
            assert "[tool.black]" in content, "Should contain [tool.black] section"
            assert "line-length = 88" in content, "Should set line-length"
            assert "target-version" in content, "Should set target-version"
        finally:
            setup_linting.get_project_root = original_get_project_root

    def test_create_black_config_existing_file(self, tmp_path):
        """Test that black config is appended to existing pyproject.toml."""
        # Create a pyproject.toml without black config
        pyproject_path = tmp_path / "pyproject.toml"
        with open(pyproject_path, "w") as f:
            f.write("[tool.something]\nkey = \"value\"\n")
        
        import setup_linting
        original_get_project_root = setup_linting.get_project_root
        setup_linting.get_project_root = lambda: tmp_path
        
        try:
            create_black_config(tmp_path)
            
            with open(pyproject_path, "r") as f:
                content = f.read()
            
            assert "[tool.black]" in content, "Should append [tool.black] section"
            assert "[tool.something]" in content, "Should preserve existing content"
        finally:
            setup_linting.get_project_root = original_get_project_root

    def test_create_black_config_existing_black_section(self, tmp_path):
        """Test that black config is not duplicated if [tool.black] already exists."""
        # Create a pyproject.toml with existing black config
        pyproject_path = tmp_path / "pyproject.toml"
        with open(pyproject_path, "w") as f:
            f.write("[tool.black]\nline-length = 88\n")
        
        import setup_linting
        original_get_project_root = setup_linting.get_project_root
        setup_linting.get_project_root = lambda: tmp_path
        
        try:
            create_black_config(tmp_path)
            
            with open(pyproject_path, "r") as f:
                content = f.read()
            
            # Count occurrences of [tool.black]
            count = content.count("[tool.black]")
            assert count == 1, "Should not duplicate [tool.black] section"
        finally:
            setup_linting.get_project_root = original_get_project_root

    def test_check_config_files_missing(self, tmp_path):
        """Test check_config_files when files are missing."""
        all_exist, missing = check_config_files(tmp_path)
        assert all_exist is False, "Should report files are missing"
        assert len(missing) == 2, "Should report both files are missing"
        assert str(tmp_path / ".flake8") in missing
        assert str(tmp_path / "pyproject.toml") in missing

    def test_check_config_files_present(self, tmp_path):
        """Test check_config_files when files exist."""
        # Create both config files
        (tmp_path / ".flake8").touch()
        (tmp_path / "pyproject.toml").touch()
        
        all_exist, missing = check_config_files(tmp_path)
        assert all_exist is True, "Should report files exist"
        assert len(missing) == 0, "Should not report any missing files"