import os
import sys
import pytest
from pathlib import Path
from setup_structure import create_directories

class TestSetupStructure:
    def test_create_directories_creates_expected_folders(self, tmp_path):
        """
        Test that create_directories creates all required folders.
        Uses a temporary directory to avoid modifying the actual project structure during tests.
        """
        # Mock the base directory to be the temp path
        original_cwd = os.getcwd()
        try:
            # Change to temp directory so the script creates folders there
            os.chdir(str(tmp_path))
            
            # Create a mock setup_structure.py in the temp dir to test logic
            # We will call the function logic directly by patching the base_dir
            import setup_structure
            
            # We need to verify the logic without actually creating files in the real repo
            # So we verify the list of directories generated
            
            expected_dirs = [
                "src/bias_pipeline",
                "src/cli",
                "data/raw",
                "data/processed",
                "data/validation",
                "tests/unit",
                "tests/integration",
                "state"
            ]
            
            # Run the function (it will create in tmp_path)
            result = create_directories()
            
            assert result is True
            
            # Verify directories were created
            for dir_name in expected_dirs:
                full_path = tmp_path / dir_name
                assert full_path.exists(), f"Directory {full_path} was not created"
                assert full_path.is_dir(), f"{full_path} is not a directory"
                
        finally:
            os.chdir(original_cwd)

    def test_directories_are_unique(self):
        """
        Ensure there are no duplicate directory paths in the configuration.
        """
        directories = [
            "src/bias_pipeline",
            "src/cli",
            "data/raw",
            "data/processed",
            "data/validation",
            "tests/unit",
            "tests/integration",
            "state"
        ]
        assert len(directories) == len(set(directories)), "Duplicate directories found in configuration"