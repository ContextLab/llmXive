import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_structure import main

class TestSetupStructure:
    def test_directory_creation(self, tmp_path):
        """Test that the script creates the required directory structure."""
        # Change to temporary directory to simulate project root
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run the setup script
            exit_code = main()
            
            # Verify exit code is 0
            assert exit_code == 0, "Setup script should exit with code 0"
            
            # Define expected directories
            base_project_dir = tmp_path / "projects" / "PROJ-470-predicting-cognitive-fatigue-from-restin"
            expected_dirs = [
                base_project_dir,
                base_project_dir / "data" / "raw",
                base_project_dir / "data" / "processed",
                base_project_dir / "data" / "analysis",
                base_project_dir / "code",
                base_project_dir / "tests" / "unit",
                base_project_dir / "tests" / "integration",
                base_project_dir / "docs",
            ]
            
            # Verify each directory exists
            for dir_path in expected_dirs:
                assert dir_path.exists(), f"Directory {dir_path} should exist"
                assert dir_path.is_dir(), f"{dir_path} should be a directory"
                
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def test_idempotency(self, tmp_path):
        """Test that running the script twice doesn't cause errors."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run the setup script twice
            exit_code_1 = main()
            exit_code_2 = main()
            
            # Both runs should succeed
            assert exit_code_1 == 0
            assert exit_code_2 == 0
            
            # Verify directories still exist
            base_project_dir = tmp_path / "projects" / "PROJ-470-predicting-cognitive-fatigue-from-restin"
            assert base_project_dir.exists()
            assert (base_project_dir / "data" / "raw").exists()
            
        finally:
            os.chdir(original_cwd)

    def test_correct_naming(self, tmp_path):
        """Test that directories are created with correct names."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            main()
            
            base_project_dir = tmp_path / "projects" / "PROJ-470-predicting-cognitive-fatigue-from-restin"
            
            # Check specific directory names
            assert (base_project_dir / "data" / "raw").name == "raw"
            assert (base_project_dir / "data" / "processed").name == "processed"
            assert (base_project_dir / "data" / "analysis").name == "analysis"
            assert (base_project_dir / "tests" / "unit").name == "unit"
            assert (base_project_dir / "tests" / "integration").name == "integration"
            assert (base_project_dir / "docs").name == "docs"
            
        finally:
            os.chdir(original_cwd)
