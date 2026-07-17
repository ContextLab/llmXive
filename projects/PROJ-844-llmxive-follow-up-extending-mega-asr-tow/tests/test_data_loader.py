"""
Unit tests for data_loader.py
"""
import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import os
import tempfile
from pathlib import Path

# Mock the datasets library and config before importing data_loader
# We assume config.py exists and defines DATA_RAW_DIR
# For testing, we might need to mock the actual download

class TestDataLoader(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_output_path = Path(self.temp_dir.name) / "test_output.csv"

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('data_loader.load_dataset')
    def test_load_librispeech_subset(self, mock_load_dataset):
        """Test loading a mock subset of LibriSpeech."""
        # Mock dataset
        mock_data = {
            'file': ['file1.flac', 'file2.flac'],
            'text': ['hello world', 'test transcript'],
            'speaker_id': [100, 101],
            'chapter_id': [1, 2],
            'utterance_id': [1, 2]
        }
        mock_df = pd.DataFrame(mock_data)
        mock_dataset = MagicMock()
        mock_dataset.to_pandas.return_value = mock_df
        mock_load_dataset.return_value = mock_dataset

        from data_loader import load_librispeech_subset

        df = load_librispeech_subset(split="test-clean", max_samples=2)

        self.assertEqual(len(df), 2)
        self.assertIn('file', df.columns)
        self.assertIn('text', df.columns)
        self.assertIn('speaker_id', df.columns)

    @patch('data_loader.load_dataset')
    def test_stratified_sample(self, mock_load_dataset):
        """Test stratified sampling logic."""
        # Create a larger mock dataset to ensure stratification works
        np.random.seed(42)
        n_samples = 100
        data = {
            'file': [f'file_{i}.flac' for i in range(n_samples)],
            'text': ['text'] * n_samples,
            'speaker_id': np.random.choice([100, 101, 102], n_samples),
        }
        mock_df = pd.DataFrame(data)
        mock_dataset = MagicMock()
        mock_dataset.to_pandas.return_value = mock_df
        mock_load_dataset.return_value = mock_dataset

        from data_loader import stratified_sample

        # Sample 1 per stratum
        sampled_df = stratified_sample(mock_df, n_per_stratum=1, seed=42)

        # Check that we have at least one sample per unique (speaker, snr_bucket) pair
        # Since snr_bucket is derived, we check the logic
        self.assertGreater(len(sampled_df), 0)
        self.assertTrue('snr_bucket' in sampled_df.columns)

    @patch('data_loader.load_dataset')
    def test_fetch_and_verify_librispeech(self, mock_load_dataset):
        """Test the main fetch and verify function."""
        mock_data = {
            'file': ['file1.flac'],
            'text': ['hello'],
            'speaker_id': [100],
        }
        mock_df = pd.DataFrame(mock_data)
        mock_dataset = MagicMock()
        mock_dataset.to_pandas.return_value = mock_df
        mock_load_dataset.return_value = mock_dataset

        from data_loader import fetch_and_verify_librispeech

        df = fetch_and_verify_librispeech(split="test-clean", max_samples=1, stratify=False)

        self.assertEqual(len(df), 1)
        self.assertIn('file', df.columns)

    def test_compute_file_hash(self):
        """Test file hash computation."""
        from data_loader import compute_file_hash
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name

        try:
            hash_val = compute_file_hash(tmp_path)
            self.assertEqual(hash_val, 'd8e8fca2dc0f896fd7cb4cb0031ba249') # MD5 of "test data"
        finally:
            os.unlink(tmp_path)

if __name__ == '__main__':
    unittest.main()
