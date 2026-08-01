import os
import sys
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Import from project API surface
from src.cli.run_pipeline import get_sample_clips, process_batch_clips, main
from src.config import get_project_root, get_data_root, get_raw_data_dir


@pytest.fixture
def temp_raw_data_dir():
    """Create a temporary directory with mock video files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir)
        # Create mock video files (empty files with video extension)
        for i in range(5):
            video_file = raw_dir / f"test_video_{i}.mp4"
            video_file.touch()
        
        # Create a manifest
        manifest = {
            "clips": [
                {"id": f"test_video_{i}", "path": str(raw_dir / f"test_video_{i}.mp4")}
                for i in range(5)
            ]
        }
        with open(raw_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f)
        
        yield raw_dir


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestGetSampleClips:
    def test_get_sample_clips(self, temp_raw_data_dir):
        """Test that get_sample_clips returns the correct number of clips."""
        clips = get_sample_clips(temp_raw_data_dir, n=3)
        assert len(clips) == 3
        assert all("id" in clip and "path" in clip for clip in clips)
    
    def test_get_sample_clips_default_n(self, temp_raw_data_dir):
        """Test default n=100 (or all if fewer available)."""
        clips = get_sample_clips(temp_raw_data_dir)
        # Should return all 5 since we only have 5
        assert len(clips) == 5
    
    def test_get_sample_clips_missing_dir(self):
        """Test error handling when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            get_sample_clips(Path("/nonexistent/path"))


class TestProcessBatchClips:
    @patch('src.cli.run_pipeline.batch_process_clips')
    def test_process_batch_clips_basic(self, mock_batch_process, temp_raw_data_dir, temp_output_dir):
        """Test basic batch processing with mocked feature extraction."""
        # Mock the batch_process_clips to return a dummy result
        mock_batch_process.return_value = {"status": "success", "features_extracted": True}
        
        clips = get_sample_clips(temp_raw_data_dir, n=2)
        stats = process_batch_clips(clips, temp_output_dir)
        
        assert stats["total_clips"] == 2
        assert stats["successful_clips"] == 2
        assert stats["failed_clips"] == 0
        assert stats["total_time_seconds"] > 0
        assert "clip_times" in stats
        assert len(stats["clip_times"]) == 2
    
    @patch('src.cli.run_pipeline.batch_process_clips')
    def test_process_batch_clips_with_failures(self, mock_batch_process, temp_raw_data_dir, temp_output_dir):
        """Test batch processing when some clips fail."""
        # Make first succeed, second fail
        call_count = [0]
        def side_effect(clips, output_dir):
            call_count[0] += 1
            if call_count[0] == 1:
                return {"status": "success"}
            else:
                raise Exception("Simulated failure")
        
        mock_batch_process.side_effect = side_effect
        
        clips = get_sample_clips(temp_raw_data_dir, n=2)
        stats = process_batch_clips(clips, temp_output_dir)
        
        assert stats["successful_clips"] == 1
        assert stats["failed_clips"] == 1
        assert len(stats["errors"]) == 1
    
    @patch('src.cli.run_pipeline.batch_process_clips')
    def test_batch_processing_creates_output_files(self, mock_batch_process, temp_raw_data_dir, temp_output_dir):
        """Test that profiling log is created."""
        mock_batch_process.return_value = {"status": "success"}
        
        clips = get_sample_clips(temp_raw_data_dir, n=2)
        profiling_log = temp_output_dir / "test_profiling.json"
        
        stats = process_batch_clips(clips, temp_output_dir, profiling_log_path=profiling_log)
        
        assert profiling_log.exists()
        with open(profiling_log, 'r') as f:
            saved_stats = json.load(f)
        assert saved_stats["total_clips"] == 2


class TestMainFunction:
    @patch('src.cli.run_pipeline.get_sample_clips')
    @patch('src.cli.run_pipeline.process_batch_clips')
    @patch('src.cli.run_pipeline.write_json')
    def test_main_function(self, mock_write_json, mock_process, mock_get_clips, temp_raw_data_dir):
        """Test the main entry point."""
        mock_get_clips.return_value = [{"id": "test", "path": str(temp_raw_data_dir / "test.mp4")}]
        mock_process.return_value = {
            "total_clips": 1,
            "successful_clips": 1,
            "total_time_seconds": 1.0,
            "peak_memory_mb": 100.0
        }
        
        # Temporarily patch the raw data dir
        with patch('src.cli.run_pipeline.get_raw_data_dir', return_value=temp_raw_data_dir):
            result = main()
        
        assert result == 0
        mock_get_clips.assert_called_once()
        mock_process.assert_called_once()
        mock_write_json.assert_called_once()


class TestMemoryTracking:
    @patch('src.cli.run_pipeline.get_memory_usage_mb')
    @patch('src.cli.run_pipeline.batch_process_clips')
    def test_memory_tracking(self, mock_batch_process, mock_get_memory, temp_raw_data_dir, temp_output_dir):
        """Test that memory is tracked during processing."""
        mock_get_memory.side_effect = [500.0, 600.0, 550.0]  # before, after, after
        mock_batch_process.return_value = {"status": "success"}
        
        clips = get_sample_clips(temp_raw_data_dir, n=1)
        stats = process_batch_clips(clips, temp_output_dir)
        
        assert "clip_memory" in stats
        assert len(stats["clip_memory"]) == 1
        assert stats["peak_memory_mb"] > 0