"""
Unit tests to verify the directory structure created by T001a.
"""
import os
import pytest

@pytest.fixture
def project_root():
    """Get the project root directory."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_code_directories_exist(project_root):
    """Test that all code directories from T001a exist."""
    required_dirs = [
        "code",
        "code/data",
        "code/models",
        "code/train",
        "code/explain"
    ]
    
    for dir_name in required_dirs:
        full_path = os.path.join(project_root, dir_name)
        assert os.path.isdir(full_path), f"Directory missing: {dir_name}"

def test_data_directories_exist(project_root):
    """Test that all data directories from T001b exist."""
    required_dirs = [
        "data",
        "data/raw",
        "data/processed",
        "data/explainability"
    ]
    
    for dir_name in required_dirs:
        full_path = os.path.join(project_root, dir_name)
        assert os.path.isdir(full_path), f"Directory missing: {dir_name}"

def test_test_directories_exist(project_root):
    """Test that all test directories from T001c exist."""
    required_dirs = [
        "tests",
        "tests/unit",
        "tests/contract",
        "tests/integration"
    ]
    
    for dir_name in required_dirs:
        full_path = os.path.join(project_root, dir_name)
        assert os.path.isdir(full_path), f"Directory missing: {dir_name}"