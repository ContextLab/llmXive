"""
Unit tests to verify the project structure creation.
"""
import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_project_structure import create_project_structure

def test_required_directories_exist():
    """Verify that all required directories are created."""
    # Run the creation script
    create_project_structure()
    
    root = Path.cwd()
    required_dirs = [
        "code/data",
        "code/models",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/results",
        "specs/001-phase-change-predictive-power/contracts"
    ]
    
    for dir_path in required_dirs:
        full_path = root / dir_path
        assert full_path.exists(), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} is not a directory"

def test_nested_structure_valid():
    """Verify nested directories were created correctly."""
    root = Path.cwd()
    
    # Check deep nesting
    contracts_path = root / "specs/001-phase-change-predictive-power/contracts"
    assert contracts_path.exists(), "Contracts directory not created"
    assert contracts_path.is_dir(), "Contracts path is not a directory"
    
    # Check parent directories exist
    assert (root / "specs").exists()
    assert (root / "specs/001-phase-change-predictive-power").exists()