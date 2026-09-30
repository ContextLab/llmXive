import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the scripts directory to the path to allow imports
# Assuming this test runs from the project root or code/tests/unit
# We need to import from code/scripts
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from setup_project_structure import setup_directories, DIRECTORIES, PROJECT_ROOT

class TestProjectStructureSetup:
    """
    Tests to verify that the project directory structure is created correctly.
    """

    def test_directories_defined(self):
        """Verify that the required directories are defined in the constant."""
        expected_dirs = [
            "src",
            "tests",
            "data",
            "data/raw",
            "data/derived",
            "data/gold_standard",
            "artifacts",
            "specs/001-llmxive-follow-up-extending-arcane-do-ro"
        ]
        assert set(DIRECTORIES) == set(expected_dirs), f"Directories mismatch: {DIRECTORIES} vs {expected_dirs}"

    def test_setup_creates_directories(self, tmp_path):
        """Test that setup_directories actually creates the directories in a temporary location."""
        # Change PROJECT_ROOT temporarily for the test
        original_root = Path.cwd()
        
        # Use tmp_path as the temporary project root
        os.chdir(tmp_path)
        
        try:
            # Re-import or re-evaluate PROJECT_ROOT logic if it depends on cwd
            # Since the function uses Path.cwd(), we just need to ensure we are in tmp_path
            # The function setup_directories does not take arguments, so it relies on global PROJECT_ROOT
            # We need to monkeypatch the function or the module to use tmp_path
            
            # Simpler approach: just call the logic directly in the test context
            # But to test the actual script logic, we should patch the module's PROJECT_ROOT
            
            import setup_project_structure
            setup_project_structure.PROJECT_ROOT = tmp_path
            
            setup_directories()
            
            # Verify all directories exist
            for dir_name in DIRECTORIES:
                full_path = tmp_path / dir_name
                assert full_path.exists(), f"Directory {full_path} was not created"
                assert full_path.is_dir(), f"{full_path} is not a directory"
            
        finally:
            # Restore original directory
            os.chdir(original_root)
            # Restore original PROJECT_ROOT if needed, though it's a local variable in module scope usually
            # Reloading the module would reset it, but for this test, just changing cwd back is enough for next tests

    def test_nested_directories_created(self, tmp_path):
        """Verify that nested directories (e.g., data/raw) are created with parents=True."""
        import setup_project_structure
        setup_project_structure.PROJECT_ROOT = tmp_path
        
        setup_directories()
        
        # Check specific nested paths
        nested_paths = [
            "data/raw",
            "data/derived",
            "data/gold_standard",
            "specs/001-llmxive-follow-up-extending-arcane-do-ro"
        ]
        
        for path_str in nested_paths:
            full_path = tmp_path / path_str
            assert full_path.exists(), f"Nested directory {full_path} was not created"