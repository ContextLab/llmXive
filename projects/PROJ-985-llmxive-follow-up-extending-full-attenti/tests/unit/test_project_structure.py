import os
import pytest
from pathlib import Path
import sys

# Add code directory to path if not already present
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_project_structure import create_directories, verify_structure, REQUIRED_DIRS

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory to simulate project root."""
    return tmp_path

def test_create_directories_creates_all_required(temp_project_root):
    """Test that create_directories creates all required directories."""
    # Act
    created = create_directories(temp_project_root)
    
    # Assert
    assert len(created) == len(REQUIRED_DIRS), f"Expected {len(REQUIRED_DIRS)} directories, created {len(created)}"
    
    for dir_name in REQUIRED_DIRS:
        full_path = temp_project_root / dir_name
        assert full_path.exists(), f"Directory {dir_name} was not created"
        assert full_path.is_dir(), f"Path {dir_name} exists but is not a directory"

def test_verify_structure_returns_true_when_complete(temp_project_root):
    """Test that verify_structure returns True when all dirs exist."""
    # Arrange
    create_directories(temp_project_root)
    
    # Act
    success, message = verify_structure(temp_project_root)
    
    # Assert
    assert success is True
    assert "Missing directories" not in message

def test_verify_structure_returns_false_when_missing(temp_project_root):
    """Test that verify_structure returns False if a directory is missing."""
    # Arrange - create only some directories
    (temp_project_root / "code").mkdir()
    (temp_project_root / "tests").mkdir()
    # "data" is missing
    
    # Act
    success, message = verify_structure(temp_project_root)
    
    # Assert
    assert success is False
    assert "Missing directories" in message
    assert "data" in message

def test_required_dirs_list_is_complete():
    """Sanity check that REQUIRED_DIRS contains the expected paths."""
    expected = [
        "code", "tests", "data",
        "code/lib", "code/data", "code/models", "code/evaluation",
        "data/results", "data/logs", "data/intermediate"
    ]
    assert REQUIRED_DIRS == expected, f"REQUIRED_DIRS mismatch: {REQUIRED_DIRS}"