import os
import pytest
from pathlib import Path
import sys
import subprocess

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_directories import ensure_directories

class TestProjectStructureIntegration:
    """Integration test to verify the full project structure is created correctly."""
    
    @pytest.fixture(autouse=True)
    def setup_environment(self, tmp_path):
        """Setup a temporary project environment."""
        self.original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        # Create a 'code' directory so the script can locate the project root
        (tmp_path / "code").mkdir()
        
        yield tmp_path
        
        os.chdir(self.original_cwd)

    def test_full_structure_creation(self, tmp_path):
        """
        Run the directory setup script and verify the complete structure.
        This simulates the actual execution of T001.
        """
        # Execute the setup function
        success = ensure_directories()
        
        assert success, "Directory setup should succeed"
        
        # Define the expected structure
        expected_structure = {
            "code": [],
            "data": ["raw", "interim", "processed", "results"],
            "tests": ["unit", "integration", "contract"]
        }
        
        # Verify top-level directories
        for top_dir in expected_structure.keys():
            top_path = tmp_path / top_dir
            assert top_path.exists(), f"Top-level directory {top_dir} missing"
            assert top_path.is_dir(), f"{top_dir} is not a directory"
            
            # Verify subdirectories
            for sub_dir in expected_structure[top_dir]:
                sub_path = top_path / sub_dir
                assert sub_path.exists(), f"Subdirectory {top_dir}/{sub_dir} missing"
                assert sub_path.is_dir(), f"{top_dir}/{sub_dir} is not a directory"

    def test_no_orphan_files(self, tmp_path):
        """Verify that only directories were created, no unexpected files."""
        ensure_directories()
        
        # List all items in the project root
        items = list(tmp_path.iterdir())
        
        expected_names = {"code", "data", "tests"}
        
        for item in items:
            assert item.name in expected_names, f"Unexpected item found: {item.name}"
            assert item.is_dir(), f"Unexpected file found in root: {item.name}"

    def test_directories_are_writable(self, tmp_path):
        """Verify that the created directories are writable."""
        ensure_directories()
        
        # Test writing a temporary file to each directory
        test_dirs = [
            "code",
            "data/raw",
            "data/interim",
            "data/processed",
            "data/results",
            "tests/unit",
            "tests/integration",
            "tests/contract"
        ]
        
        for dir_path_str in test_dirs:
            dir_path = tmp_path / dir_path_str
            test_file = dir_path / ".write_test"
            
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                # Clean up
                test_file.unlink()
            except Exception as e:
                pytest.fail(f"Directory {dir_path} is not writable: {e}")