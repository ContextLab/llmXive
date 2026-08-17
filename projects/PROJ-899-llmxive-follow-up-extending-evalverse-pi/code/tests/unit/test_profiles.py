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
    run_feasibility_gate,
    main
)

class TestMemoryProfiling:
    """Unit tests for memory profiling functionality."""

    def test_get_memory_usage_mb_returns_positive_value(self):
        """Test that get_memory_usage_mb returns a positive float."""
        memory_mb = get_memory_usage_mb()
        assert isinstance(memory_mb, float)
        assert memory_mb >= 0

    def test_get_cpu_time_seconds_returns_positive_value(self):
        """Test that get_cpu_time_seconds returns a positive value."""
        start_time = 0.0
        cpu_time = get_cpu_time_seconds(start_time)
        assert isinstance(cpu_time, float)
        assert cpu_time >= 0

    def test_profile_clip_execution_success(self):
        """Test profiling a successful function execution."""
        def mock_func():
            pass

        result = profile_clip_execution("test_clip", mock_func)
        
        assert result["clip_id"] == "test_clip"
        assert result["success"] is True
        assert result["cpu_time_seconds"] >= 0
        assert result["memory_peak_mb"] >= 0
        assert result["error_message"] is None
        assert "timestamp" in result

    def test_profile_clip_execution_failure(self):
        """Test profiling a function that raises an exception."""
        def failing_func():
            raise ValueError("Test error")

        result = profile_clip_execution("test_clip", failing_func)
        
        assert result["clip_id"] == "test_clip"
        assert result["success"] is False
        assert result["cpu_time_seconds"] >= 0
        assert result["memory_peak_mb"] >= 0
        assert result["error_message"] is not None
        assert "Test error" in result["error_message"]

    def test_save_profiling_results_creates_file(self):
        """Test that save_profiling_results creates a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_profiling.json")
            results = [
                {"clip_id": "clip1", "success": True, "cpu_time_seconds": 0.5, "memory_peak_mb": 100.0}
            ]
            
            saved_path = save_profiling_results(results, output_path)
            
            assert os.path.exists(saved_path)
            assert saved_path == output_path
            
            with open(saved_path, 'r') as f:
                data = json.load(f)
            
            assert "metadata" in data
            assert "results" in data
            assert len(data["results"]) == 1

    def test_save_profiling_results_with_summary(self):
        """Test that save_profiling_results includes summary statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_profiling.json")
            results = [
                {"clip_id": "clip1", "success": True, "cpu_time_seconds": 0.5, "memory_peak_mb": 100.0},
                {"clip_id": "clip2", "success": True, "cpu_time_seconds": 1.0, "memory_peak_mb": 150.0},
                {"clip_id": "clip3", "success": False, "cpu_time_seconds": 0.2, "memory_peak_mb": 50.0, "error_message": "Error"}
            ]
            
            saved_path = save_profiling_results(results, output_path)
            
            with open(saved_path, 'r') as f:
                data = json.load(f)
            
            assert "summary" in data
            assert data["summary"]["avg_cpu_time_seconds"] == 0.75  # (0.5 + 1.0) / 2
            assert data["summary"]["max_memory_mb"] == 150.0
            assert data["metadata"]["total_clips"] == 3
            assert data["metadata"]["successful_clips"] == 2
            assert data["metadata"]["failed_clips"] == 1

    def test_load_profiling_results(self):
        """Test loading profiling results from a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_profiling.json")
            results = [
                {"clip_id": "clip1", "success": True, "cpu_time_seconds": 0.5, "memory_peak_mb": 100.0}
            ]
            
            save_profiling_results(results, output_path)
            loaded_data = load_profiling_results(output_path)
            
            assert "metadata" in loaded_data
            assert "results" in loaded_data
            assert len(loaded_data["results"]) == 1
            assert loaded_data["results"][0]["clip_id"] == "clip1"

    def test_load_profiling_results_file_not_found(self):
        """Test that loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_profiling_results("/nonexistent/path/file.json")

    def test_run_feasibility_gate_pass(self):
        """Test feasibility gate with acceptable memory usage."""
        results = {
            "summary": {
                "max_memory_mb": 5000.0,  # ~4.88 GB, under 7GB limit
                "avg_cpu_time_seconds": 1.0
            }
        }
        
        assert run_feasibility_gate(results) is True

    def test_run_feasibility_gate_fail(self):
        """Test feasibility gate with excessive memory usage."""
        results = {
            "summary": {
                "max_memory_mb": 8000.0,  # ~7.81 GB, over 7GB limit
                "avg_cpu_time_seconds": 1.0
            }
        }
        
        assert run_feasibility_gate(results) is False

    def test_run_feasibility_gate_missing_summary(self):
        """Test feasibility gate with missing summary data."""
        results = {}
        
        assert run_feasibility_gate(results) is False

    def test_main_function_creates_output(self):
        """Test that main function creates the profiling log file."""
        with patch('src.data.profiles.fetch_evalverse_dataset') as mock_fetch, \
             patch('src.data.profiles.get_raw_data_dir') as mock_get_dir, \
             patch('os.path.exists') as mock_exists:
            
            # Mock the data directory to not exist, triggering mock clip creation
            mock_get_dir.return_value = "/mock/data/dir"
            mock_exists.return_value = False
            mock_fetch.side_effect = Exception("Mock fetch failure")
            
            # Run main
            output_path = main()
            
            assert output_path is not None
            # The file should be created in the default location
            assert os.path.exists(output_path)
            
            # Verify it's valid JSON
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert "metadata" in data
            assert "results" in data
            assert len(data["results"]) > 0