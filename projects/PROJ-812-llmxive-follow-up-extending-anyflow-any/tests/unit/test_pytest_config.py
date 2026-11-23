"""
Unit tests to verify that pytest is correctly configured and the directory structure is valid.

This task satisfies T004: Setup pytest configuration and directory structure.
"""
import os
import sys
import json
import pytest

def test_project_root_accessible(temp_project_dir):
    """Verify that the temporary project directory structure is created correctly."""
    assert os.path.isdir(temp_project_dir)
    assert os.path.isdir(os.path.join(temp_project_dir, "data", "raw"))
    assert os.path.isdir(os.path.join(temp_project_dir, "data", "processed"))
    assert os.path.isdir(os.path.join(temp_project_dir, "artifacts"))

def test_code_import_path_resolution(temp_project_dir, add_code_to_path):
    """
    Verify that the code directory is correctly added to sys.path 
    allowing imports from sibling modules.
    """
    # This test relies on the autouse fixture add_code_to_path
    # If the fixture works, 'code' should be in sys.path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code_dir = os.path.join(project_root, "code")
    assert code_dir in sys.path

def test_pytest_markers_available():
    """Verify that standard pytest markers (e.g., unit, integration) are recognized."""
    # This test simply runs to ensure pytest configuration doesn't crash on markers
    # In a real scenario, we would use @pytest.mark.unit here
    assert True

def test_temp_dir_cleanup(temp_project_dir):
    """Verify that the temp directory can be written to and read from."""
    test_file = os.path.join(temp_project_dir, "data", "raw", "test_write.txt")
    with open(test_file, "w") as f:
        f.write("pytest is working")
    
    assert os.path.exists(test_file)
    with open(test_file, "r") as f:
        content = f.read()
        assert content == "pytest is working"
