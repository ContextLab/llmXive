import os
import pytest
from pathlib import Path
import sys

# Add code to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project_structure import setup_directories

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory acting as the project root."""
    return tmp_path

def test_setup_creates_required_directories(temp_project_root):
    """Verify that setup_directories creates all required paths."""
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "code/ingestion",
        "code/features",
        "code/models",
        "code/evaluation",
        "code/visualization",
        "tests",
        "models"
    ]
    
    setup_directories(temp_project_root)
    
    for rel_path in required_dirs:
        full_path = temp_project_root / rel_path
        assert full_path.exists(), f"Directory {rel_path} was not created"
        assert full_path.is_dir(), f"Path {rel_path} exists but is not a directory"

def test_setup_creates_code_root(temp_project_root):
    """Verify that the main 'code' directory is created."""
    setup_directories(temp_project_root)
    code_root = temp_project_root / "code"
    assert code_root.exists()
    assert code_root.is_dir()

def test_setup_idempotent(temp_project_root):
    """Verify that running setup twice does not raise errors."""
    setup_directories(temp_project_root)
    setup_directories(temp_project_root)
    
    # Verify directories still exist
    assert (temp_project_root / "data/raw").exists()
    assert (temp_project_root / "code/models").exists()
