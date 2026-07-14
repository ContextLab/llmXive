import os
import pytest
from pathlib import Path
from setup_project import ensure_directories

class TestProjectSetup:
    def test_directories_exist(self):
        """Test that the required directories are created."""
        base_path = Path("projects/PROJ-077-investigating-the-correlation-between-gu")
        expected_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "tests"
        ]
        
        # Run the setup function
        created_dirs = ensure_directories()
        
        # Verify each expected directory exists
        for expected_dir in expected_dirs:
            full_path = base_path / expected_dir
            assert full_path.exists(), f"Directory {full_path} does not exist"
            assert full_path.is_dir(), f"{full_path} is not a directory"

    def test_correct_base_path(self):
        """Verify the base path is correct."""
        base_path = Path("projects/PROJ-077-investigating-the-correlation-between-gu")
        assert base_path.exists(), "Base project directory should exist"
        
        # Verify it contains the expected subdirectories
        assert (base_path / "data").exists(), "data directory missing"
        assert (base_path / "code").exists(), "code directory missing"
        assert (base_path / "tests").exists(), "tests directory missing"