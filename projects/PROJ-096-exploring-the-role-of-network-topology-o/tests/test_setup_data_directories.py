"""
Test for Task T001b: Verify data directories are created correctly.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the project root to the path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

from code.setup_data_directories import create_data_directories

class TestDataDirectories:
    """Test cases for data directory creation."""

    def setup_method(self):
        """Set up a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create the code directory structure
        code_dir = Path(self.temp_dir) / "code"
        code_dir.mkdir()
        (code_dir / "__init__.py").touch()

        # Copy the module to the temp location
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "setup_data_directories",
            project_root / "code" / "setup_data_directories.py"
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def teardown_method(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_directories_created(self):
        """Verify that all required directories are created."""
        result = self.module.create_data_directories()
        assert result is True

        data_dir = Path(self.temp_dir) / "data"
        assert data_dir.exists()
        assert (data_dir / "processed").exists()
        assert (data_dir / "checksums").exists()
        assert (data_dir / "raw").exists()

    def test_processed_directory_exists(self):
        """Verify that data/processed exists after creation."""
        self.module.create_data_directories()
        data_dir = Path(self.temp_dir) / "data"
        processed_dir = data_dir / "processed"
        assert processed_dir.exists()
        assert processed_dir.is_dir()

    def test_idempotent_creation(self):
        """Verify that running the function twice doesn't cause errors."""
        result1 = self.module.create_data_directories()
        result2 = self.module.create_data_directories()
        assert result1 is True
        assert result2 is True

        data_dir = Path(self.temp_dir) / "data"
        assert (data_dir / "processed").exists()
        assert (data_dir / "checksums").exists()
        assert (data_dir / "raw").exists()