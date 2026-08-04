import os
import pytest
from pathlib import Path
from code.setup_directories import create_project_directories

class TestCreateProjectDirectories:
    """Tests for the create_project_directories function."""

    def test_directories_created(self):
        """Test that all required directories are created."""
        # Run the function
        success = create_project_directories()
        
        # Assert success
        assert success, "Directory creation should succeed"
        
        # Define expected paths
        project_root = Path("projects/PROJ-271-evaluating-the-effectiveness-of-llms-for")
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "results",
            "tests/unit",
            "tests/contract",
        ]
        
        # Verify each directory exists
        for dir_path in expected_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory {full_path} should exist"
            assert full_path.is_dir(), f"{full_path} should be a directory"

    def test_idempotent(self):
        """Test that running the function twice doesn't cause errors."""
        # Run twice
        success1 = create_project_directories()
        success2 = create_project_directories()
        
        assert success1, "First run should succeed"
        assert success2, "Second run should succeed (idempotent)"