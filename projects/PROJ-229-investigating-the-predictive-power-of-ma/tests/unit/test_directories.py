"""
Unit tests to verify the project directory structure.
Checks that all required data/, code/, and tests/ subfolders exist.
"""
import os
import pytest
from pathlib import Path
from config import get_config

def get_project_root():
    """Retrieve the project root path from config or default."""
    try:
        config = get_config()
        return Path(config.get("project_root", "."))
    except Exception:
        # Fallback if config is not loaded or project_root is missing
        return Path(".")

class TestDirectoryStructure:
    """Tests for verifying the existence of required project directories."""

    def test_data_directories_exist(self):
        """Verify that all required data subdirectories exist."""
        root = get_project_root()
        required_data_dirs = [
            "data/raw",
            "data/processed",
            "data/results",
            "data/external",
        ]
        
        for dir_name in required_data_dirs:
            dir_path = root / dir_name
            assert dir_path.exists(), f"Missing required directory: {dir_path}"
            assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

    def test_code_directories_exist(self):
        """Verify that all required code subdirectories exist."""
        root = get_project_root()
        required_code_dirs = [
            "code/data",
            "code/models",
            "code/utils",
            "code/validate",
        ]
        
        for dir_name in required_code_dirs:
            dir_path = root / dir_name
            assert dir_path.exists(), f"Missing required directory: {dir_path}"
            assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

    def test_test_directories_exist(self):
        """Verify that all required test subdirectories exist (T001c)."""
        root = get_project_root()
        required_test_dirs = [
            "tests/unit",
            "tests/integration",
            "tests/contract",
        ]
        
        for dir_name in required_test_dirs:
            dir_path = root / dir_name
            assert dir_path.exists(), f"Missing required directory: {dir_path}"
            assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

    def test_project_structure_integrity(self):
        """
        High-level check to ensure the basic project structure is intact.
        """
        root = get_project_root()
        
        # Check top-level directories
        assert (root / "data").exists(), "Missing 'data' root directory"
        assert (root / "code").exists(), "Missing 'code' root directory"
        assert (root / "tests").exists(), "Missing 'tests' root directory"
        
        # Check key files exist
        assert (root / "config.yaml").exists(), "Missing 'config.yaml'"
        assert (root / "requirements.txt").exists(), "Missing 'requirements.txt'"