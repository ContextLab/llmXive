import os
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Mock the config module to use a temporary directory for testing
@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)

@pytest.fixture
def mock_config(temp_project_root):
    """Patch utils.config functions to use the temporary root."""
    with patch('utils.config.get_project_root', return_value=temp_project_root):
        with patch('utils.config.get_path', side_effect=lambda key: temp_project_root / key):
            with patch('utils.config.ensure_dirs_exist', side_effect=lambda p: p.mkdir(parents=True, exist_ok=True)):
                yield temp_project_root

class TestSetupDataDirs:
    """Test the data directory setup logic."""

    def test_creates_required_directories(self, mock_config):
        """Verify that setup_data_dirs creates raw, derived, logs, and results."""
        from setup_data_dirs import main
        import utils.config

        # Ensure the mock is active
        root = utils.config.get_project_root()
        
        # Run the setup
        main()

        # Check directories exist
        expected_dirs = ["raw", "derived", "logs", "results"]
        for subdir in expected_dirs:
            dir_path = root / "data" / subdir
            assert dir_path.exists(), f"Directory {dir_path} was not created."
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."

    def test_data_root_created(self, mock_config):
        """Verify that the main data directory is created."""
        from setup_data_dirs import main
        import utils.config

        root = utils.config.get_project_root()
        main()

        data_root = root / "data"
        assert data_root.exists()
        assert data_root.is_dir()