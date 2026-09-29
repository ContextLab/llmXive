import pytest
import os
import sys
from pathlib import Path
from code.setup_directories import create_project_structure

class TestProjectStructure:
    """Test that the project structure is correctly created."""
    
    def test_create_project_structure(self):
        """Verify that create_project_structure creates all required directories."""
        # Run the setup function
        result = create_project_structure()
        
        # Assert it returned True
        assert result is True
        
        # Define expected directories
        expected_dirs = [
            "code",
            "data",
            "outputs",
            "docs",
            "state",
            "data/raw",
            "data/processed",
            "data/metadata",
            "outputs/reports",
            "outputs/figures",
            "code/utils",
            "code/ingestion",
            "code/processing",
            "code/analysis",
            "code/tests",
        ]
        
        # Verify each directory exists
        for dir_path in expected_dirs:
            full_path = Path(dir_path)
            assert full_path.exists(), f"Directory {dir_path} should exist"
            assert full_path.is_dir(), f"{dir_path} should be a directory"
    
    def test_required_root_directories(self):
        """Verify that all required root directories exist."""
        required_roots = ["code", "data", "outputs", "docs", "state"]
        
        for root_dir in required_roots:
            path = Path(root_dir)
            assert path.exists(), f"Root directory {root_dir} must exist"
            assert path.is_dir(), f"{root_dir} must be a directory"
    
    def test_data_subdirectories(self):
        """Verify data subdirectories are created."""
        data_subdirs = ["data/raw", "data/processed", "data/metadata"]
        
        for subdir in data_subdirs:
            path = Path(subdir)
            assert path.exists(), f"Data subdirectory {subdir} must exist"
            assert path.is_dir(), f"{subdir} must be a directory"
    
    def test_outputs_subdirectories(self):
        """Verify outputs subdirectories are created."""
        outputs_subdirs = ["outputs/reports", "outputs/figures"]
        
        for subdir in outputs_subdirs:
            path = Path(subdir)
            assert path.exists(), f"Outputs subdirectory {subdir} must exist"
            assert path.is_dir(), f"{subdir} must be a directory"
    
    def test_code_subdirectories(self):
        """Verify code subdirectories are created."""
        code_subdirs = [
            "code/utils",
            "code/ingestion",
            "code/processing",
            "code/analysis",
            "code/tests"
        ]
        
        for subdir in code_subdirs:
            path = Path(subdir)
            assert path.exists(), f"Code subdirectory {subdir} must exist"
            assert path.is_dir(), f"{subdir} must be a directory"