"""
Unit tests for setup_structure.py to verify T001 completion.
"""
import os
import sys
import pytest
from pathlib import Path

# Add code root to path for imports
code_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(code_root))

from setup_structure import create_directories

class TestSetupStructure:
    def test_directories_exist(self, tmp_path):
        """
        Verify that the create_directories function creates the expected structure.
        We use a temporary directory to simulate the project root.
        """
        # Create a temporary "project root"
        temp_root = tmp_path / "project_root"
        temp_root.mkdir()
        
        # Mock the __file__ behavior by changing to the temp dir context
        # We can't easily mock __file__ inside the function, so we test the logic
        # by verifying the function runs without error and creates dirs if we passed the right args.
        # However, since the function is hardcoded to look at __file__'s parent,
        # we will test the existence of dirs relative to the actual run context.
        
        # Instead, we test the specific paths that T001 requires.
        # Since we are running this test, the script should have been run or we run it here.
        
        # Let's run the function to ensure it executes
        # Note: In a real CI, the script runs once. Here we verify the paths exist after execution.
        create_directories()
        
        # Verify the paths relative to the actual code directory
        # Assuming this test runs from code/tests/unit/
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent 
        
        required_dirs = [
            "src/bias_pipeline",
            "src/cli",
            "data/raw",
            "data/processed",
            "data/validation",
            "tests/unit",
            "tests/integration",
            "state"
        ]
        
        for rel_dir in required_dirs:
            full_path = project_root / rel_dir
            assert full_path.exists(), f"Directory {full_path} was not created."
            assert full_path.is_dir(), f"{full_path} exists but is not a directory."

    def test_init_files_exist(self):
        """Verify that __init__.py files were created for package recognition."""
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent
        
        required_inits = [
            project_root / "src" / "__init__.py",
            project_root / "src" / "bias_pipeline" / "__init__.py",
            project_root / "src" / "cli" / "__init__.py",
            project_root / "tests" / "__init__.py",
            project_root / "tests" / "unit" / "__init__.py",
            project_root / "tests" / "integration" / "__init__.py",
        ]
        
        for init_file in required_inits:
            assert init_file.exists(), f"Init file {init_file} is missing."