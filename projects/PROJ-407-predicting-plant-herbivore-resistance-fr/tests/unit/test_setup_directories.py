import os
import pytest
from pathlib import Path
import shutil
import tempfile
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_directories import ensure_directories

class TestSetupDirectories:
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Create a temporary directory to simulate the project root."""
        self.original_cwd = os.getcwd()
        # Change to the temporary directory
        os.chdir(tmp_path)
        # Create a fake 'code' directory so the script finds its parent correctly
        (tmp_path / "code").mkdir()
        yield tmp_path
        # Restore original working directory and clean up
        os.chdir(self.original_cwd)
        # Note: tmp_path is automatically cleaned up by pytest

    def test_creates_required_directories(self, tmp_path):
        """Test that ensure_directories creates all required folders."""
        # Change to the temp directory which acts as project root
        os.chdir(tmp_path)
        
        result = ensure_directories()
        
        assert result is True, "ensure_directories should return True on success"
        
        # Check all required directories exist
        required_dirs = [
            "code",
            "data/raw",
            "data/interim",
            "data/processed",
            "data/results",
            "tests/unit",
            "tests/integration",
            "tests/contract"
        ]
        
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"

    def test_handles_existing_directories(self, tmp_path):
        """Test that ensure_directories handles pre-existing directories gracefully."""
        os.chdir(tmp_path)
        
        # Pre-create some directories
        (tmp_path / "code").mkdir()
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "raw").mkdir()
        
        result = ensure_directories()
        
        assert result is True, "ensure_directories should return True even if dirs exist"
        
        # Verify they still exist
        assert (tmp_path / "code").exists()
        assert (tmp_path / "data" / "raw").exists()

    def test_nested_structure_created(self, tmp_path):
        """Test that nested directory structures (e.g., data/raw) are created."""
        os.chdir(tmp_path)
        
        ensure_directories()
        
        # Verify nested paths
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "interim").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "data" / "results").exists()
        assert (tmp_path / "tests" / "unit").exists()
        assert (tmp_path / "tests" / "integration").exists()
        assert (tmp_path / "tests" / "contract").exists()
