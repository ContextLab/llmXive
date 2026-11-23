import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Adjust path for import if running from tests/
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from setup_directories import create_directories, verify_directories, REQUIRED_DIRS
from utils.exceptions import DataInsufficientError

class TestSetupDirectories:
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to simulate project root."""
        tmp_dir = tempfile.mkdtemp()
        yield Path(tmp_dir)
        shutil.rmtree(tmp_dir)

    def test_create_directories_creates_all(self, temp_project_root):
        """Test that create_directories actually creates the folder structure."""
        results = create_directories(temp_project_root)
        
        assert len(results) == len(REQUIRED_DIRS)
        
        for item in results:
            assert "path" in item
            assert "created_at" in item
            assert Path(item["path"]).exists()
            assert Path(item["path"]).is_dir()

    def test_verify_directories_passes(self, temp_project_root):
        """Test verification passes when dirs exist."""
        created = create_directories(temp_project_root)
        assert verify_directories(temp_project_root, created) is True

    def test_verify_directories_fails_on_missing(self, temp_project_root):
        """Test verification fails if a directory is missing."""
        created = create_directories(temp_project_root)
        
        # Manually remove one to simulate failure
        missing_path = Path(created[0]["path"])
        shutil.rmtree(missing_path)
        
        assert verify_directories(temp_project_root, created) is False

    def test_output_json_structure(self, temp_project_root):
        """Test that the JSON output format matches specification."""
        results = create_directories(temp_project_root)
        
        for item in results:
            assert isinstance(item, dict)
            assert isinstance(item["path"], str)
            assert isinstance(item["created_at"], str)
            # Basic ISO8601 check (contains T)
            assert "T" in item["created_at"]

    def test_all_required_dirs_present(self, temp_project_root):
        """Ensure the list of required dirs includes the critical ones from T001."""
        expected_subdirs = [
            "code", "data", "data/raw", "data/processed", "data/logs",
            "state", "contracts", "config", "code/data", "code/models",
            "code/utils", "code/tests"
        ]
        
        for expected in expected_subdirs:
            assert expected in REQUIRED_DIRS, f"Missing required dir: {expected}"