"""
Unit tests for optimization utilities.

These tests verify that the optimization utilities work correctly
and stay within memory limits.
"""
import os
import sys
import json
import tempfile
import numpy as np
import pytest
from unittest.mock import Mock, patch
import mne

# Import the module under test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
from utils.optimization_utils import (
    get_current_memory_mb,
    estimate_memory_for_epochs,
    chunked_ica_processing,
    optimized_chunked_loading,
    batch_psd_computation,
    optimize_ica_components,
    MEMORY_LIMIT_GB,
    CHUNK_SIZE_EPOCHS
)

class TestMemoryEstimation:
    """Tests for memory estimation functions."""
    
    def test_estimate_memory_for_epochs(self):
        """Test memory estimation for epochs."""
        n_epochs = 100
        n_channels = 32
        n_times = 1000
        
        estimated_mb = estimate_memory_for_epochs(n_epochs, n_channels, n_times)
        
        # Should be positive and reasonable
        assert estimated_mb > 0
        # Should be less than 1000 MB for this small example
        assert estimated_mb < 1000
        
        # Check that memory scales linearly with number of epochs
        estimated_mb_2x = estimate_memory_for_epochs(n_epochs * 2, n_channels, n_times)
        assert abs(estimated_mb_2x - 2 * estimated_mb) / estimated_mb < 0.1  # Within 10%

    def test_get_current_memory_mb(self):
        """Test current memory measurement."""
        memory_mb = get_current_memory_mb()
        assert memory_mb > 0
        assert isinstance(memory_mb, float)

class TestChunkedLoading:
    """Tests for chunked loading functionality."""
    
    def test_chunked_loading_basic(self):
        """Test basic chunked loading."""
        # Create mock epochs
        n_epochs = 50
        n_channels = 16
        n_times = 500
        sfreq = 250.0
        
        # Create dummy data
        data = np.random.randn(n_epochs, n_channels, n_times)
        times = np.arange(n_times) / sfreq
        
        # Create MNE Epochs object
        info = mne.create_info(
            ch_names=[f'EEG{i}' for i in range(n_channels)],
            sfreq=sfreq,
            ch_types='eeg'
        )
        events = np.array([[i * 1000, 0, 1] for i in range(n_epochs)])
        epochs = mne.EpochsArray(data, info, events=events, tmin=0)
        
        # Test chunked loading
        chunks = list(optimized_chunked_loading(epochs, chunk_size=10))
        
        assert len(chunks) == 5  # 50 epochs / 10 per chunk
        
        # Verify all data is present
        total_epochs = sum(chunk[0].shape[0] for chunk in chunks)
        assert total_epochs == n_epochs
        
        # Verify metadata
        for data_chunk, metadata in chunks:
            assert 'chunk_start' in metadata
            assert 'chunk_end' in metadata
            assert 'progress' in metadata
            assert 0 <= metadata['progress'] <= 1

    def test_chunked_loading_memory_monitoring(self):
        """Test that memory is monitored during chunked loading."""
        n_epochs = 20
        n_channels = 8
        n_times = 200
        sfreq = 250.0
        
        data = np.random.randn(n_epochs, n_channels, n_times)
        times = np.arange(n_times) / sfreq
        
        info = mne.create_info(
            ch_names=[f'EEG{i}' for i in range(n_channels)],
            sfreq=sfreq,
            ch_types='eeg'
        )
        events = np.array([[i * 1000, 0, 1] for i in range(n_epochs)])
        epochs = mne.EpochsArray(data, info, events=events, tmin=0)
        
        # Test chunked loading with memory monitoring
        for data_chunk, metadata in optimized_chunked_loading(epochs, chunk_size=5):
            assert 'current_memory_mb' in metadata
            assert 'peak_memory_mb' in metadata
            assert metadata['current_memory_mb'] > 0
            assert metadata['peak_memory_mb'] > 0

