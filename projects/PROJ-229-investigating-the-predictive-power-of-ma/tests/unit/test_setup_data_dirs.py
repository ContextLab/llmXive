"""
Unit tests for the data directory setup script (T001a).

Verifies that the required directories are created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Mocking config and logger for isolation if necessary, 
# but here we test the logic by patching get_config or running in a temp dir.
# For simplicity in this unit test, we will test the directory creation logic directly
# by calling the function in a temporary environment.

from code.setup_data_dirs import create_data_directories
from config import get_config

def test_data_directories_creation():
    """
    Test that data/raw, data/processed, data/results, and data/external are created.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Mock the config to point to our temporary directory
        # We need to patch get_config to return our temp path as base_dir
        # Since get_config loads from a file, we might need to temporarily 
        # create a config file or patch the function.
        # A simpler approach for this specific test is to modify the function 
        # to accept a base_path argument, but since we must adhere to the existing API,
        # we will patch the get_config return value.
        
        original_get_config = get_config
        
        def mock_get_config():
            return {"base_dir": str(tmp_path)}
        
        # Patching the import in the module where it's used
        import code.setup_data_dirs as setup_module
        setup_module.get_config = mock_get_config
        
        try:
            # Run the function
            create_data_directories()
            
            # Verify directories exist
            expected_dirs = ["raw", "processed", "results", "external"]
            for dir_name in expected_dirs:
                dir_path = tmp_path / "data" / dir_name
                assert dir_path.exists(), f"Directory {dir_path} was not created."
                assert dir_path.is_dir(), f"{dir_path} is not a directory."
            
        finally:
            # Restore original function
            setup_module.get_config = original_get_config

if __name__ == "__main__":
    pytest.main([__file__, "-v"])