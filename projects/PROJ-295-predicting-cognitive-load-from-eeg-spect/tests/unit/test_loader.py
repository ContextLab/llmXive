"""
Unit tests for the chunked loading logic in code/data/loader.py.

These tests verify:
1. The loader correctly yields epochs in chunks.
2. Memory usage remains within the 7GB constraint during chunked loading.
3. Data integrity is maintained across chunks.
"""
import os
import sys
import unittest
import tempfile
import shutil
import numpy as np
import pandas as pd
import mne
from unittest.mock import patch, MagicMock

# Add the project root to the path to import code modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.data.loader import (
    estimate_memory_usage,
    get_epoch_metadata,
    load_epochs_chunked,
    load_all_epochs
)

# Constants for testing
SAMPLE_RATE = 250  # Hz
N_CHANNELS = 64
EPOCH_DURATION_SECONDS = 2.0
CHUNK_SIZE_EPOCHS = 10
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * (1024 ** 3)

class TestChunkedLoader(unittest.TestCase):
    """Test cases for the chunked EEG data loading logic."""

    def setUp(self):
        """Set up a temporary directory and mock data for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_data = None
        self.events = None
        self.ch_names = [f'EEG {i:03d}' for i in range(N_CHANNELS)]
        self.info = mne.create_info(ch_names=self.ch_names, sfreq=SAMPLE_RATE, ch_types='eeg')
        
        # Generate realistic-looking mock EEG data
        n_samples = int(SAMPLE_RATE * EPOCH_DURATION_SECONDS)
        n_epochs_total = 100
        
        # Create mock raw data
        data = np.random.randn(N_CHANNELS, n_samples * n_epochs_total) * 1e-6
        self.raw_data = mne.io.RawArray(data, self.info)
        
        # Create mock events (every epoch duration)
        self.events = np.array([
            [i * int(SAMPLE_RATE * EPOCH_DURATION_SECONDS), 0, 1]
            for i in range(n_epochs_total)
        ])

    def tearDown(self):
        """Clean up the temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_estimate_memory_usage_basic(self):
        """Test that memory estimation logic returns a positive number."""
        # Estimate memory for a single epoch
        memory_bytes = estimate_memory_usage(
            n_channels=N_CHANNELS,
            n_samples=int(SAMPLE_RATE * EPOCH_DURATION_SECONDS),
            dtype=np.float64
        )
        
        self.assertGreater(memory_bytes, 0)
        # Check calculation: 64 channels * 500 samples * 8 bytes
        expected = N_CHANNELS * int(SAMPLE_RATE * EPOCH_DURATION_SECONDS) * 8
        self.assertEqual(memory_bytes, expected)

    def test_get_epoch_metadata(self):
        """Test that epoch metadata is correctly extracted."""
        # Create a mock Raw object
        mock_raw = MagicMock()
        mock_raw.info = {'sfreq': SAMPLE_RATE, 'ch_names': self.ch_names}
        mock_raw.n_times = int(SAMPLE_RATE * 60)  # 60 seconds of data
        mock_raw.get_channel_types = MagicMock(return_value=['eeg'] * N_CHANNELS)
        
        metadata = get_epoch_metadata(mock_raw)
        
        self.assertIn('sfreq', metadata)
        self.assertIn('n_channels', metadata)
        self.assertIn('duration', metadata)
        self.assertEqual(metadata['n_channels'], N_CHANNELS)
        self.assertEqual(metadata['sfreq'], SAMPLE_RATE)

    @patch('code.data.loader.mne')
    def test_load_epochs_chunked_memory_constraint(self, mock_mne):
        """
        Test that load_epochs_chunked respects the 7GB memory limit.
        
        This test verifies that the loader processes data in chunks
        and does not attempt to load the entire dataset into memory at once.
        """
        # Mock mne functions to avoid actual I/O
        mock_raw = MagicMock()
        mock_raw.info = {'sfreq': SAMPLE_RATE, 'ch_names': self.ch_names}
        mock_raw.n_times = int(SAMPLE_RATE * 60)
        mock_raw.get_channel_types = MagicMock(return_value=['eeg'] * N_CHANNELS)
        
        # Mock events
        mock_events = self.events[:CHUNK_SIZE_EPOCHS]
        
        # Mock epochs object
        mock_epochs = MagicMock()
        mock_epochs.get_data = MagicMock(return_value=np.random.randn(
            CHUNK_SIZE_EPOCHS, N_CHANNELS, int(SAMPLE_RATE * EPOCH_DURATION_SECONDS)
        ))
        mock_epochs.info = {'sfreq': SAMPLE_RATE, 'ch_names': self.ch_names}
        
        mock_mne.Epochs.return_value = mock_epochs
        
        # Simulate a large dataset by mocking the file glob to return many files
        with patch('code.data.loader.glob.glob') as mock_glob:
            # Simulate 1000 epoch files (would exceed memory if loaded all at once)
            mock_glob.return_value = [
                os.path.join(self.temp_dir, f'epoch_{i}.fif')
                for i in range(1000)
            ]
            
            # Track total memory usage during chunked loading
            max_memory_used = 0
            chunk_count = 0
            
            # Load data in chunks
            for chunk_data, metadata in load_epochs_chunked(
                data_dir=self.temp_dir,
                chunk_size=CHUNK_SIZE_EPOCHS,
                memory_limit_gb=MEMORY_LIMIT_GB
            ):
                chunk_count += 1
                chunk_memory = chunk_data.nbytes
                max_memory_used = max(max_memory_used, chunk_memory)
                
                # Verify each chunk is within reasonable size
                self.assertLessEqual(
                    chunk_memory, 
                    MEMORY_LIMIT_BYTES,
                    f"Chunk {chunk_count} exceeds memory limit"
                )
                
                # Verify chunk size matches expected
                self.assertEqual(chunk_data.shape[0], CHUNK_SIZE_EPOCHS)
                
                # Break after a few chunks to avoid long test time
                if chunk_count >= 5:
                    break
            
            # Verify that we processed multiple chunks (not all data at once)
            self.assertGreater(chunk_count, 1, "Loader should process data in multiple chunks")
            
            # Verify max memory used is well under the limit
            # We allow some overhead but it should be significantly less than 7GB
            self.assertLess(
                max_memory_used, 
                MEMORY_LIMIT_BYTES * 0.8,
                "Memory usage should stay comfortably under the 7GB limit"
            )

    def test_load_epochs_chunked_data_integrity(self):
        """
        Test that data integrity is maintained across chunked loading.
        
        This verifies that the data yielded by the chunked loader
        matches what would be loaded if the entire dataset were loaded at once.
        """
        # Create a small test dataset
        n_epochs = 20
        mock_epochs_list = []
        
        for i in range(n_epochs):
            # Create mock data for each epoch
            data = np.random.randn(N_CHANNELS, int(SAMPLE_RATE * EPOCH_DURATION_SECONDS))
            mock_epochs_list.append(data)
        
        # Simulate chunked loading
        chunk_size = 5
        chunks_data = []
        
        # Mock the internal logic to yield our pre-generated data
        with patch('code.data.loader.glob.glob') as mock_glob, \
             patch('code.data.loader.mne') as mock_mne:
            
            mock_glob.return_value = [
                os.path.join(self.temp_dir, f'epoch_{i}.fif')
                for i in range(n_epochs)
            ]
            
            # Mock mne.Epochs to return our pre-generated data
            def mock_epochs_constructor(*args, **kwargs):
                mock_ep = MagicMock()
                mock_ep.get_data = MagicMock(return_value=mock_epochs_list[0])
                return mock_ep
            
            mock_mne.Epochs.side_effect = mock_epochs_constructor
            
            # Collect chunks
            for chunk_data, _ in load_epochs_chunked(
                data_dir=self.temp_dir,
                chunk_size=chunk_size,
                memory_limit_gb=MEMORY_LIMIT_GB
            ):
                chunks_data.append(chunk_data)
            
            # Concatenate all chunks
            all_chunked_data = np.concatenate(chunks_data, axis=0)
            
            # Compare with expected data (first n_epochs * chunk_size)
            expected_data = np.concatenate(mock_epochs_list[:n_epochs], axis=0)
            
            # Verify shapes match
            self.assertEqual(all_chunked_data.shape, expected_data.shape)
            
            # Verify data values match (within floating point tolerance)
            np.testing.assert_array_almost_equal(
                all_chunked_data, 
                expected_data,
                decimal=5,
                err_msg="Data integrity check failed: chunked data does not match expected"
            )

    def test_load_epochs_chunked_empty_directory(self):
        """Test that the loader handles an empty directory gracefully."""
        # Create an empty directory
        empty_dir = tempfile.mkdtemp()
        
        try:
            chunks = list(load_epochs_chunked(
                data_dir=empty_dir,
                chunk_size=CHUNK_SIZE_EPOCHS,
                memory_limit_gb=MEMORY_LIMIT_GB
            ))
            
            # Should return an empty iterator
            self.assertEqual(len(chunks), 0)
        finally:
            shutil.rmtree(empty_dir)

    def test_load_epochs_chunked_memory_limit_enforcement(self):
        """
        Test that the loader enforces the memory limit.
        
        This test verifies that if a single chunk would exceed the memory limit,
        the loader raises an appropriate error.
        """
        # Create a mock that would exceed memory limit
        with patch('code.data.loader.estimate_memory_usage') as mock_estimate:
            # Simulate a chunk that exceeds the memory limit
            mock_estimate.return_value = MEMORY_LIMIT_BYTES * 2  # 2x the limit
            
            with self.assertRaises(MemoryError):
                # This should raise a MemoryError
                list(load_epochs_chunked(
                    data_dir=self.temp_dir,
                    chunk_size=1,  # Small chunk size, but mock returns huge estimate
                    memory_limit_gb=MEMORY_LIMIT_GB
                ))

if __name__ == '__main__':
    unittest.main()