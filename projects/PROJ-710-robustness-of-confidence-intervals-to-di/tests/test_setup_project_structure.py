"""
Tests for the project setup script (T001a).
Verifies that the required directory structure is created correctly.
"""
import os
import pytest
from pathlib import Path
import shutil

from code.setup_project_structure import main as setup_main

class TestProjectSetup:
    """Test cases for project directory structure creation."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Store original state if needed
        self.base_path = Path("projects/PROJ-710-robustness-of-confidence-intervals-to-di")
        
        # Clean up before test if directory exists
        if self.base_path.exists():
            shutil.rmtree(self.base_path)
        
        yield
        
        # Cleanup after test
        if self.base_path.exists():
            shutil.rmtree(self.base_path)
    
    def test_main_creates_all_directories(self):
        """Test that main() creates all required directories."""
        # Run the setup
        result = setup_main()
        
        # Verify result
        assert result is True, "main() should return True on success"
        
        # Verify all required directories exist
        required_dirs = [
            "code",
            "code/data",
            "code/analysis",
            "code/utils",
            "code/tests",
            "artifacts",
        ]
        
        for dir_path in required_dirs:
            full_path = self.base_path / dir_path
            assert full_path.exists(), f"Directory {full_path} should exist"
            assert full_path.is_dir(), f"{full_path} should be a directory"
    
    def test_directory_structure_is_valid(self):
        """Test that the created directory structure is valid."""
        # Run the setup
        setup_main()
        
        # Verify parent-child relationships
        code_dir = self.base_path / "code"
        assert code_dir.exists()
        assert code_dir.is_dir()
        
        # Verify subdirectories are inside code/
        subdirs = ["data", "analysis", "utils", "tests"]
        for subdir in subdirs:
            subdir_path = code_dir / subdir
            assert subdir_path.exists(), f"{subdir_path} should exist"
            assert subdir_path.is_dir(), f"{subdir_path} should be a directory"
        
        # Verify artifacts directory exists at project root
        artifacts_dir = self.base_path / "artifacts"
        assert artifacts_dir.exists(), "artifacts directory should exist"
        assert artifacts_dir.is_dir(), "artifacts should be a directory"
    
    def test_idempotent_creation(self):
        """Test that running setup multiple times doesn't cause errors."""
        # Run setup twice
        result1 = setup_main()
        result2 = setup_main()
        
        # Both should succeed
        assert result1 is True
        assert result2 is True
        
        # Verify directories still exist
        required_dirs = [
            "code",
            "code/data",
            "code/analysis",
            "code/utils",
            "code/tests",
            "artifacts",
        ]
        
        for dir_path in required_dirs:
            full_path = self.base_path / dir_path
            assert full_path.exists(), f"Directory {full_path} should still exist"