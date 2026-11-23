"""
Integration tests for data acquisition checksum functionality (T012).

Verifies that:
1. Checksums are computed correctly for downloaded files
2. Checksums are written atomically to the state file
3. The state file contains the correct artifact_hashes map
"""
import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_acquisition import (
    compute_file_checksum,
    write_checksum_to_state,
    get_collected_checksums,
    reset_checksums,
    PROJECT_ID,
    STATE_FILE
)
from src.config import get_project_root


class TestDataAcquisitionChecksum:
    """Test suite for checksum functionality in data acquisition."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Set up test environment before each test."""
        # Store original project root
        self.original_root = os.environ.get('PROJECT_ROOT')
        
        # Set up temporary project structure
        test_root = tmp_path / "test_project"
        test_root.mkdir(parents=True)
        
        # Create necessary directories
        (test_root / "state" / "projects").mkdir(parents=True)
        (test_root / "data" / "raw").mkdir(parents=True)
        (test_root / "data" / "processed").mkdir(parents=True)
        
        # Set environment variable for test
        os.environ['PROJECT_ROOT'] = str(test_root)
        
        # Create initial state file
        state_path = test_root / "state" / "projects" / f"{PROJECT_ID}.yaml"
        initial_state = {
            "project_id": PROJECT_ID,
            "artifact_hashes": {}
        }
        with open(state_path, 'w') as f:
            yaml.dump(initial_state, f)
        
        yield test_root
        
        # Restore original project root
        if self.original_root:
            os.environ['PROJECT_ROOT'] = self.original_root
        elif 'PROJECT_ROOT' in os.environ:
            del os.environ['PROJECT_ROOT']
    
    def test_compute_file_checksum_valid_file(self, setup_teardown):
        """Test that checksum is computed correctly for a valid file."""
        test_root = setup_teardown
        
        # Create a test file with known content
        test_file = test_root / "data" / "raw" / "test_file.txt"
        test_content = b"Hello, World! This is test content."
        test_file.write_bytes(test_content)
        
        # Compute checksum
        checksum = compute_file_checksum(test_file)
        
        # Verify checksum
        expected_hash = hashlib.sha256(test_content).hexdigest()
        assert checksum == expected_hash, f"Checksum mismatch: {checksum} != {expected_hash}"
    
    def test_compute_file_checksum_missing_file(self, setup_teardown):
        """Test that FileNotFoundError is raised for missing file."""
        test_root = setup_teardown
        
        missing_file = test_root / "nonexistent" / "file.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(missing_file)
    
    def test_write_checksum_to_state(self, setup_teardown):
        """Test that checksum is written to state file correctly."""
        test_root = setup_teardown
        
        # Create a test file
        test_file = test_root / "data" / "raw" / "test_data.csv"
        test_content = b"sample,data\n1,2\n3,4"
        test_file.write_bytes(test_content)
        
        # Write checksum to state
        write_checksum_to_state(test_file, source="real")
        
        # Read state file and verify
        state_path = test_root / "state" / "projects" / f"{PROJECT_ID}.yaml"
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f)
        
        assert 'artifact_hashes' in state_data, "artifact_hashes not found in state file"
        
        relative_path = str(test_file.relative_to(test_root))
        assert relative_path in state_data['artifact_hashes'], f"{relative_path} not in artifact_hashes"
        
        hash_info = state_data['artifact_hashes'][relative_path]
        assert 'hash' in hash_info, "hash not found in artifact_hashes entry"
        assert 'source' in hash_info, "source not found in artifact_hashes entry"
        assert hash_info['source'] == 'real', f"Expected source 'real', got {hash_info['source']}"
        
        # Verify the hash is correct
        expected_hash = hashlib.sha256(test_content).hexdigest()
        assert hash_info['hash'] == expected_hash, f"Hash mismatch: {hash_info['hash']} != {expected_hash}"
    
    def test_reset_checksums(self, setup_teardown):
        """Test that reset_checksums clears all artifact_hashes."""
        test_root = setup_teardown
        
        # Add some dummy checksums
        state_path = test_root / "state" / "projects" / f"{PROJECT_ID}.yaml"
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f)
        state_data['artifact_hashes'] = {
            "file1.csv": {"hash": "abc123", "source": "real"},
            "file2.csv": {"hash": "def456", "source": "real"}
        }
        with open(state_path, 'w') as f:
            yaml.dump(state_data, f)
        
        # Reset checksums
        reset_checksums()
        
        # Verify checksums are cleared
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f)
        
        assert 'artifact_hashes' in state_data
        assert len(state_data['artifact_hashes']) == 0, "artifact_hashes not cleared after reset"
    
    def test_get_collected_checksums(self, setup_teardown):
        """Test that get_collected_checksums returns correct data."""
        test_root = setup_teardown
        
        # Create test files and write checksums
        test_file1 = test_root / "data" / "raw" / "file1.csv"
        test_file1.write_bytes(b"test1")
        write_checksum_to_state(test_file1, source="real")
        
        test_file2 = test_root / "data" / "raw" / "file2.csv"
        test_file2.write_bytes(b"test2")
        write_checksum_to_state(test_file2, source="real")
        
        # Get checksums
        checksums = get_collected_checksums()
        
        # Verify
        assert len(checksums) == 2, f"Expected 2 checksums, got {len(checksums)}"
        
        relative_path1 = str(test_file1.relative_to(test_root))
        relative_path2 = str(test_file2.relative_to(test_root))
        
        assert relative_path1 in checksums
        assert relative_path2 in checksums
        assert checksums[relative_path1]['source'] == 'real'
        assert checksums[relative_path2]['source'] == 'real'
    
    def test_atomic_write_checksum(self, setup_teardown):
        """Test that checksum writes are atomic (no partial state)."""
        test_root = setup_teardown
        
        # Create test file
        test_file = test_root / "data" / "raw" / "atomic_test.csv"
        test_file.write_bytes(b"atomic test data")
        
        # Write checksum
        write_checksum_to_state(test_file, source="real")
        
        # Verify state file is valid YAML
        state_path = test_root / "state" / "projects" / f"{PROJECT_ID}.yaml"
        try:
            with open(state_path, 'r') as f:
                state_data = yaml.safe_load(f)
            assert state_data is not None, "State file is corrupted or invalid"
            assert 'artifact_hashes' in state_data
        except yaml.YAMLError as e:
            pytest.fail(f"State file is not valid YAML after atomic write: {e}")
    
    def test_checksum_persistence_across_calls(self, setup_teardown):
        """Test that checksums persist across multiple function calls."""
        test_root = setup_teardown
        
        # Create and checksum first file
        test_file1 = test_root / "data" / "raw" / "persistent1.csv"
        test_file1.write_bytes(b"persistent data 1")
        write_checksum_to_state(test_file1, source="real")
        
        # Create and checksum second file
        test_file2 = test_root / "data" / "raw" / "persistent2.csv"
        test_file2.write_bytes(b"persistent data 2")
        write_checksum_to_state(test_file2, source="real")
        
        # Get all checksums
        checksums = get_collected_checksums()
        
        # Verify both are present
        assert len(checksums) == 2
        
        relative_path1 = str(test_file1.relative_to(test_root))
        relative_path2 = str(test_file2.relative_to(test_root))
        
        assert relative_path1 in checksums
        assert relative_path2 in checksums