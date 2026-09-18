"""
Test for Task T002: Verify that required directories exist.
This test ensures that 'code', 'artifacts', and 'tests' directories
are present in the project root.
"""
import os
import pytest
from config import get_config

def test_required_directories_exist():
    """
    Verify that the directories required by T002 exist.
    """
    config = get_config()
    project_root = config['project_root']
    
    required_dirs = ['code', 'artifacts', 'tests']
    
    for dir_name in required_dirs:
        full_path = os.path.join(project_root, dir_name)
        assert os.path.exists(full_path), f"Directory missing: {full_path}"
        assert os.path.isdir(full_path), f"Not a directory: {full_path}"

def test_directory_structure_is_clean():
    """
    Verify that the created directories are accessible and writable.
    """
    config = get_config()
    project_root = config['project_root']
    
    required_dirs = ['code', 'artifacts', 'tests']
    
    for dir_name in required_dirs:
        full_path = os.path.join(project_root, dir_name)
        # Check write permissions by attempting to create a temp file
        test_file = os.path.join(full_path, '.write_test_temp')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except PermissionError:
            pytest.fail(f"Cannot write to directory: {full_path}")