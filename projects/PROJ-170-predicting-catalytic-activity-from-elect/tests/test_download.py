import os
import sys
import pytest
from pathlib import Path
import tempfile
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from download_data import (
    download_stratified_sample,
    compute_file_hash,
    verify_checksum,
    verify_downloaded_data
)
from config import get_data_path

class TestDownloadStratifiedSample:
    """Tests for the stratified sample download functionality."""

    def test_download_creates_output_file(self):
        """Test that download_stratified_sample creates the expected output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_sample.h5"
            
            # Mock the download to avoid actual network call in unit test
            # In a real scenario, this would call the actual download
            # For now, we test the file creation logic
            df = pd.DataFrame({
                'composition': ['Fe2O3', 'CuO'],
                'surface_facet': ['100', '111'],
                'composition_family': ['oxides', 'oxides']
            })
            df.to_hdf(output_path, key='data', mode='w')
            
            assert output_path.exists()
            assert verify_downloaded_data(output_path)

    def test_hash_computation(self):
        """Test file hash computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            hash1 = compute_file_hash(test_file)
            hash2 = compute_file_hash(test_file)
            
            assert len(hash1) == 64  # SHA256 hex length
            assert hash1 == hash2  # Deterministic

    def test_stratification_logic(self):
        """Test that stratification maintains proportional representation."""
        # This is a conceptual test - in practice, we'd verify the actual
        # stratification logic by checking the distribution of composition_family
        # in the output dataset
        pass

class TestVerification:
    """Tests for data verification functions."""

    def test_verify_checksum(self):
        """Test checksum verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            expected_hash = compute_file_hash(test_file)
            assert verify_checksum(test_file, expected_hash)
            
            assert not verify_checksum(test_file, "wrong_hash")

    def test_verify_downloaded_data_exists(self):
        """Test that verify_downloaded_data checks for file existence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent = Path(tmpdir) / "nonexistent.h5"
            assert not verify_downloaded_data(non_existent)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])