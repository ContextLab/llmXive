import os
import sys
from pathlib import Path
import pytest

# Add project root to path for imports if running from tests/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.setup_data_dirs import DATA_DIRS

class TestDataStructure:
    """
    Contract test to verify that the required data directory structure
    (data/raw, data/processed, data/models) exists as per T007.
    """

    @pytest.fixture
    def project_root(self):
        return Path(__file__).resolve().parent.parent.parent

    def test_required_directories_exist(self, project_root):
        """
        Verify that all directories defined in DATA_DIRS exist.
        """
        for dir_name in DATA_DIRS:
            full_path = project_root / dir_name
            assert full_path.exists(), f"Required directory missing: {full_path}"
            assert full_path.is_dir(), f"Path is not a directory: {full_path}"

    def test_data_raw_directory(self, project_root):
        """
        Specific check for data/raw directory.
        """
        path = project_root / "data/raw"
        assert path.exists() and path.is_dir(), "data/raw directory must exist"

    def test_data_processed_directory(self, project_root):
        """
        Specific check for data/processed directory.
        """
        path = project_root / "data/processed"
        assert path.exists() and path.is_dir(), "data/processed directory must exist"

    def test_data_models_directory(self, project_root):
        """
        Specific check for data/models directory.
        """
        path = project_root / "data/models"
        assert path.exists() and path.is_dir(), "data/models directory must exist"