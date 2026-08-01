import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.data.profiles import (
    get_memory_usage_mb,
    get_cpu_time_seconds,
    profile_clip_execution,
    save_profiling_results,
    load_profiling_results,
    run_feasibility_gate
)
from src.config import get_state_root, get_data_root

class TestMemoryProfiling:
    """Unit tests for memory profiling logic with mock data."""

    def test_get_memory_usage_mb(self):
        """Test that memory usage is returned as a positive float."""
        mem_mb = get_memory_usage_mb()
        assert isinstance(mem_mb, float)
        assert mem_mb > 0

    def test_get_cpu_time_seconds(self):
        """Test that CPU time is returned as a non-negative float."""
        cpu_time = get_cpu_time_seconds()
        assert isinstance(cpu_time, float)
        assert cpu_time >= 0

    @patch('src.data.profiles.batch_process_clips')
    def test_profile_clip_execution_success(self, mock_batch_process):
        """Test profiling a successful clip execution."""
        # Mock the batch_process_clips to return a dummy result
        mock_batch_process.return_value = {"status": "success", "features": {}}
        
        clip_path = "/fake/path/video.mp4"
        clip_id = "test_clip_001"
        
        result = profile_clip_execution(clip_id, clip_path)
        
        assert result["clip_id"] == clip_id
        assert result["clip_path"] == clip_path
        assert result["status"] == "success"
        assert "execution_time_seconds" in result
        assert "peak_memory_mb" in result
        assert result["execution_time_seconds"] >= 0
        assert result["peak_memory_mb"] > 0

    @patch('src.data.profiles.batch_process_clips')
    def test_profile_clip_execution_failure(self, mock_batch_process):
        """Test profiling a failed clip execution."""
        # Mock the batch_process_clips to raise an exception
        mock_batch_process.side_effect = Exception("Simulated failure")
        
        clip_path = "/fake/path/video.mp4"
        clip_id = "test_clip_002"
        
        result = profile_clip_execution(clip_id, clip_path)
        
        assert result["clip_id"] == clip_id
        assert result["clip_path"] == clip_path
        assert result["status"] == "failed"
        assert "error" in result
        assert "Simulated failure" in result["error"]

    def test_save_and_load_profiling_results(self):
        """Test saving and loading profiling results to/from JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_results = [
                {
                    "clip_id": "test_1",
                    "clip_path": "/path/to/video1.mp4",
                    "execution_time_seconds": 1.5,
                    "peak_memory_mb": 100.0,
                    "status": "success"
                },
                {
                    "clip_id": "test_2",
                    "clip_path": "/path/to/video2.mp4",
                    "execution_time_seconds": 2.0,
                    "peak_memory_mb": 150.0,
                    "status": "success"
                }
            ]
            
            output_path = os.path.join(temp_dir, "test_results.json")
            
            # Save results
            saved_path = save_profiling_results(test_results, output_path)
            assert saved_path == output_path
            assert os.path.exists(output_path)
            
            # Load results
            loaded_results = load_profiling_results(output_path)
            assert len(loaded_results) == len(test_results)
            assert loaded_results[0]["clip_id"] == "test_1"
            assert loaded_results[1]["peak_memory_mb"] == 150.0

    @patch('src.data.profiles.get_state_root')
    @patch('src.data.profiles.get_data_root')
    @patch('os.walk')
    @patch('src.data.profiles.profile_clip_execution')
    def test_run_feasibility_gate_viable(
        self, 
        mock_profile, 
        mock_walk, 
        mock_data_root, 
        mock_state_root
    ):
        """Test feasibility gate with viable results (passes constraints)."""
        # Mock paths
        mock_state_root.return_value = "/tmp/test_state"
        mock_data_root.return_value = "/tmp/test_data"
        
        # Mock directory walk to return fake video files
        fake_files = [f"video_{i}.mp4" for i in range(10)]
        mock_walk.return_value = [("/tmp/test_data/raw", [], fake_files)]
        
        # Mock profiling results to be well within limits
        def mock_profile_side_effect(clip_id, clip_path):
            return {
                "clip_id": clip_id,
                "clip_path": clip_path,
                "execution_time_seconds": 0.1,  # Very fast
                "peak_memory_mb": 100.0,  # Very low memory
                "status": "success"
            }
        
        mock_profile.side_effect = mock_profile_side_effect
        
        # Run gate
        result = run_feasibility_gate(sample_size=10, max_memory_gb=7.0, max_projected_hours=6.0)
        
        assert result["gate_passed"] is True
        assert result["status"] == "viable"
        assert result["memory_constraint_ok"] is True
        assert result["time_constraint_ok"] is True

    @patch('src.data.profiles.get_state_root')
    @patch('src.data.profiles.get_data_root')
    @patch('os.walk')
    @patch('src.data.profiles.profile_clip_execution')
    def test_run_feasibility_gate_memory_exceeded(
        self, 
        mock_profile, 
        mock_walk, 
        mock_data_root, 
        mock_state_root
    ):
        """Test feasibility gate when memory constraint is exceeded."""
        mock_state_root.return_value = "/tmp/test_state"
        mock_data_root.return_value = "/tmp/test_data"
        
        fake_files = [f"video_{i}.mp4" for i in range(10)]
        mock_walk.return_value = [("/tmp/test_data/raw", [], fake_files)]
        
        # Mock high memory usage
        def mock_profile_side_effect(clip_id, clip_path):
            return {
                "clip_id": clip_id,
                "clip_path": clip_path,
                "execution_time_seconds": 0.1,
                "peak_memory_mb": 8000.0,  # ~7.8 GB - exceeds 7GB limit
                "status": "success"
            }
        
        mock_profile.side_effect = mock_profile_side_effect
        
        result = run_feasibility_gate(sample_size=10, max_memory_gb=7.0, max_projected_hours=6.0)
        
        assert result["gate_passed"] is False
        assert result["status"] == "non-viable"
        assert result["memory_constraint_ok"] is False
        assert result["time_constraint_ok"] is True

    @patch('src.data.profiles.get_state_root')
    @patch('src.data.profiles.get_data_root')
    @patch('os.walk')
    @patch('src.data.profiles.profile_clip_execution')
    def test_run_feasibility_gate_time_exceeded(
        self, 
        mock_profile, 
        mock_walk, 
        mock_data_root, 
        mock_state_root
    ):
        """Test feasibility gate when time constraint is exceeded."""
        mock_state_root.return_value = "/tmp/test_state"
        mock_data_root.return_value = "/tmp/test_data"
        
        fake_files = [f"video_{i}.mp4" for i in range(10)]
        mock_walk.return_value = [("/tmp/test_data/raw", [], fake_files)]
        
        # Mock slow execution (would project to > 6 hours for 10k clips)
        # 0.1s per clip * 10000 = 1000s = 0.28h (OK)
        # Need: 0.1s * 10000 = 1000s -> need 21600s (6h) -> 2.16s per clip
        def mock_profile_side_effect(clip_id, clip_path):
            return {
                "clip_id": clip_id,
                "clip_path": clip_path,
                "execution_time_seconds": 3.0,  # Would project to ~8.3 hours
                "peak_memory_mb": 100.0,
                "status": "success"
            }
        
        mock_profile.side_effect = mock_profile_side_effect
        
        result = run_feasibility_gate(sample_size=10, max_memory_gb=7.0, max_projected_hours=6.0)
        
        assert result["gate_passed"] is False
        assert result["status"] == "non-viable"
        assert result["memory_constraint_ok"] is True
        assert result["time_constraint_ok"] is False

    @patch('os.path.exists')
    def test_run_feasibility_gate_no_data(self, mock_exists):
        """Test feasibility gate when no data directory exists."""
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            run_feasibility_gate(sample_size=10)