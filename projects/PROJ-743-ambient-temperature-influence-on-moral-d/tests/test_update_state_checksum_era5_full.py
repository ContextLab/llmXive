"""
Unit tests for T002d: update_state_checksum_era5_full.py

Tests verify that:
1. The checksum is computed correctly for a known file.
2. The state file is updated with the correct checksum and timestamp.
3. The script handles missing files appropriately.
"""
import os
import sys
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import yaml
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from update_state_checksum_era5_full import compute_sha256, update_state_file

class TestComputeSha256:
    def test_compute_sha256_known_file(self):
        """Test checksum computation against a known file."""
        # Create a temporary file with known content
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_path = Path(f.name)
        
        try:
            # Compute expected checksum manually
            expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
            
            # Compute using function
            actual_hash = compute_sha256(temp_path)
            
            assert actual_hash == expected_hash
        finally:
            # Cleanup
            temp_path.unlink()

    def test_compute_sha256_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            compute_sha256(Path("/nonexistent/file.txt"))

class TestUpdateStateFile:
    def test_update_state_file_creates_new(self):
        """Test creating a new state file with checksum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "state.yaml"
            checksum = "test_checksum_123"
            
            # Call function
            # We need to mock the global STATE_FILE_PATH for testing
            import update_state_checksum_era5_full as module
            original_path = module.STATE_FILE_PATH
            module.STATE_FILE_PATH = state_path
            
            try:
                update_state_file(checksum)
                
                # Verify file was created
                assert state_path.exists()
                
                # Verify content
                with open(state_path, 'r') as f:
                    data = yaml.safe_load(f)
                
                assert data["artifact_hashes"]["era5_full"] == checksum
                assert "updated_at" in data
            finally:
                # Restore original path
                module.STATE_FILE_PATH = original_path

    def test_update_state_file_updates_existing(self):
        """Test updating an existing state file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "state.yaml"
            
            # Create initial state file
            initial_data = {
                "project_id": "test-project",
                "updated_at": "2023-01-01T00:00:00+00:00",
                "artifact_hashes": {
                    "old_file": "old_checksum"
                }
            }
            with open(state_path, 'w') as f:
                yaml.dump(initial_data, f)
            
            new_checksum = "new_checksum_456"
            
            import update_state_checksum_era5_full as module
            original_path = module.STATE_FILE_PATH
            module.STATE_FILE_PATH = state_path
            
            try:
                update_state_file(new_checksum)
                
                # Verify content
                with open(state_path, 'r') as f:
                    data = yaml.safe_load(f)
                
                assert data["artifact_hashes"]["era5_full"] == new_checksum
                assert data["artifact_hashes"]["old_file"] == "old_checksum"
                assert data["updated_at"] != "2023-01-01T00:00:00+00:00"
            finally:
                module.STATE_FILE_PATH = original_path

class TestIntegration:
    def test_full_workflow(self):
        """Test the complete workflow of computing and updating checksum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test_data.h5"
            test_content = b"test data for checksum"
            with open(test_file, 'wb') as f:
                f.write(test_content)
            
            expected_checksum = hashlib.sha256(test_content).hexdigest()
            
            # Compute checksum
            actual_checksum = compute_sha256(test_file)
            assert actual_checksum == expected_checksum
            
            # Update state file
            state_path = Path(tmpdir) / "state.yaml"
            import update_state_checksum_era5_full as module
            original_path = module.STATE_FILE_PATH
            module.STATE_FILE_PATH = state_path
            
            try:
                update_state_file(actual_checksum)
                
                # Verify state file
                with open(state_path, 'r') as f:
                    data = yaml.safe_load(f)
                
                assert data["artifact_hashes"]["era5_full"] == actual_checksum
                assert "updated_at" in data
                
                # Verify timestamp is recent
                updated_at = datetime.fromisoformat(data["updated_at"])
                now = datetime.now(timezone.utc)
                # Allow 1 minute difference for execution time
                assert abs((now - updated_at).total_seconds()) < 60
            finally:
                module.STATE_FILE_PATH = original_path
