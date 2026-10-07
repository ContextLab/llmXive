import os
import pytest
from pathlib import Path
import sys

# Add code to path if not already present
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_project_structure import create_directories, verify_directories
from utils.config import get_project_root

class TestProjectStructure:
    """
    Tests for T002: Create project directory structure.
    """

    def test_create_directories_creates_all_required(self):
        """Verify that create_directories creates all required folders."""
        project_root = get_project_root()
        
        # Ensure directories exist by running creation
        create_directories()
        
        required_dirs = [
            "code",
            "tests",
            "data",
            "data/raw",
            "data/processed",
            "state/projects",
            "state/pending",
            "specs/001-molecular-flexibility-permeability/contracts",
        ]
        
        for rel_path in required_dirs:
            full_path = project_root / rel_path
            assert full_path.exists(), f"Directory {full_path} should exist after creation."
            assert full_path.is_dir(), f"{full_path} should be a directory."

    def test_verify_directories_returns_true_when_all_exist(self):
        """Verify that verify_directories returns True when all directories exist."""
        # First ensure they are created
        create_directories()
        
        result = verify_directories()
        assert result is True, "verify_directories should return True when all directories exist."

    def test_specific_contracts_directory_exists(self):
        """Specific test for the deep nested contracts directory required by T007."""
        project_root = get_project_root()
        contracts_dir = project_root / "specs" / "001-molecular-flexibility-permeability" / "contracts"
        
        create_directories()
        
        assert contracts_dir.exists(), f"Contracts directory {contracts_dir} must exist."
        assert contracts_dir.is_dir(), f"{contracts_dir} must be a directory."
