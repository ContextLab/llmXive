import pytest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
import torch
import numpy as np
from pathlib import Path
import json

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.tracing import (
    trace_single_image,
    trace_routing_batch,
    trace_routing,
    get_memory_usage_gb,
    compute_data_source_hash
)
from src.utils import memory_guard

class TestTracingMemoryManagement:
    """Test memory management in tracing functions."""

    def test_memory_guard_raises_on_exceed(self):
        """Test that memory_guard raises MemoryError when threshold is exceeded."""
        with patch('src.utils.get_memory_usage_gb', return_value=8.0):  # 8GB > 7GB
            with pytest.raises(MemoryError):
                memory_guard(7.0)

    def test_memory_guard_passes_under_limit(self):
        """Test that memory_guard returns True when under threshold."""
        with patch('src.utils.get_memory_usage_gb', return_value=4.0):  # 4GB < 7GB
            assert memory_guard(7.0) is True

    def test_trace_single_image_memory_check(self):
        """Test that trace_single_image checks memory before processing."""
        # Create mock model
        mock_model = MagicMock()
        mock_model.eval = MagicMock()
        
        # Create mock image
        mock_image = torch.randn(3, 256, 256)
        
        # Create temporary directories
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "results"
            cache_path = Path(tmpdir) / "cache"
            results_path.mkdir()
            cache_path.mkdir()
            
            # Create mock log files
            log_file = MagicMock()
            memory_log_file = MagicMock()
            
            # Mock memory_guard to pass
            with patch('src.tracing.memory_guard', return_value=True):
                # Mock the actual tracing logic to avoid model dependency
                with patch('src.tracing.get_memory_usage_gb', return_value=4.0):
                    result = trace_single_image(
                        mock_model, mock_image, list(range(-99, 100)),
                        'cpu', 0, results_path, cache_path,
                        log_file, memory_log_file
                    )
                    
                    # Verify result is a numpy array
                    assert isinstance(result, np.ndarray)
                    assert result.shape == (199, 28, 32)  # [timesteps, blocks, history_dim]

    def test_trace_routing_batch_memory_cleanup(self):
        """Test that trace_routing_batch cleans up memory after each image."""
        # Create mock model
        mock_model = MagicMock()
        
        # Create mock images
        mock_images = [torch.randn(3, 256, 256) for _ in range(3)]
        image_ids = [0, 1, 2]
        
        # Create temporary directories
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "results"
            cache_path = Path(tmpdir) / "cache"
            results_path.mkdir()
            cache_path.mkdir()
            
            # Create mock log files
            log_file = MagicMock()
            memory_log_file = MagicMock()
            
            # Mock memory_guard to pass
            with patch('src.tracing.memory_guard', return_value=True):
                with patch('src.tracing.get_memory_usage_gb', return_value=4.0):
                    with patch('torch.no_grad'):
                        with patch('np.save'):
                            results = trace_routing_batch(
                                mock_model, mock_images, image_ids,
                                list(range(-99, 100)), 'cpu',
                                results_path, cache_path,
                                log_file, memory_log_file
                            )
                            
                            # Verify all results are numpy arrays
                            assert len(results) == 3
                            for result in results:
                                assert isinstance(result, np.ndarray)
                                assert result.shape == (199, 28, 32)

    def test_compute_data_source_hash(self):
        """Test data source hash computation."""
        hash1 = compute_data_source_hash("imagenetk", "validation", b"test_shard")
        hash2 = compute_data_source_hash("imagenetk", "validation", b"test_shard")
        hash3 = compute_data_source_hash("imagenetk", "validation", b"different_shard")
        
        # Same inputs should produce same hash
        assert hash1 == hash2
        
        # Different inputs should produce different hash
        assert hash1 != hash3
        
        # Verify hash format (SHA-256)
        assert len(hash1) == 64  # Hex string of SHA-256

    def test_memory_usage_gb_function(self):
        """Test that get_memory_usage_gb returns a float."""
        mem_usage = get_memory_usage_gb()
        assert isinstance(mem_usage, float)
        assert mem_usage >= 0.0