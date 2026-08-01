import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import psutil

from src.data.profiles import (
    get_memory_usage_mb,
    get_cpu_time_seconds,
    profile_clip_execution,
    save_profiling_results,
    load_profiling_results,
    run_feasibility_gate,
)
from src.config import get_state_root


class TestMemoryProfiling:
    @patch("psutil.Process")
    def test_get_memory_usage_mb_mocked(self, mock_process_class):
        """Test memory retrieval with mocked psutil."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 100  # 100 MB
        mock_process_class.return_value = mock_process

        mem_mb = get_memory_usage_mb()
        assert mem_mb == 100.0

    @patch("time.time")
    def test_get_cpu_time_seconds_mocked(self, mock_time):
        """Test CPU time calculation with mocked time."""
        mock_time.side_effect = [100.0, 105.0]  # Start, End
        duration = get_cpu_time_seconds()
        assert duration == 5.0

    def test_profile_clip_execution_structure(self):
        """Test that profile_clip_execution returns expected keys."""
        # We mock the actual function execution to avoid needing real video files
        with patch("src.data.profiles.process_video_clip") as mock_proc:
            mock_proc.return_value = {"status": "success"}
            
            result = profile_clip_execution("dummy_path.mp4", 1000)
            
            assert "memory_mb" in result
            assert "time_seconds" in result
            assert "clip_path" in result
            assert "status" in result

    def test_save_and_load_profiling_results(self):
        """Test saving and loading profiling results to/from JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_results = [
                {"clip_path": "a.mp4", "memory_mb": 100.0, "time_seconds": 1.0},
                {"clip_path": "b.mp4", "memory_mb": 150.0, "time_seconds": 1.5},
            ]
            output_path = os.path.join(tmpdir, "test_profiles.json")
            
            save_profiling_results(test_results, output_path)
            
            assert os.path.exists(output_path)
            
            loaded = load_profiling_results(output_path)
            assert len(loaded) == 2
            assert loaded[0]["memory_mb"] == 100.0
            assert loaded[1]["time_seconds"] == 1.5

    @patch("src.data.profiles.run_feasibility_gate")
    def test_run_feasibility_gate_integration(self, mock_gate):
        """Test that run_feasibility_gate is called correctly in main context."""
        mock_gate.return_value = {"passed": True, "peak_memory_gb": 2.0, "projected_hours": 3.0}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            state_root = Path(tmpdir)
            # Override state root for the test
            with patch("src.data.profiles.get_state_root", return_value=state_root):
                result = run_feasibility_gate(
                    profiling_data=[{"memory_mb": 2000, "time_seconds": 10}],
                    projected_total_hours=3.0,
                    output_filename="test_gate.json"
                )
                
                assert result["passed"] is True
                assert "peak_memory_gb" in result
                assert "projected_hours" in result

    def test_run_feasibility_gate_failure_high_memory(self):
        """Test gate failure when memory exceeds 7GB."""
        # Simulate high memory usage
        profiling_data = [{"memory_mb": 8000 * 1024}] # 8GB
        
        result = run_feasibility_gate(
            profiling_data=profiling_data,
            projected_total_hours=1.0,
            output_filename="test_fail_memory.json"
        )
        
        assert result["passed"] is False
        assert result["reason"] == "Peak memory (8.00 GB) exceeds limit (7.00 GB)"

    def test_run_feasibility_gate_failure_high_time(self):
        """Test gate failure when projected time exceeds 6 hours."""
        profiling_data = [{"memory_mb": 100}] # Low memory
        
        result = run_feasibility_gate(
            profiling_data=profiling_data,
            projected_total_hours=7.0, # Exceeds 6 hours
            output_filename="test_fail_time.json"
        )
        
        assert result["passed"] is False
        assert result["reason"] == "Projected total time (7.00 hours) exceeds limit (6.00 hours)"

    @patch("src.data.profiles.get_state_root")
    @patch("src.data.profiles.write_json")
    def test_gate_writes_output_file(self, mock_write, mock_state_root):
        """Verify that the gate writes the JSON file to the state directory."""
        mock_state_root.return_value = Path("/tmp/test_state")
        
        run_feasibility_gate(
            profiling_data=[{"memory_mb": 100}],
            projected_total_hours=1.0,
            output_filename="gate_result.json"
        )
        
        mock_write.assert_called_once()
        call_args = mock_write.call_args
        assert "gate_result.json" in str(call_args[0][1]) # Check path in args
