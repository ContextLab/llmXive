import os
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports if running from tests/
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_data_structure import setup_data_structure
from utils import get_project_root_path

def test_setup_data_structure_creates_directories():
    """
    Verify that setup_data_structure creates the required directories:
    data/raw, data/processed, data/qc
    """
    project_root = get_project_root_path()
    data_root = project_root / "data"
    
    required_dirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "qc",
    ]

    # Run the setup function
    result = setup_data_structure()
    
    assert result is True, "setup_data_structure should return True"
    
    for d in required_dirs:
        assert d.exists(), f"Directory {d} should exist after setup"
        assert d.is_dir(), f"{d} should be a directory"

def test_directories_are_empty_or_valid():
    """
    Verify that the created directories are valid filesystem objects.
    """
    project_root = get_project_root_path()
    data_root = project_root / "data"
    
    required_dirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "qc",
    ]

    for d in required_dirs:
        assert d.is_dir()
        # We don't assert they are empty because they might contain .gitkeep or previous runs
        # but they must be accessible
        assert os.access(d, os.R_OK | os.W_OK)
