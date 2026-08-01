import os
import pytest
from config import ensure_directories

def test_directories_exist_after_setup(tmp_path):
    """Test that required directories are created by ensure_directories."""
    # Change to temporary directory for testing
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        required_dirs = [
            'data/raw',
            'data/processed',
            'data/assets',
            'code',
            'artifacts',
            'tests',
            'artifacts/logs',
            'artifacts/figures'
        ]
        
        ensure_directories(required_dirs)
        
        # Verify each directory exists
        for dir_path in required_dirs:
            full_path = os.path.join(tmp_path, dir_path)
            assert os.path.isdir(full_path), f"Directory {dir_path} was not created"
    finally:
        os.chdir(original_cwd)

def test_nested_directories_created():
    """Test that nested directories (e.g., artifacts/logs) are created correctly."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        os.chdir(tmp_dir)
        
        try:
            ensure_directories(['artifacts/logs'])
            assert os.path.isdir('artifacts/logs')
            assert os.path.isdir('artifacts')
        finally:
            os.chdir(original_cwd)