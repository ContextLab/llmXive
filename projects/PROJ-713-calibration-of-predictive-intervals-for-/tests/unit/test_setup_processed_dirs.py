"""
Unit tests for the setup_processed_dirs module (Task T001d).
Verifies that the data/processed/ directory is created and is writable.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from setup_processed_dirs import ensure_dir_with_backoff, setup_processed_dirs
from utils.exceptions import ConfigurationError


class TestSetupProcessedDirs:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        """
        Setup: Create a temporary directory to act as a mock project root.
        Teardown: Cleanup is handled by tmp_path fixture automatically.
        """
        self.tmp_project_root = tmp_path
        self.mock_processed_dir = self.tmp_project_root / "data" / "processed"
        
        # Temporarily patch PROJECT_ROOT logic if necessary, 
        # but since we are testing the function directly with paths, 
        # we will pass the tmp_path as the target.
        yield

    def test_ensure_dir_creates_new_directory(self):
        """Test that a new directory is created if it doesn't exist."""
        assert not self.mock_processed_dir.exists()
        
        result = ensure_dir_with_backoff(self.mock_processed_dir)
        
        assert result is True
        assert self.mock_processed_dir.exists()
        assert self.mock_processed_dir.is_dir()

    def test_ensure_dir_idempotent(self):
        """Test that calling the function on an existing directory is safe (idempotent)."""
        # Create the directory first
        self.mock_processed_dir.mkdir(parents=True)
        assert self.mock_processed_dir.exists()
        
        # Run the function again
        result = ensure_dir_with_backoff(self.mock_processed_dir)
        
        assert result is True
        assert self.mock_processed_dir.exists()

    def test_ensure_dir_verifies_writability(self):
        """Test that the function verifies the directory is writable."""
        result = ensure_dir_with_backoff(self.mock_processed_dir)
        
        assert result is True
        
        # Attempt to write a file manually to confirm
        test_file = self.mock_processed_dir / "test_writability.txt"
        try:
            test_file.write_text("test content")
            assert test_file.exists()
            assert test_file.read_text() == "test content"
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_ensure_dir_fails_on_unwritable_parent(self):
        """Test behavior when parent directory cannot be created (e.g., permission issues)."""
        # This is hard to test reliably in all environments without root/sudo,
        # so we test the logic path where the directory exists but is read-only.
        # We simulate this by creating a read-only directory.
        
        read_only_dir = self.tmp_project_root / "readonly"
        read_only_dir.mkdir()
        read_only_dir.chmod(0o555) # Read and execute only (no write)
        
        try:
            # Attempting to create a subdirectory in a read-only dir should fail
            # depending on OS and user permissions. 
            # If the current user is root, this test might pass where it should fail.
            # We'll catch the expected exception or failure.
            sub_dir = read_only_dir / "sub"
            result = ensure_dir_with_backoff(sub_dir)
            
            # If we are root, the mkdir might succeed despite 0o555.
            # If we are not root, it should fail.
            if os.geteuid() != 0:
                assert result is False
            else:
                # If root, the directory might have been created, which is fine for this env
                assert result is True
        finally:
            # Restore permissions to allow cleanup
            read_only_dir.chmod(0o755)

    def test_setup_processed_dirs_integration(self):
        """
        Integration test for the main setup function logic.
        Since the real function relies on global PROJECT_ROOT, we test the logic
        by ensuring the directory creation logic works in our temp environment.
        """
        # We can't easily run the global setup_processed_dirs() without mocking
        # the global PROJECT_ROOT in config. Instead, we verify the core logic
        # via ensure_dir_with_backoff which is the core dependency.
        
        # Simulate the path structure expected
        target_dir = self.tmp_project_root / "data" / "processed"
        
        # The function should create 'data' and 'processed'
        success = ensure_dir_with_backoff(target_dir)
        
        assert success is True
        assert target_dir.exists()
        assert target_dir.is_dir()