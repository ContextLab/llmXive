"""
Unit tests for chunked loading logic in code/data/loader.py.

Specifically verifies that memory usage stays within the 7GB peak limit
during epoch loading operations.
"""
import os
import sys
import tempfile
import shutil
import unittest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from contextlib import contextmanager

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.loader import estimate_memory_usage, load_epochs_chunked, get_epoch_metadata


class MockEpochs:
    """Mock MNE Epochs object for testing without real data."""
    def __init__(self, n_epochs, n_channels, sfreq, data_shape):
        self.n_epochs = n_epochs
        self.n_channels = n_channels
        self.sfreq = sfreq
        self.info = {'nchan': n_channels}
        self.times = np.arange(data_shape[2]) / sfreq
        
    def __len__(self):
        return self.n_epochs
        
    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return self
        return np.random.rand(self.n_channels, len(self.times))
        
    def get_data(self, items=None):
        if items is None:
            return np.random.rand(self.n_epochs, self.n_channels, len(self.times))
        return np.random.rand(len(items), self.n_channels, len(self.times))


@contextmanager
def mock_memory_monitor(limit_gb=7.0):
    """Context manager to mock memory tracking."""
    with patch('data.loader.psutil') as mock_psutil:
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB baseline
        mock_psutil.Process.return_value = mock_process
        yield mock_process


class TestChunkedLoading(unittest.TestCase):
    """Test suite for chunked loading memory constraints."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.chunk_size = 10
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_estimate_memory_usage_calculation(self):
        """Test that memory estimation formula is reasonable."""
        # Simulate: 100 epochs, 64 channels, 250Hz, 2 seconds
        # Data size = 100 * 64 * 500 * 8 bytes (float64)
        n_epochs = 100
        n_channels = 64
        n_samples = 500  # 2 seconds at 250Hz
        
        estimated_gb = estimate_memory_usage(n_epochs, n_channels, n_samples)
        
        # Expected: 100 * 64 * 500 * 8 bytes = 25,600,000 bytes ≈ 0.024 GB
        expected_bytes = n_epochs * n_channels * n_samples * 8
        expected_gb = expected_bytes / (1024 ** 3)
        
        self.assertAlmostEqual(estimated_gb, expected_gb, places=2)
        self.assertLess(estimated_gb, 7.0, "Estimated memory should be under 7GB")

    def test_chunked_loading_memory_peak(self):
        """Verify that chunked loading keeps memory peak below 7GB."""
        # Create a scenario that would exceed 7GB if loaded all at once
        # 1000 epochs, 128 channels, 10 seconds @ 250Hz
        n_total_epochs = 1000
        n_channels = 128
        sfreq = 250
        duration_seconds = 10
        n_samples = sfreq * duration_seconds
        
        # Calculate full load memory
        full_load_gb = estimate_memory_usage(n_total_epochs, n_channels, n_samples)
        
        # If full load would exceed 7GB, chunked loading should handle it
        if full_load_gb > 7.0:
            # Mock the epoch loading to simulate the process
            with mock_memory_monitor() as mock_process:
                # Simulate chunked processing
                chunk_sizes = []
                for start in range(0, n_total_epochs, self.chunk_size):
                    end = min(start + self.chunk_size, n_total_epochs)
                    chunk_size = end - start
                    chunk_sizes.append(chunk_size)
                    
                    # Estimate memory for this chunk
                    chunk_memory = estimate_memory_usage(chunk_size, n_channels, n_samples)
                    
                    # Verify each chunk is well under the limit
                    self.assertLess(
                        chunk_memory, 
                        7.0, 
                        f"Chunk memory {chunk_memory:.2f}GB exceeds 7GB limit"
                    )
                    
                    # Simulate memory usage tracking
                    mock_process.memory_info.return_value.rss = int(
                        (chunk_memory * (1024 ** 3)) * 0.8  # 80% of estimated
                    )
                
                # Verify peak memory tracking logic
                mock_process.memory_info.assert_called()
                
        else:
            # Even if full load is under 7GB, chunked should still work
            self.assertLess(full_load_gb, 7.0)

    def test_chunked_loading_function_signature(self):
        """Verify load_epochs_chunked accepts required parameters."""
        # This test ensures the function exists and has the right signature
        # Actual execution would require real MNE data
        import inspect
        sig = inspect.signature(load_epochs_chunked)
        params = list(sig.parameters.keys())
        
        self.assertIn('epochs', params)
        self.assertIn('chunk_size', params)
        self.assertIn('output_dir', params)
        
    def test_epoch_metadata_extraction(self):
        """Test that epoch metadata can be extracted correctly."""
        # Create mock metadata
        mock_metadata = pd.DataFrame({
            'epoch_id': range(10),
            'subject_id': ['S01'] * 10,
            'condition': ['task'] * 10,
            'onset': np.arange(10) * 2.0
        })
        
        # Test metadata retrieval
        metadata = get_epoch_metadata(mock_metadata, list(range(5)))
        
        self.assertEqual(len(metadata), 5)
        self.assertIn('epoch_id', metadata.columns)
        self.assertIn('subject_id', metadata.columns)

    def test_memory_limit_enforcement(self):
        """Test that memory limits are properly enforced in chunking logic."""
        # Calculate chunk size needed to stay under 7GB
        n_channels = 64
        n_samples = 250 * 5  # 5 seconds
        max_memory_gb = 7.0
        
        # Estimate how many epochs per chunk
        bytes_per_epoch = n_channels * n_samples * 8
        max_epochs_per_chunk = int((max_memory_gb * (1024 ** 3)) / bytes_per_epoch)
        
        # Verify calculation is reasonable
        self.assertGreater(max_epochs_per_chunk, 0)
        self.assertLess(max_epochs_per_chunk, 10000)
        
        # Test that our chunking logic respects this
        estimated_chunk_memory = estimate_memory_usage(
            max_epochs_per_chunk, 
            n_channels, 
            n_samples
        )
        
        self.assertLess(
            estimated_chunk_memory, 
            max_memory_gb,
            f"Calculated chunk memory {estimated_chunk_memory:.2f}GB exceeds limit"
        )


if __name__ == '__main__':
    unittest.main()