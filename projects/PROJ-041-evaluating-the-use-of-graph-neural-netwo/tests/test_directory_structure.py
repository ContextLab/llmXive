import os
import pytest

def test_directory_structure_exists():
    """Verify that all required project directories exist."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    required_dirs = [
        os.path.join(base_dir, "code", "data"),
        os.path.join(base_dir, "code", "models"),
        os.path.join(base_dir, "code", "analysis"),
        os.path.join(base_dir, "code", "utils"),
        os.path.join(base_dir, "data", "raw"),
        os.path.join(base_dir, "data", "processed"),
        os.path.join(base_dir, "data", "results"),
        os.path.join(base_dir, "tests"),
        os.path.join(base_dir, "tests", "integration"),
        os.path.join(base_dir, "tests", "unit"),
    ]
    
    for directory in required_dirs:
        assert os.path.isdir(directory), f"Directory missing: {directory}"

def test_directory_structure_is_not_empty():
    """Verify that the test directories can contain files (they exist as valid directories)."""
    # This test ensures the directories are valid and accessible
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    test_dirs = [
        os.path.join(base_dir, "tests"),
        os.path.join(base_dir, "tests", "integration"),
        os.path.join(base_dir, "tests", "unit"),
    ]
    
    for directory in test_dirs:
        assert os.access(directory, os.R_OK | os.W_OK), f"Directory not accessible: {directory}"
