"""
Unit tests for directory creation and verification (T001a).
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup.create_directories import create_directories, verify_directories

@pytest.fixture
def temp_root():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_create_directories_creates_all(temp_root):
    """Test that create_directories creates all specified directories."""
    required_dirs = [
        "code",
        "tests",
        "data",
        "code/lib",
        "code/data",
        "code/models",
        "code/evaluation",
        "data/results",
        "data/logs",
        "data/intermediate",
        "data/config"
    ]
    
    created = create_directories(temp_root, required_dirs)
    
    assert len(created) == len(required_dirs), "All directories should be created"
    
    for dir_path in required_dirs:
        full_path = temp_root / dir_path
        assert full_path.exists(), f"Directory {full_path} should exist"
        assert full_path.is_dir(), f"{full_path} should be a directory"

def test_verify_directories_returns_true(temp_root):
    """Test that verify_directories returns True when all dirs exist."""
    required_dirs = ["code", "data", "data/logs"]
    
    # First create them
    create_directories(temp_root, required_dirs)
    
    # Then verify
    assert verify_directories(temp_root, required_dirs) is True

def test_verify_directories_returns_false_missing(temp_root):
    """Test that verify_directories returns False when some dirs missing."""
    required_dirs = ["code", "nonexistent_dir"]
    
    # Only create one
    create_directories(temp_root, ["code"])
    
    # Verify should fail
    assert verify_directories(temp_root, required_dirs) is False

def test_nested_directories_created(temp_root):
    """Test that nested directories are created with parents=True."""
    nested_path = "code/lib/utils/helpers"
    create_directories(temp_root, [nested_path])
    
    full_path = temp_root / nested_path
    assert full_path.exists()
    assert full_path.is_dir()

def test_existing_directories_not_recreated(temp_root):
    """Test that existing directories are handled gracefully."""
    required_dirs = ["code", "data"]
    
    # Create once
    create_directories(temp_root, required_dirs)
    
    # Create again - should not fail
    created_again = create_directories(temp_root, required_dirs)
    
    assert len(created_again) == len(required_dirs)
    
    for dir_path in required_dirs:
        full_path = temp_root / dir_path
        assert full_path.exists()