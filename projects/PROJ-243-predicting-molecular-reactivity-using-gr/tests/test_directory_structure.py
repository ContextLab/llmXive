import os
import pytest

def test_required_directories_exist():
    """
    Verify that all required project directories exist.
    
    This test checks for the presence of:
    - data/raw
    - data/processed
    - data/assets
    - code
    - artifacts
    - tests
    """
    required_dirs = [
        'data/raw',
        'data/processed',
        'data/assets',
        'code',
        'artifacts',
        'tests'
    ]
    
    for dir_path in required_dirs:
        assert os.path.isdir(dir_path), f"Required directory missing: {dir_path}"

def test_data_processed_directory_exists():
    """
    Specific test for the T001b task: verify data/processed directory exists.
    """
    assert os.path.isdir('data/processed'), "data/processed directory must exist for T001b"