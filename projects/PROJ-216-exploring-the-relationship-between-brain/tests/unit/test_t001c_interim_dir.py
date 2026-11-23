import os
import sys
from pathlib import Path
import pytest

# Ensure code path is accessible
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from setup_directories import create_directories

class TestT001cInterimDir:
    """
    Tests for Task T001c: Create directory data/interim and verify existence.
    """

    def test_interim_directory_exists(self):
        """Verify that data/interim exists after setup."""
        base = project_root
        interim_path = base / "data" / "interim"
        assert interim_path.exists(), f"Directory {interim_path} does not exist"
        assert interim_path.is_dir(), f"{interim_path} exists but is not a directory"

    def test_create_directories_function(self):
        """Test the create_directories helper function."""
        test_dir = project_root / "data" / "test_tmp_interim"
        try:
            # Clean up if exists
            if test_dir.exists():
                import shutil
                shutil.rmtree(test_dir)

            created = create_directories([test_dir])
            assert len(created) == 1
            assert test_dir.exists()
            assert test_dir.is_dir()
        finally:
            # Cleanup
            if test_dir.exists():
                import shutil
                shutil.rmtree(test_dir)

    def test_parent_data_directory_exists(self):
        """Verify that the parent data directory exists."""
        base = project_root
        data_path = base / "data"
        assert data_path.exists(), "Parent data directory does not exist"
        assert data_path.is_dir(), "Parent data path is not a directory"
