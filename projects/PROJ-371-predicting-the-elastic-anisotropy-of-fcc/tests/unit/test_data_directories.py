import os
import pytest
from pathlib import Path

from src.utils.config import get_path

class TestDataDirectories:
    """Verify that required data directories exist as per T007."""

    def test_data_raw_directory_exists(self):
        """Verify data/raw directory exists."""
        raw_path = get_path("data_raw")
        assert raw_path.exists(), f"Directory {raw_path} does not exist"
        assert raw_path.is_dir(), f"{raw_path} is not a directory"

    def test_data_processed_directory_exists(self):
        """Verify data/processed directory exists."""
        processed_path = get_path("data_processed")
        assert processed_path.exists(), f"Directory {processed_path} does not exist"
        assert processed_path.is_dir(), f"{processed_path} is not a directory"

    def test_gitkeep_files_exist_in_data_dirs(self):
        """Verify .gitkeep files exist to ensure directories are tracked in git."""
        raw_path = get_path("data_raw")
        processed_path = get_path("data_processed")

        assert (raw_path / ".gitkeep").exists(), f".gitkeep missing in {raw_path}"
        assert (processed_path / ".gitkeep").exists(), f".gitkeep missing in {processed_path}"