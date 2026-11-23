import os
import sys
import pytest
from pathlib import Path

# Add code to path if running from tests/
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_project_structure import DIRECTORIES, setup_directories, verify_directory_structure

class TestProjectStructure:
    
    def test_directories_defined(self):
        """Ensure the list of required directories is populated."""
        assert len(DIRECTORIES) > 0
        assert "data/raw" in DIRECTORIES
        assert "code/ingestion" in DIRECTORIES
        assert "tests/contract" in DIRECTORIES

    def test_setup_creates_directories(self, tmp_path):
        """Test that setup_directories actually creates the folders."""
        # tmp_path is a unique temporary directory provided by pytest
        created = setup_directories(tmp_path)
        
        assert len(created) > 0
        
        # Verify each created path actually exists on disk
        for path_str in created:
            full_path = Path(path_str)
            assert full_path.exists(), f"Directory {path_str} was reported created but does not exist."
            assert full_path.is_dir(), f"Path {path_str} exists but is not a directory."

    def test_verify_passes_after_setup(self, tmp_path):
        """Test that verify_directory_structure returns success after setup."""
        setup_directories(tmp_path)
        result = verify_directory_structure(tmp_path)
        
        assert result["success"] is True
        assert len(result["missing"]) == 0
        assert result["verified_count"] == result["checked_count"]

    def test_verify_fails_on_missing(self, tmp_path):
        """Test that verify_directory_structure detects missing directories."""
        # Do NOT run setup, just verify on empty tmp_path
        result = verify_directory_structure(tmp_path)
        
        assert result["success"] is False
        assert len(result["missing"]) > 0
        # Ensure we are checking the specific expected paths
        assert "data/raw" in result["missing"]
        assert "code/ingestion" in result["missing"]
