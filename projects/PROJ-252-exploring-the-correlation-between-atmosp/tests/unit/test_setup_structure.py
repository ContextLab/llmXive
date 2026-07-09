"""
Unit tests for the project structure setup.
"""
import os
import pytest
from pathlib import Path
import shutil
import tempfile
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.setup_structure import main


class TestSetupStructure:
    """Test cases for setup_structure module."""

    def test_directory_creation(self, tmp_path):
        """Test that all required directories are created."""
        # Create a temporary directory to simulate project root
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run the setup
            result = main()
            
            # Check return code
            assert result == 0, "Setup should return 0 on success"
            
            # Verify directories exist
            required_dirs = [
                "data/raw",
                "data/interim",
                "data/processed",
                "code",
                "tests",
                "docs",
            ]
            
            for dir_path in required_dirs:
                full_path = tmp_path / dir_path
                assert full_path.exists(), f"Directory {dir_path} should exist"
                assert full_path.is_dir(), f"{dir_path} should be a directory"
        
        finally:
            os.chdir(original_cwd)

    def test_idempotency(self, tmp_path):
        """Test that running setup twice doesn't cause errors."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run setup twice
            result1 = main()
            result2 = main()
            
            # Both should succeed
            assert result1 == 0
            assert result2 == 0
            
            # Verify directories still exist
            required_dirs = [
                "data/raw",
                "data/interim",
                "data/processed",
                "code",
                "tests",
                "docs",
            ]
            
            for dir_path in required_dirs:
                full_path = tmp_path / dir_path
                assert full_path.exists()
        
        finally:
            os.chdir(original_cwd)