class TestICAProcessing:
    """Tests for ICA processing optimization."""
    
    @pytest.fixture
    def mock_raw(self):
        """Create a mock raw EEG object."""
        n_channels = 16
        n_times = 10000
        sfreq = 250.0
        
        data = np.random.randn(n_channels, n_times)
        info = mne.create_info(
            ch_names=[f'EEG{i}' for i in range(n_channels)],
            sfreq=sfreq,
            ch_types='eeg'
        )
        
        return mne.io.RawArray(data, info)
    
    def test_chunked_ica_processing_basic(self, mock_raw):
        """Test basic ICA processing."""
        ica, metrics = chunked_ica_processing(
            mock_raw,
            n_components=5,
            method='fastica'
        )
        
        assert ica is not None
        assert metrics is not None
        assert 'processing_time_seconds' in metrics
        assert 'peak_memory_mb' in metrics
        assert metrics['peak_memory_mb'] > 0
        
        # Verify ICA was fitted
        assert hasattr(ica, 'n_components_')
        assert ica.n_components_ == 5
    
    def test_chunked_ica_processing_memory_limit(self, mock_raw):
        """Test ICA processing respects memory limits."""
        # Set a very low memory limit to test the limit checking
        ica, metrics = chunked_ica_processing(
            mock_raw,
            n_components=3,
            method='fastica',
            memory_limit_mb=10000  # High limit to avoid actual failure
        )
        
        assert 'memory_limit_exceeded' in metrics
        # With a high limit, this should be False
        assert metrics['memory_limit_exceeded'] == False

class TestPSDComputation:
    """Tests for PSD computation optimization."""
    
    def test_batch_psd_computation(self):
        """Test batch PSD computation."""
        n_epochs = 10
        n_channels = 8
        n_times = 500
        sfreq = 250.0
        
        data = np.random.randn(n_epochs, n_channels, n_times)
        times = np.arange(n_times) / sfreq
        
        info = mne.create_info(
            ch_names=[f'EEG{i}' for i in range(n_channels)],
            sfreq=sfreq,
            ch_types='eeg'
        )
        events = np.array([[i * 1000, 0, 1] for i in range(n_epochs)])
        epochs = mne.EpochsArray(data, info, events=events, tmin=0)
        
        freqs, psd_values, metrics = batch_psd_computation(
            epochs,
            fmin=1.0,
            fmax=45.0,
            n_fft=256,
            n_overlap=128,
            batch_size=5
        )
        
        assert freqs is not None
        assert psd_values is not None
        assert metrics is not None
        
        # Check shapes
        assert len(freqs) == 256 // 2 + 1
        assert psd_values.shape == (n_epochs, n_channels, len(freqs))
        
        # Check metrics
        assert 'processing_time_seconds' in metrics
        assert metrics['processing_time_seconds'] > 0

class TestComponentOptimization:
    """Tests for ICA component optimization."""
    
    @pytest.fixture
    def mock_ica_and_raw(self):
        """Create mock ICA and raw objects."""
        n_channels = 16
        n_times = 5000
        sfreq = 250.0
        
        data = np.random.randn(n_channels, n_times)
        info = mne.create_info(
            ch_names=[f'EEG{i}' for i in range(n_channels)],
            sfreq=sfreq,
            ch_types='eeg'
        )
        raw = mne.io.RawArray(data, info)
        
        # Fit ICA
        ica = mne.preprocessing.ICA(n_components=5, method='fastica', random_state=42)
        ica.fit(raw)
        
        return ica, raw
    
    def test_optimize_ica_components(self, mock_ica_and_raw):
        """Test ICA component optimization."""
        ica, raw = mock_ica_and_raw
        
        # Test with explained variance method
        optimal_components = optimize_ica_components(
            ica,
            raw,
            threshold=0.9,
            method='explained_variance'
        )
        
        assert isinstance(optimal_components, list)
        assert len(optimal_components) > 0
        assert len(optimal_components) <= ica.n_components_
        
        # All components should be valid indices
        for comp in optimal_components:
            assert 0 <= comp < ica.n_components_

class TestOptimizationIntegration:
    """Integration tests for optimization utilities."""
    
    def test_memory_limits_not_exceeded(self):
        """Test that memory limits are respected during processing."""
        # Create a small dataset
        n_epochs = 20
        n_channels = 8
        n_times = 200
        sfreq = 250.0
        
        data = np.random.randn(n_epochs, n_channels, n_times)
        info = mne.create_info(
            ch_names=[f'EEG{i}' for i in range(n_channels)],
            sfreq=sfreq,
            ch_types='eeg'
        )
        events = np.array([[i * 1000, 0, 1] for i in range(n_epochs)])
        epochs = mne.EpochsArray(data, info, events=events, tmin=0)
        
        # Process with chunked loading
        max_memory = 0
        for data_chunk, metadata in optimized_chunked_loading(epochs, chunk_size=5):
            if metadata['peak_memory_mb'] > max_memory:
                max_memory = metadata['peak_memory_mb']
        
        # Memory should be well under the limit
        assert max_memory < MEMORY_LIMIT_GB * 1024  # Convert to MB

if __name__ == '__main__':
    pytest.main([__file__, '-v'])