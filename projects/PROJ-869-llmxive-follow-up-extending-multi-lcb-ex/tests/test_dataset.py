"""
Tests for dataset loading and checksum verification.
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import hashlib
import os
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.dataset import load_multi_lcb_dataset, verify_checksum, save_dataset_with_checksum
from code.utils.checksum_tracker import load_registry

class TestDatasetLoading:
    def test_load_multi_lcb_real_data(self):
        """
        Test that we can load the real Multi-LCB dataset from HuggingFace.
        This test requires internet access and the real dataset to exist.
        """
        # We only run this if the dataset is actually available to avoid flaky CI failures
        # In a real run, this would fetch the data.
        try:
            df = load_multi_lcb_dataset(split="test")
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0, "Dataset should not be empty"
            # Check for essential columns as defined in load_multi_lcb_dataset
            assert 'problem' in df.columns
            assert 'solution' in df.columns
            assert 'language' in df.columns
            assert 'difficulty' in df.columns
            assert 'test_cases' in df.columns
        except RuntimeError as e:
            # If the real dataset is unavailable (e.g. network, HF down), 
            # we mark the test as skipped rather than failed to allow local dev without internet
            # But in the context of the "Real data only" rule, if the script runs, it MUST fail loudly.
            # Here in a unit test, we might skip if the environment is not set up for HF.
            pytest.skip(f"Real dataset unavailable (expected in isolated env): {e}")

    def test_verify_checksum_valid(self, tmp_path):
        """Test checksum verification with a valid file."""
        test_file = tmp_path / "test.parquet"
        test_file.write_text("dummy data")
        
        # Compute real checksum
        sha256_hash = hashlib.sha256()
        with open(test_file, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        expected = sha256_hash.hexdigest()
        
        assert verify_checksum(test_file, expected) is True

    def test_verify_checksum_invalid(self, tmp_path):
        """Test checksum verification with an invalid checksum."""
        test_file = tmp_path / "test.parquet"
        test_file.write_text("dummy data")
        
        assert verify_checksum(test_file, "invalid_checksum") is False

    def test_verify_checksum_missing_file(self, tmp_path):
        """Test checksum verification on a missing file."""
        missing_file = tmp_path / "nonexistent.parquet"
        assert verify_checksum(missing_file, "any_checksum") is False

class TestChecksumRegistration:
    def test_save_and_register(self, tmp_path):
        """Test saving a dataframe and registering its checksum."""
        # Create a dummy dataframe
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        
        # Temporarily override DATA_RAW_DIR for the test
        from code import dataset
        original_dir = dataset.DATA_RAW_DIR
        dataset.DATA_RAW_DIR = tmp_path
        
        try:
            output_path = save_dataset_with_checksum(df, "test_save.parquet")
            
            assert output_path.exists()
            assert output_path.suffix == ".parquet"
            
            # Check registry
            registry = load_registry()
            assert str(output_path) in registry or any(p.endswith("test_save.parquet") for p in registry.keys())
        finally:
            dataset.DATA_RAW_DIR = original_dir
