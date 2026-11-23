import os
import pytest
from pathlib import Path
import sys

# Add the project root to the path so we can import code modules
# Assuming tests are at tests/unit/ and code is at code/
# Project root is parent of tests/
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from setup_directories import main

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory structure simulating the project root."""
    # Create a fake 'code' directory to make the script think it's in the right place
    # We will mock the PROJECT_ROOT in the module for testing
    return tmp_path

def test_setup_directories_creates_folders(temp_project_root):
    """
    Test that setup_directories creates data, state, and docs directories.
    
    We temporarily patch the PROJECT_ROOT in setup_directories to point
    to our temp directory.
    """
    import setup_directories
    
    # Save original
    original_root = setup_directories.PROJECT_ROOT
    
    try:
        # Set to temp path
        setup_directories.PROJECT_ROOT = temp_project_root
        
        # Run main
        result = main()
        
        # Verify directories exist
        for dir_name in ["data", "state", "docs"]:
            target_path = temp_project_root / dir_name
            assert target_path.exists(), f"Directory {target_path} was not created"
            assert target_path.is_dir(), f"{target_path} is not a directory"
        
        # Verify return value contains paths
        assert len(result) == 3
        for path_str in result:
            assert Path(path_str).exists()
            
    finally:
        # Restore original
        setup_directories.PROJECT_ROOT = original_root
