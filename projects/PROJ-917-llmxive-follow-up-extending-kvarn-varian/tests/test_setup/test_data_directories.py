import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add the project root to the path to allow imports
# Assuming tests are in tests/ and code is in code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from setup_data_directories import create_directories, get_project_root

class TestDataDirectories:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """
        Setup and teardown for tests.
        Creates a temporary directory structure to simulate the project root.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Create a fake project structure in temp_dir
        # We want code/ to exist so get_project_root works correctly if run from there
        # But for this test, we will mock the path or run from the temp_dir root
        # Actually, the script assumes it runs from project root.
        # Let's create the structure: temp_dir/code/...
        os.chdir(self.temp_dir)
        
        # Create a dummy code dir to simulate project root context
        (Path(self.temp_dir) / "code").mkdir()
        
        yield
        
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_data_raw_exists(self):
        """Test that data/raw directory is created."""
        create_directories()
        data_raw = Path(self.temp_dir) / "data" / "raw"
        assert data_raw.exists(), "data/raw directory should exist"
        assert data_raw.is_dir(), "data/raw should be a directory"

    def test_data_processed_exists(self):
        """Test that data/processed directory is created."""
        create_directories()
        data_processed = Path(self.temp_dir) / "data" / "processed"
        assert data_processed.exists(), "data/processed directory should exist"
        assert data_processed.is_dir(), "data/processed should be a directory"

    def test_data_results_exists(self):
        """Test that data/results directory is created."""
        create_directories()
        data_results = Path(self.temp_dir) / "data" / "results"
        assert data_results.exists(), "data/results directory should exist"
        assert data_results.is_dir(), "data/results should be a directory"

    def test_data_models_exists(self):
        """Test that data/models directory is created."""
        create_directories()
        data_models = Path(self.temp_dir) / "data" / "models"
        assert data_models.exists(), "data/models directory should exist"
        assert data_models.is_dir(), "data/models should be a directory"

    def test_create_directories_returns_true(self):
        """Test that create_directories returns True on success."""
        result = create_directories()
        assert result is True, "create_directories should return True"
