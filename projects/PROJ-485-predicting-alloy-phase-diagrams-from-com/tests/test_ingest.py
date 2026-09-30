"""
Tests for data ingestion module.
Includes test for T061: Data Integrity Checksum Verification.
"""
import os
import sys
import json
import tempfile
import shutil
import pytest
import pandas as pd
import yaml

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.ingest.load_data import (
    compute_dataset_checksum, 
    verify_processed_data_integrity,
    compute_file_sha256
)
from code.utils.error_codes import ErrorCode

class TestDataIntegrityChecksum:
    """Tests for T061: Data Integrity Checksum Verification."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.state_dir = os.path.join(self.test_dir, 'state', 'PROJ-485')
        os.makedirs(self.state_dir, exist_ok=True)
        
        # Create a test CSV file
        self.test_csv_path = os.path.join(self.test_dir, 'test_descriptors.csv')
        test_data = {
            'element_a': ['Cu', 'Al', 'Fe'],
            'element_b': ['Zn', 'Cu', 'C'],
            'temperature': [1000.0, 900.0, 1500.0],
            'composition': [0.5, 0.3, 0.7]
        }
        self.df = pd.DataFrame(test_data)
        self.df.to_csv(self.test_csv_path, index=False)
        
        # Compute expected checksum
        self.expected_checksum = compute_file_sha256(self.test_csv_path)
        
        # Create initial state file
        self.state_path = os.path.join(self.state_dir, 'pipeline_state.yaml')
        self.state = {
            'artifacts': {
                'test_descriptors.csv': {
                    'checksum': self.expected_checksum,
                    'updated_at': '2024-01-01T00:00:00Z'
                }
            }
        }
        with open(self.state_path, 'w') as f:
            yaml.dump(self.state, f)

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_checksum_verification_passes(self):
        """Test that verification passes when checksums match."""
        result = verify_processed_data_integrity(self.test_csv_path, self.expected_checksum)
        assert result is True

    def test_checksum_verification_fails_on_mismatch(self):
        """Test that verification fails when checksums don't match."""
        wrong_checksum = "0" * 64  # Invalid checksum
        
        with pytest.raises(ValueError) as exc_info:
            verify_processed_data_integrity(self.test_csv_path, wrong_checksum)
        
        assert "DATA_INTEGRITY_VIOLATION" in str(exc_info.value)
        assert "Checksum mismatch" in str(exc_info.value)

    def test_checksum_verification_fails_on_missing_file(self):
        """Test that verification fails when file doesn't exist."""
        non_existent_path = os.path.join(self.test_dir, 'non_existent.csv')
        
        with pytest.raises(ValueError) as exc_info:
            verify_processed_data_integrity(non_existent_path, self.expected_checksum)
        
        assert "DATA_INTEGRITY_VIOLATION" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_checksum_computation_consistency(self):
        """Test that checksum computation is consistent."""
        checksum1 = compute_file_sha256(self.test_csv_path)
        checksum2 = compute_file_sha256(self.test_csv_path)
        assert checksum1 == checksum2

    def test_corrupted_file_detection(self):
        """Test that corrupted file is detected by checksum mismatch."""
        # Corrupt the file
        with open(self.test_csv_path, 'a') as f:
            f.write("\nCORRUPTED_ROW,1,2,3")
        
        # Recompute checksum - should be different
        new_checksum = compute_file_sha256(self.test_csv_path)
        assert new_checksum != self.expected_checksum
        
        # Verify should fail
        with pytest.raises(ValueError) as exc_info:
            verify_processed_data_integrity(self.test_csv_path, self.expected_checksum)
        
        assert "DATA_INTEGRITY_VIOLATION" in str(exc_info.value)

    def test_integration_with_state_file(self):
        """Test integration with state file checksum verification."""
        # Load state and verify checksum
        with open(self.state_path, 'r') as f:
            state = yaml.safe_load(f)
        
        expected_checksum = state['artifacts']['test_descriptors.csv']['checksum']
        
        # Verify should pass
        result = verify_processed_data_integrity(self.test_csv_path, expected_checksum)
        assert result is True

    def test_large_file_checksum(self):
        """Test checksum computation on a larger file."""
        # Create a larger test file
        large_data_path = os.path.join(self.test_dir, 'large_test.csv')
        large_df = pd.DataFrame({
            'col1': range(10000),
            'col2': range(10000, 20000),
            'col3': ['test'] * 10000
        })
        large_df.to_csv(large_data_path, index=False)
        
        checksum = compute_file_sha256(large_data_path)
        assert len(checksum) == 64  # SHA-256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_empty_file_checksum(self):
        """Test checksum computation on an empty file."""
        empty_path = os.path.join(self.test_dir, 'empty.csv')
        with open(empty_path, 'w') as f:
            pass  # Create empty file
        
        checksum = compute_file_sha256(empty_path)
        assert len(checksum) == 64

    def test_binary_file_checksum(self):
        """Test checksum computation on a binary file."""
        binary_path = os.path.join(self.test_dir, 'binary.bin')
        with open(binary_path, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\x04\x05')
        
        checksum = compute_file_sha256(binary_path)
        assert len(checksum) == 64
        assert checksum != self.expected_checksum  # Different content should have different checksum

if __name__ == '__main__':
    pytest.main([__file__, '-v'])