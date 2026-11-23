"""
Unit tests for the Hashing Utility (Task T006).
"""
import os
import tempfile
import pytest
from pathlib import Path
import yaml

# Import the module under test
from code.utils.hashing import (
    calculate_checksum,
    update_state_file,
    load_state_file,
    verify_artifact,
    STATE_FILE
)
from code.config import get_path


class TestHashingUtility:
    """Tests for checksum calculation and state management."""

    def setup_method(self):
        """Set up test fixtures."""
        # Ensure state directory exists
        get_path("state").mkdir(parents=True, exist_ok=True)
        # Clear state file before each test to ensure isolation
        state_path = get_path(STATE_FILE)
        if state_path.exists():
            state_path.unlink()

    def teardown_method(self):
        """Clean up after tests."""
        # Optional: Clean up state file if desired for test isolation
        pass

    def test_calculate_checksum_file_exists(self):
        """Test that calculate_checksum returns a valid hash for an existing file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            checksum = calculate_checksum(temp_path)
            assert len(checksum) == 64  # SHA-256 hex digest length
            assert all(c in '0123456789abcdef' for c in checksum)
        finally:
            os.unlink(temp_path)

    def test_calculate_checksum_file_not_found(self):
        """Test that calculate_checksum raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_checksum("non_existent_file_12345.txt")

    def test_update_state_file(self):
        """Test that update_state_file correctly writes to state/artifact_hashes.yaml."""
        # Create a dummy file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("id,value\n")
            temp_path = f.name

        try:
            checksum = calculate_checksum(temp_path)
            update_state_file(temp_path, checksum)

            # Verify state file exists
            state_path = get_path(STATE_FILE)
            assert state_path.exists()

            # Verify content
            state = load_state_file()
            assert "artifact_hashes" in state
            
            key = os.path.basename(temp_path)
            assert key in state["artifact_hashes"]
            assert state["artifact_hashes"][key]["checksum"] == checksum
            assert state["artifact_hashes"][key]["source_path"] == temp_path
        finally:
            os.unlink(temp_path)

    def test_verify_artifact_match(self):
        """Test verify_artifact returns True when checksum matches."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("test data")
            temp_path = f.name

        try:
            checksum = calculate_checksum(temp_path)
            update_state_file(temp_path, checksum)
            
            # Verify against stored checksum
            assert verify_artifact(temp_path) is True
            
            # Verify against explicit checksum
            assert verify_artifact(temp_path, expected_checksum=checksum) is True
        finally:
            os.unlink(temp_path)

    def test_verify_artifact_mismatch(self):
        """Test verify_artifact returns False when checksum mismatches."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("test data")
            temp_path = f.name

        try:
            update_state_file(temp_path, "wrong_checksum_1234567890abcdef")
            
            assert verify_artifact(temp_path) is False
        finally:
            os.unlink(temp_path)

    def test_verify_artifact_missing_stored(self):
        """Test verify_artifact raises error if no stored checksum exists."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("test data")
            temp_path = f.name

        try:
            with pytest.raises(FileNotFoundError):
                verify_artifact(temp_path)
        finally:
            os.unlink(temp_path)

    def test_update_state_file_overwrites(self):
        """Test that updating a file twice overwrites the previous entry."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("version 1")
            temp_path = f.name

        try:
            checksum1 = calculate_checksum(temp_path)
            update_state_file(temp_path, checksum1)
            
            # Update file content
            with open(temp_path, 'w') as f:
                f.write("version 2")
            checksum2 = calculate_checksum(temp_path)
            update_state_file(temp_path, checksum2)
            
            state = load_state_file()
            key = os.path.basename(temp_path)
            assert state["artifact_hashes"][key]["checksum"] == checksum2
        finally:
            os.unlink(temp_path)
