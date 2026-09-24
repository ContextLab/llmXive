import pytest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
import torch
import numpy as np
from pathlib import Path

# Import the functions to test
from src.utils import memory_guard, get_memory_usage_gb, cleanup_memory
from src.tracing import trace_single_image, trace_routing, simulate_routing_trace

class TestTracingMemoryManagement:
    @patch('src.utils.psutil.Process')
    def test_memory_guard_within_limit(self, mock_process):
        """Test that memory_guard returns True when memory is within limit."""
        mock_process.return_value.memory_info.return_value.rss = 1 * 1024 ** 3  # 1 GB
        
        result = memory_guard(7.0)
        assert result is True

    @patch('src.utils.psutil.Process')
    def test_memory_guard_exceeds_limit(self, mock_process):
        """Test that memory_guard raises MemoryError when memory exceeds limit."""
        mock_process.return_value.memory_info.return_value.rss = 8 * 1024 ** 3  # 8 GB
        
        with pytest.raises(MemoryError):
            memory_guard(7.0)

    def test_cleanup_memory(self):
        """Test that cleanup_memory runs without error."""
        cleanup_memory()
        # Just ensure it doesn't raise an exception

    @patch('src.tracing.load_imagenet_subset')
    @patch('src.tracing.load_sit_xl_model')
    @patch('src.tracing.get_memory_usage_gb')
    @patch('src.tracing.memory_guard')
    @patch('src.tracing.cleanup_memory')
    def test_trace_routing_memory_check(
        self, mock_cleanup, mock_guard, mock_mem_usage, mock_model, mock_loader
    ):
        """Test that trace_routing checks memory before processing each image."""
        mock_guard.return_value = True
        mock_mem_usage.return_value = 1.0
        
        # Mock dataset
        mock_dataset = [
            {'image': MagicMock()},
            {'image': MagicMock()}
        ]
        mock_loader.return_value = iter(mock_dataset)
        
        # Mock model
        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance
        
        # Mock trace_single_image to avoid actual processing
        with patch('src.tracing.trace_single_image') as mock_trace:
            mock_trace.return_value = np.random.rand(100, 28, 8).astype(np.float32)
            
            # Call trace_routing
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch('src.tracing.get_routing_cache_path', return_value=Path(tmpdir)):
                    with patch('src.tracing.get_results_path', return_value=Path(tmpdir)):
                        with patch('src.tracing.ensure_directories_exist'):
                            trace_routing(trace_set_size=2, simulate=False)
            
            # Verify memory_guard was called
            assert mock_guard.called

    def test_simulate_routing_trace(self):
        """Test that simulate_routing_trace generates files correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            simulate_routing_trace(num_images=2, output_dir=tmpdir)
            
            # Check that files were created
            cache_path = Path(tmpdir)
            assert (cache_path / "routing_0.npy").exists()
            assert (cache_path / "routing_1.npy").exists()
            
            # Check file contents
            data0 = np.load(cache_path / "routing_0.npy")
            assert data0.shape == (100, 28, 8)
            assert data0.dtype == np.float32