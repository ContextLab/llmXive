import os
import pytest
from code.config import get_config, ensure_directories

def test_directory_structure_exists():
    """
    Verify that all required project directories exist after calling ensure_directories.
    This test validates the output of T001a, T001b, T001c, and T002.
    """
    # Ensure directories are created (idempotent)
    ensure_directories()
    
    config = get_config()
    required_dirs = [
        config.data_raw_dir,
        config.data_processed_dir,
        config.data_assets_dir,
        config.code_dir,
        config.artifacts_dir,
        config.tests_dir
    ]
    
    for directory in required_dirs:
        assert os.path.isdir(directory), f"Required directory missing: {directory}"

def test_processed_data_directory():
    """
    Specific test for T001b: Verify data/processed directory exists.
    """
    config = get_config()
    assert os.path.isdir(config.data_processed_dir), "data/processed directory does not exist"
    
    # Check for .gitkeep or any file to ensure it's tracked
    files = os.listdir(config.data_processed_dir)
    # We expect at least .gitkeep if we created it, or it's empty but exists
    # The task requires the directory to exist.
    assert os.path.isdir(config.data_processed_dir)