import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from code.setup.create_data_dirs import create_directory_structure

class TestDataDirectoryCreation:
    """Tests for the data directory creation logic."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create a temporary directory to act as the project root for testing."""
        self.temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            yield
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_creates_data_raw_directory(self):
        """Verify that data/raw/ is created."""
        result = create_directory_structure()
        
        assert result is True, "Function should return True on success"
        
        data_raw = Path(self.temp_dir) / "data" / "raw"
        assert data_raw.exists(), "data/raw/ directory must exist"
        assert data_raw.is_dir(), "data/raw/ must be a directory"

    def test_creates_all_required_data_directories(self):
        """Verify that all required data directories are created."""
        result = create_directory_structure()
        
        assert result is True
        
        expected_dirs = [
            "data",
            "data/raw",
            "data/derived",
            "data/artifacts"
        ]
        
        for dir_path in expected_dirs:
            full_path = Path(self.temp_dir) / dir_path
            assert full_path.exists(), f"{dir_path} must exist"
            assert full_path.is_dir(), f"{dir_path} must be a directory"

    def test_idempotency(self):
        """Verify that running the function multiple times doesn't fail."""
        result1 = create_directory_structure()
        result2 = create_directory_structure()
        
        assert result1 is True
        assert result2 is True
        
        # Verify directories still exist and are valid
        data_raw = Path(self.temp_dir) / "data" / "raw"
        assert data_raw.exists() and data_raw.is_dir()