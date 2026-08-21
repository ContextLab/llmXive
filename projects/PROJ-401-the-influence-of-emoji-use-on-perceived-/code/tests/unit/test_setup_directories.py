import pytest
import tempfile
import os
from pathlib import Path
import shutil
from src.utils.io import ensure_directory

class TestSetupDirectories:
    """Tests for verifying directory structure creation (Task T008)."""

    def test_create_data_directories(self, tmp_path):
        """Verify that data/raw, data/processed, and state directories are created."""
        # Setup: Change to a temporary directory to simulate project root
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Define the required paths relative to the temp directory
            data_raw = Path("data/raw")
            data_processed = Path("data/processed")
            state_dir = Path("state")

            # Ensure directories exist using the project utility
            ensure_directory(data_raw)
            ensure_directory(data_processed)
            ensure_directory(state_dir)

            # Assertions: Verify directories exist on disk
            assert data_raw.exists(), f"Directory {data_raw} was not created."
            assert data_raw.is_dir(), f"{data_raw} exists but is not a directory."

            assert data_processed.exists(), f"Directory {data_processed} was not created."
            assert data_processed.is_dir(), f"{data_processed} exists but is not a directory."

            assert state_dir.exists(), f"Directory {state_dir} was not created."
            assert state_dir.is_dir(), f"{state_dir} exists but is not a directory."

        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def test_nested_directory_creation(self, tmp_path):
        """Verify that nested directories are created if parent doesn't exist."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Create a deeply nested path
            nested_path = Path("data/processed/features/emoji_stats")
            ensure_directory(nested_path)

            assert nested_path.exists(), f"Nested directory {nested_path} was not created."
            assert nested_path.is_dir(), f"{nested_path} exists but is not a directory."
        finally:
            os.chdir(original_cwd)

    def test_idempotent_directory_creation(self, tmp_path):
        """Verify that calling ensure_directory on an existing path does not fail."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            target = Path("data/raw")
            ensure_directory(target)
            
            # Call again; should not raise
            ensure_directory(target)
            
            assert target.exists()
        finally:
            os.chdir(original_cwd)
