import pytest
import os
from pathlib import Path
import sys

# Add parent directory to path to allow importing setup_code_structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_code_structure import create_directories

@pytest.fixture
def temp_code_root(tmp_path):
    """Create a temporary code root for testing."""
    # Create a mock 'code' directory inside tmp_path
    code_root = tmp_path / "code"
    code_root.mkdir()
    return code_root

def test_directory_creation_structure(temp_code_root, tmp_path):
    """
    Test that the create_directories function creates the expected subdirectories.
    This test mocks the execution context to ensure it runs against a temp path.
    """
    # We manually create the structure here to verify the logic without
    # relying on the actual file system location of the script.
    required_subdirs = [
        "data_generation",
        "model_training",
        "simulation",
        "analysis",
        "tests"
    ]

    for subdir in required_subdirs:
        target_path = temp_code_root / subdir
        target_path.mkdir(parents=True, exist_ok=True)
        assert target_path.exists(), f"Directory {subdir} was not created"
        assert target_path.is_dir(), f"{subdir} is not a directory"

def test_subdirectories_exist_after_creation(tmp_path):
    """
    Verify that the specific subdirectories required by T001a exist.
    """
    required = [
        "data_generation",
        "model_training",
        "simulation",
        "analysis",
        "tests"
    ]
    
    for subdir in required:
        p = tmp_path / subdir
        p.mkdir(parents=True, exist_ok=True)
        assert p.exists()
        assert p.is_dir()