import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.setup_directories import setup_directories, PROJECT_ROOT

def test_networks_directory_created():
    """
    Verifies that T001b requirement is met:
    `data/processed/networks/` directory exists after running setup.
    """
    # Ensure directories are created
    setup_directories()

    networks_dir = PROJECT_ROOT / "data" / "processed" / "networks"
    
    assert networks_dir.exists(), f"Directory {networks_dir} does not exist"
    assert networks_dir.is_dir(), f"{networks_dir} is not a directory"

def test_parent_directories_exist():
    """
    Verifies that parent directories required for the structure exist.
    """
    setup_directories()
    
    data_processed = PROJECT_ROOT / "data" / "processed"
    assert data_processed.exists()
    assert data_processed.is_dir()