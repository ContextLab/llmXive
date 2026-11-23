import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from setup_directories import create_directories

def test_create_directories_creates_all_needed():
    """
    Test that create_directories creates all required directories.
    This test verifies the side effect of directory creation.
    """
    base_path = Path(__file__).parent.parent
    expected_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs",
        "contracts"
    ]
    
    # Run the function
    result = create_directories()
    
    assert result is True, "create_directories should return True on success"
    
    # Verify each directory exists
    for dir_name in expected_dirs:
        full_path = base_path / dir_name
        assert full_path.exists(), f"Directory {full_path} was not created"
        assert full_path.is_dir(), f"{full_path} exists but is not a directory"
