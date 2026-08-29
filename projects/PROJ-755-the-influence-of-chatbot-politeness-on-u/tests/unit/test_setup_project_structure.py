import os
import sys
import pytest
from pathlib import Path
import shutil
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_project_structure import create_structure

class TestSetupProjectStructure:
    """Unit tests for the project structure creation script."""

    @pytest.fixture
    def temp_test_dir(self):
        """Create a temporary directory for testing."""
        original_dir = os.getcwd()
        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)
        yield temp_dir
        os.chdir(original_dir)
        shutil.rmtree(temp_dir)

    def test_creates_required_directories(self, temp_test_dir):
        """Test that all required directories are created."""
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "code/utils",
            "tests",
            "tests/contract",
            "tests/unit",
            "tests/integration",
            "docs",
            "state"
        ]
        
        # Verify directories don't exist before
        for dir_path in required_dirs:
            assert not Path(dir_path).exists(), f"Directory {dir_path} should not exist before test"

        # Run the function
        result = create_structure()

        # Verify all directories exist after
        for dir_path in required_dirs:
            full_path = Path(dir_path)
            assert full_path.exists(), f"Directory {dir_path} should exist after creation"
            assert full_path.is_dir(), f"{dir_path} should be a directory"

        assert result is True

    def test_idempotent_creation(self, temp_test_dir):
        """Test that running the function twice doesn't cause errors."""
        # Run once
        create_structure()
        
        # Run again - should not raise exceptions
        result = create_structure()
        assert result is True

    def test_nested_directory_creation(self, temp_test_dir):
        """Test that nested directories are created correctly."""
        # Create only the parent
        Path("data").mkdir()
        
        # Run structure creation
        create_structure()
        
        # Verify nested structure exists
        assert Path("data/raw").exists()
        assert Path("data/processed").exists()
        assert Path("code/utils").exists()
        assert Path("tests/contract").exists()
        assert Path("tests/unit").exists()
        assert Path("tests/integration").exists()

    def test_directory_permissions(self, temp_test_dir):
        """Test that created directories are writable."""
        create_structure()
        
        # Test writing a file to each directory
        test_files = [
            "data/raw/.gitkeep",
            "data/processed/.gitkeep",
            "code/utils/.gitkeep",
            "tests/.gitkeep",
            "docs/.gitkeep",
            "state/.gitkeep"
        ]
        
        for file_path in test_files:
            path = Path(file_path)
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            # Try to write
            path.touch()
            assert path.exists(), f"Should be able to create file in {path.parent}"
            assert os.access(path, os.W_OK), f"Directory {path.parent} should be writable"
            # Cleanup
            path.unlink()