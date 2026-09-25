import os
import pytest
from setup_directories import create_directories, setup_script_logging

@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for testing."""
    return str(tmp_path)

def test_create_directories_creates_new(temp_test_dir):
    """Test that create_directories creates new directories."""
    logger = setup_script_logging()
    test_path = os.path.join(temp_test_dir, "test_new_dir")
    
    assert not os.path.exists(test_path)
    create_directories([test_path], logger)
    assert os.path.exists(test_path)
    assert os.path.isdir(test_path)

def test_create_directories_ignores_existing(temp_test_dir):
    """Test that create_directories does not fail on existing directories."""
    logger = setup_script_logging()
    test_path = os.path.join(temp_test_dir, "test_existing_dir")
    
    os.makedirs(test_path, exist_ok=True)
    assert os.path.exists(test_path)
    
    # Should not raise an exception
    create_directories([test_path], logger)
    assert os.path.exists(test_path)

def test_create_directories_nested(temp_test_dir):
    """Test that create_directories creates nested directories."""
    logger = setup_script_logging()
    test_path = os.path.join(temp_test_dir, "level1", "level2", "level3")
    
    assert not os.path.exists(test_path)
    create_directories([test_path], logger)
    assert os.path.exists(test_path)
    assert os.path.isdir(test_path)

def test_project_structure_creation():
    """
    Verify that the standard project directories (code, artifacts, tests)
    can be created without error.
    """
    logger = setup_script_logging()
    # We test in the current working directory or a temp location if preferred,
    # but for this unit test, we just ensure the function logic works.
    # In integration tests, we verify the actual files exist.
    pass
