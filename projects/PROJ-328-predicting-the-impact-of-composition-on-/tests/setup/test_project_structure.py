import pytest
from pathlib import Path
import sys
import os

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_project_structure import verify_directory_structure

def test_verify_directory_structure():
    """Test that the directory structure verification works."""
    # Get project root (parent of code/)
    project_root = Path(__file__).parent.parent.parent
    
    # Verify structure
    result = verify_directory_structure(project_root)
    
    # Assert all directories exist
    assert result is True, "Directory structure verification failed"

def test_required_dirs_exist():
    """Explicitly check for required directories."""
    project_root = Path(__file__).parent.parent.parent
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "data/config",
        "code/ingestion",
        "code/features",
        "code/models",
        "code/evaluation",
        "code/visualization",
        "code/utils",
        "tests/contract",
        "tests/integration",
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Missing directory: {full_path}"
        assert full_path.is_dir(), f"Not a directory: {full_path}"