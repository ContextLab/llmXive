"""
Tests for the runtime logger module.
"""
import json
import os
import sys
import time
import tempfile
from pathlib import Path
from datetime import datetime

# Add the project root to the path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.runtime_logger import (
    start_timer, 
    get_elapsed_minutes, 
    save_runtime_log,
    ensure_metrics_directory,
    LOG_FILE
)

def test_start_timer():
    """Test that start_timer returns a float."""
    start = start_timer()
    assert isinstance(start, float), "Start time should be a float"
    assert start > 0, "Start time should be positive"

def test_get_elapsed_minutes():
    """Test elapsed time calculation."""
    start = time.time()
    time.sleep(0.1)
    elapsed = get_elapsed_minutes(start)
    assert elapsed >= 0.1 / 60.0, f"Elapsed time should be at least 0.1/60 minutes, got {elapsed}"
    assert isinstance(elapsed, float), "Elapsed time should be a float"

def test_save_runtime_log():
    """Test that save_runtime_log creates a valid JSON file."""
    # Use a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override LOG_FILE for testing
        test_log_file = Path(tmpdir) / "runtime_log.json"
        
        start = time.time()
        time.sleep(0.1)
        end = time.time()
        
        # Temporarily replace the global LOG_FILE
        import code.runtime_logger as rt_module
        original_log_file = rt_module.LOG_FILE
        rt_module.LOG_FILE = test_log_file
        
        try:
            log_data = save_runtime_log(start, end, "success")
            
            # Verify the file exists
            assert test_log_file.exists(), "Runtime log file should exist"
            
            # Verify the content
            with open(test_log_file, 'r') as f:
                loaded_data = json.load(f)
            
            assert "start_time" in loaded_data, "start_time should be in log"
            assert "end_time" in loaded_data, "end_time should be in log"
            assert "total_duration_minutes" in loaded_data, "total_duration_minutes should be in log"
            assert "status" in loaded_data, "status should be in log"
            
            assert loaded_data["status"] == "success", "Status should be 'success'"
            assert isinstance(loaded_data["total_duration_minutes"], float), "Duration should be a float"
            
            # Verify timestamps are valid ISO format
            datetime.fromisoformat(loaded_data["start_time"])
            datetime.fromisoformat(loaded_data["end_time"])
            
            # Verify end_time is after start_time
            start_dt = datetime.fromisoformat(loaded_data["start_time"])
            end_dt = datetime.fromisoformat(loaded_data["end_time"])
            assert end_dt >= start_dt, "End time should be after or equal to start time"
            
        finally:
            # Restore original LOG_FILE
            rt_module.LOG_FILE = original_log_file

def test_timeout_status():
    """Test that timeout status is recorded correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_log_file = Path(tmpdir) / "runtime_log.json"
        
        start = time.time()
        end = time.time()
        
        import code.runtime_logger as rt_module
        original_log_file = rt_module.LOG_FILE
        rt_module.LOG_FILE = test_log_file
        
        try:
            log_data = save_runtime_log(start, end, "timeout")
            
            with open(test_log_file, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data["status"] == "timeout", "Status should be 'timeout'"
            
        finally:
            rt_module.LOG_FILE = original_log_file

if __name__ == "__main__":
    test_start_timer()
    test_get_elapsed_minutes()
    test_save_runtime_log()
    test_timeout_status()
    print("All tests passed!")