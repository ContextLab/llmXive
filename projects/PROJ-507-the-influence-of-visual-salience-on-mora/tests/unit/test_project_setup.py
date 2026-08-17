import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from project_setup import create_project_structure

class TestProjectStructure:
    """Unit tests for project structure creation."""

    def test_creates_all_required_directories(self):
        """Verify that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Call the function
                result = create_project_structure()
                
                # Verify return value
                assert result is True
                
                # Verify directories exist
                required_dirs = [
                    "code",
                    "data/raw",
                    "data/processed",
                    "data/survey",
                    "data/synth",
                    "tests",
                    "tests/unit",
                    "tests/integration",
                    "docs",
                    "config",
                    "figures",
                    "data/raw/human_coding",
                ]
                
                for dir_path in required_dirs:
                    full_path = Path(tmpdir) / dir_path
                    assert full_path.exists(), f"Directory not created: {dir_path}"
                    assert full_path.is_dir(), f"Path is not a directory: {dir_path}"
                    
            finally:
                os.chdir(original_cwd)

    def test_handles_existing_directories_gracefully(self):
        """Verify that existing directories are not overwritten or cause errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Pre-create some directories
                Path("code").mkdir()
                Path("data").mkdir()
                Path("data/raw").mkdir()
                
                # Call the function - should not raise
                result = create_project_structure()
                
                # Verify it still returns True
                assert result is True
                
                # Verify pre-existing directories still exist
                assert Path("code").is_dir()
                assert Path("data/raw").is_dir()
                
            finally:
                os.chdir(original_cwd)

    def test_raises_on_file_collision(self):
        """Verify that a file blocking a directory raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Create a file where a directory should be
                Path("code").touch()
                
                # Should raise FileExistsError
                with pytest.raises(FileExistsError):
                    create_project_structure()
                    
            finally:
                os.chdir(original_cwd)

    def test_creates_nested_directories(self):
        """Verify that nested directories (e.g., tests/unit) are created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                create_project_structure()
                
                # Verify nested structure
                assert Path("tests/unit").is_dir()
                assert Path("tests/integration").is_dir()
                assert Path("data/raw/human_coding").is_dir()
                
            finally:
                os.chdir(original_cwd)

    def test_directories_are_writable(self):
        """Verify that created directories are writable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                create_project_structure()
                
                # Try to write a test file to each directory
                test_dirs = [
                    "code",
                    "data/processed",
                    "data/survey",
                    "tests",
                ]
                
                for dir_path in test_dirs:
                    test_file = Path(tmpdir) / dir_path / ".test_write"
                    test_file.write_text("test")
                    assert test_file.exists()
                    test_file.unlink()
                    
            finally:
                os.chdir(original_cwd)
