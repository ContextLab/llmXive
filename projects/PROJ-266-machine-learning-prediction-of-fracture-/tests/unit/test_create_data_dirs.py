"""
Unit tests for data directory creation (Task T004a).

Verifies that the create_data_dirs script correctly creates the required
directory structure: data/raw, data/processed, data/explainability.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys
import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.create_data_dirs import main


class TestDataDirectoryCreation:
    """Test cases for T004a data directory creation."""

    def setup_method(self):
        """Create a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_creates_raw_directory(self):
        """Verify data/raw directory is created."""
        result = main()
        assert result == 0
        assert Path("data/raw").exists()
        assert Path("data/raw").is_dir()

    def test_creates_processed_directory(self):
        """Verify data/processed directory is created."""
        result = main()
        assert result == 0
        assert Path("data/processed").exists()
        assert Path("data/processed").is_dir()

    def test_creates_explainability_directory(self):
        """Verify data/explainability directory is created."""
        result = main()
        assert result == 0
        assert Path("data/explainability").exists()
        assert Path("data/explainability").is_dir()

    def test_all_directories_exist_simultaneously(self):
        """Verify all three directories exist after running main."""
        result = main()
        assert result == 0
        
        raw_exists = Path("data/raw").exists()
        processed_exists = Path("data/processed").exists()
        explainability_exists = Path("data/explainability").exists()
        
        assert raw_exists and processed_exists and explainability_exists

    def test_idempotent_creation(self):
        """Verify running main twice doesn't cause errors."""
        result1 = main()
        assert result1 == 0
        
        result2 = main()
        assert result2 == 0
        
        assert Path("data/raw").exists()
        assert Path("data/processed").exists()
        assert Path("data/explainability").exists()

    def test_verification_command_equivalent(self):
        """
        Verify the exact condition from T004a verification:
        test -d data/raw && test -d data/processed && test -d data/explainability
        """
        main()
        
        # Simulate the shell verification command
        assert Path("data/raw").is_dir(), "data/raw must be a directory"
        assert Path("data/processed").is_dir(), "data/processed must be a directory"
        assert Path("data/explainability").is_dir(), "data/explainability must be a directory"