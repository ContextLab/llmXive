import os
import tempfile
import shutil
from pathlib import Path
import pytest
from src.verify_structure import verify_structure

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure mimicking a valid project."""
    temp_dir = tempfile.mkdtemp()
    root = Path(temp_dir)
    
    required_dirs = [
        "src/data",
        "src/models",
        "src/analysis",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs",
    ]
    
    for d in required_dirs:
        (root / d).mkdir(parents=True, exist_ok=True)
        
    yield root
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_project_root_missing():
    """Create a temporary directory structure with missing directories."""
    temp_dir = tempfile.mkdtemp()
    root = Path(temp_dir)
    
    # Create only some directories
    (root / "src/data").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    
    yield root
    shutil.rmtree(temp_dir)

def test_verify_structure_all_present(temp_project_root):
    """Test that verify_structure returns True when all dirs exist."""
    assert verify_structure(temp_project_root) is True

def test_verify_structure_missing_dirs(temp_project_root_missing):
    """Test that verify_structure returns False when some dirs are missing."""
    assert verify_structure(temp_project_root_missing) is False

def test_verify_structure_empty_root():
    """Test verify_structure on an empty directory."""
    temp_dir = tempfile.mkdtemp()
    root = Path(temp_dir)
    try:
        assert verify_structure(root) is False
    finally:
        shutil.rmtree(temp_dir)