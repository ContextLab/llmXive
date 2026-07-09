"""
Unit tests for the linting setup functionality.
"""
import os
import tempfile
import pytest
from code.setup_linting import create_flake8_config, create_black_config

class TestLintingSetup:
    def test_flake8_config_creation(self, tmp_path):
        """Test that flake8 configuration is created correctly."""
        # Change to temp directory
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            create_flake8_config()
            
            # Check file exists
            assert os.path.exists(".flake8")
            
            # Check content
            with open(".flake8", "r") as f:
                content = f.read()
            
            assert "[flake8]" in content
            assert "max-line-length = 88" in content
            assert "E203" in content
        finally:
            os.chdir(original_dir)

    def test_black_config_creation(self, tmp_path):
        """Test that black configuration is created correctly."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            create_black_config()
            
            # Check file exists (pyproject.toml)
            assert os.path.exists("pyproject.toml")
            
            # Check content
            with open("pyproject.toml", "r") as f:
                content = f.read()
            
            assert "[tool.black]" in content
            assert "line-length = 88" in content
            assert "py310" in content
        finally:
            os.chdir(original_dir)

    def test_black_config_creation_existing_file(self, tmp_path):
        """Test that black configuration appends to existing pyproject.toml."""
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Create existing pyproject.toml
            with open("pyproject.toml", "w") as f:
                f.write("[project]\nname = 'test'\n")
            
            create_black_config()
            
            # Check file exists
            assert os.path.exists("pyproject.toml")
            
            # Check both sections exist
            with open("pyproject.toml", "r") as f:
                content = f.read()
            
            assert "[project]" in content
            assert "[tool.black]" in content
        finally:
            os.chdir(original_dir)