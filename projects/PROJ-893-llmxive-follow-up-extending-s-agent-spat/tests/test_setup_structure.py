import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_structure import create_directories

class TestSetupStructure:
    def test_directories_created(self):
        """Test that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            create_directories(base_path)
            
            required_dirs = [
                "code",
                "data/raw",
                "data/derived",
                "data/results",
                "specs",
                "tests",
                "state/projects"
            ]
            
            for dir_name in required_dirs:
                dir_path = base_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"

    def test_nested_directories_created(self):
        """Test that nested directories (e.g., data/raw) are created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            create_directories(base_path)
            
            # Check specific nested paths
            assert (base_path / "data" / "raw").exists()
            assert (base_path / "data" / "derived").exists()
            assert (base_path / "data" / "results").exists()
            assert (base_path / "state" / "projects").exists()

    def test_idempotent_creation(self):
        """Test that running create_directories twice doesn't raise errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            create_directories(base_path)
            # Running again should not raise
            create_directories(base_path)
            
            assert (base_path / "code").exists()
            assert (base_path / "data" / "raw").exists()

    def test_main_entry_point(self):
        """Test the main function executes without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                from setup_structure import main
                main()
                assert (Path(tmpdir) / "code").exists()
            finally:
                os.chdir(original_cwd)