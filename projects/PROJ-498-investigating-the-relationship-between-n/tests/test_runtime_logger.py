import os
import json
import time
from pathlib import Path
import pytest

from runtime_logger import start_timer, get_elapsed_minutes, save_runtime_log, ensure_metrics_directory, RUNTIME_LOG_PATH

class TestRuntimeLogger:
    def test_ensure_metrics_directory(self):
        """Test that the metrics directory is created."""
        ensure_metrics_directory()
        assert Path("data/metrics").exists()

    def test_start_timer(self):
        """Test that start_timer returns a valid timestamp."""
        start_time = start_timer()
        assert isinstance(start_time, float)
        assert start_time > 0

    def test_get_elapsed_minutes(self):
        """Test that get_elapsed_minutes calculates time correctly."""
        start = start_timer()
        time.sleep(0.1)
        metrics = get_elapsed_minutes(start)
        
        assert "start_time" in metrics
        assert "end_time" in metrics
        assert "total_duration_minutes" in metrics
        assert metrics["total_duration_minutes"] >= 0.1 / 60.0

    def test_save_runtime_log(self):
        """Test that save_runtime_log writes valid JSON."""
        start = start_timer()
        time.sleep(0.05)
        info = get_elapsed_minutes(start)
        info["status"] = "success"
        
        save_runtime_log(info)
        
        assert RUNTIME_LOG_PATH.exists()
        
        with open(RUNTIME_LOG_PATH, 'r') as f:
            data = json.load(f)
        
        assert data["status"] == "success"
        assert "start_time" in data
        assert "end_time" in data
        assert "total_duration_minutes" in data

    def test_runtime_log_content_structure(self):
        """Verify the structure of the runtime log matches requirements."""
        start = start_timer()
        time.sleep(0.01)
        info = get_elapsed_minutes(start)
        info["status"] = "success"
        save_runtime_log(info)
        
        with open(RUNTIME_LOG_PATH, 'r') as f:
            data = json.load(f)
        
        required_keys = {"start_time", "end_time", "total_duration_minutes", "status"}
        assert required_keys.issubset(data.keys())
        assert data["status"] in ["success", "timeout", "memory_exceeded", "no_subjects"]
