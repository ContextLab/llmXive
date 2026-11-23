import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import numpy as np
import psutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.io import (
    load_data,
    load_dreamx_world_streaming,
    load_scannet_fallback,
    stream_and_process_frames,
    MemoryProfiler,
    save_results,
    verify_data_integrity
)

class TestMemoryProfiler:
    """Test memory profiling functionality."""
    
    def test_memory_profiler_context_manager(self):
        """Test that MemoryProfiler works as context manager."""
        with MemoryProfiler(max_rss_ratio=0.9, sampling_interval=0.01) as profiler:
            # Do some work
            _ = [x for x in range(1000)]
            profiler.sample()
        
        # Should complete without raising MemoryError
        assert profiler.max_rss > 0
    
    def test_memory_profiler_asserts_limit(self):
        """Test that MemoryProfiler raises MemoryError when limit exceeded."""
        # Mock available_ram to be very small to force limit exceeded
        with patch.object(psutil, 'virtual_memory') as mock_vm:
            mock_vm.return_value.available = 1000  # 1KB available
            
            profiler = MemoryProfiler(max_rss_ratio=0.5, sampling_interval=0.01)
            profiler.available_ram = 1000
            profiler.max_allowed_rss = 500
            profiler.max_rss = 600  # Simulate exceeding limit
            profiler._monitoring = False
            profiler._samples = [500, 600]
            
            with pytest.raises(MemoryError):
                profiler.stop()
    
    def test_memory_profiler_sampling(self):
        """Test that memory profiling samples correctly."""
        with MemoryProfiler(max_rss_ratio=0.9, sampling_interval=0.01) as profiler:
            profiler.sample()
            profiler.sample()
            profiler.sample()
        
        assert len(profiler._samples) >= 1
        assert all(s > 0 for s in profiler._samples)

class TestLoadData:
    """Test data loading functions."""
    
    @patch('utils.io.load_dataset')
    def test_load_dreamx_streaming(self, mock_load_dataset):
        """Test streaming load of DreamX-World."""
        # Mock streaming dataset
        mock_ds = Mock()
        mock_ds.__iter__ = Mock(return_value=iter([{"frame_id": 1}, {"frame_id": 2}]))
        mock_load_dataset.return_value = mock_ds
        
        result = load_dreamx_world_streaming()
        items = list(result)
        
        assert len(items) == 2
        mock_load_dataset.assert_called_once_with(
            "DreamX-World/DreamX-World-1.0",
            split="train",
            streaming=True,
            trust_remote_code=True
        )
    
    @patch('utils.io.load_dataset')
    def test_load_scannet_fallback(self, mock_load_dataset):
        """Test non-streaming load of ScanNet fallback."""
        # Mock non-streaming dataset
        mock_ds = Mock()
        mock_ds.__iter__ = Mock(return_value=iter([{"scene_id": "scene_001"}]))
        mock_load_dataset.return_value = mock_ds
        
        result = load_scannet_fallback()
        items = list(result)
        
        assert len(items) == 1
        mock_load_dataset.assert_called_once()
    
    def test_load_data_with_fallback(self):
        """Test that load_data uses fallback when requested."""
        with patch('utils.io.load_scannet_fallback') as mock_fallback:
            mock_fallback.return_value = iter([{"test": "data"}])
            
            result = load_data(fallback_to_scannet=True)
            items = list(result)
            
            assert len(items) == 1
            mock_fallback.assert_called_once()

class TestStreamAndProcessFrames:
    """Test streaming and processing functionality."""
    
    def test_stream_and_process_with_function(self):
        """Test streaming with a processing function."""
        mock_data = iter([
            {"frame_id": 1, "image": "img1"},
            {"frame_id": 2, "image": "img2"},
            {"frame_id": 3, "image": "img3"}
        ])
        
        def process_fn(item):
            return {"id": item["frame_id"], "has_image": True}
        
        results = stream_and_process_frames(mock_data, process_fn=process_fn, max_items=2)
        
        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[1]["id"] == 2
    
    def test_stream_and_process_without_function(self):
        """Test streaming without a processing function."""
        mock_data = iter([
            {"frame_id": 1},
            {"frame_id": 2}
        ])
        
        results = stream_and_process_frames(mock_data, max_items=2)
        
        assert len(results) == 2
        assert results[0]["frame_id"] == 1
    
    def test_stream_and_process_max_items(self):
        """Test that max_items limits processing."""
        mock_data = iter([{"frame_id": i} for i in range(100)])
        
        results = stream_and_process_frames(mock_data, max_items=10)
        
        assert len(results) == 10
    
    def test_stream_and_process_memory_limit(self):
        """Test that memory limit is enforced during streaming."""
        mock_data = iter([{"frame_id": i} for i in range(1000)])
        
        # Mock MemoryProfiler to raise MemoryError
        with patch('utils.io.MemoryProfiler') as MockProfiler:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_instance.stop = Mock(return_value=False)
            MockProfiler.return_value = mock_instance
            
            with pytest.raises(MemoryError):
                stream_and_process_frames(mock_data, max_items=100)

class TestSaveResults:
    """Test results saving functionality."""
    
    def test_save_results_creates_directory(self):
        """Test that save_results creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "results.json")
            results = [{"test": "data"}]
            
            save_results(results, output_path)
            
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                saved = json.load(f)
            assert saved == results
    
    def test_save_results_json_format(self):
        """Test that results are saved in correct JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "results.json")
            results = [
                {"frame_id": 1, "value": 10.5},
                {"frame_id": 2, "value": 20.3}
            ]
            
            save_results(results, output_path)
            
            with open(output_path, 'r') as f:
                saved = json.load(f)
            
            assert len(saved) == 2
            assert saved[0]["frame_id"] == 1

class TestDataIntegrity:
    """Test data integrity verification."""
    
    def test_verify_data_integrity_success(self):
        """Test verification with valid data."""
        mock_data = iter([
            {"frame_id": 1, "timestamp": 100},
            {"frame_id": 2, "timestamp": 200}
        ])
        
        result = verify_data_integrity(mock_data, ["frame_id", "timestamp"])
        
        assert result is True
    
    def test_verify_data_integrity_failure(self):
        """Test verification with missing keys."""
        mock_data = iter([
            {"frame_id": 1, "timestamp": 100},
            {"frame_id": 2}  # Missing timestamp
        ])
        
        result = verify_data_integrity(mock_data, ["frame_id", "timestamp"])
        
        assert result is False
    
    def test_verify_data_integrity_samples_first_100(self):
        """Test that verification only samples first 100 items."""
        mock_data = iter([{"frame_id": i, "timestamp": i*100} for i in range(200)])
        
        with patch('utils.io.logger') as mock_logger:
            result = verify_data_integrity(mock_data, ["frame_id", "timestamp"])
            
            # Should only check first 100 items
            assert result is True
            mock_logger.info.assert_called_with("Data integrity verified for 100 items")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
