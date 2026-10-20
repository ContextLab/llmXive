import os
import json
import time
import pytest
from pathlib import Path

from runtime.runtime_tracker import start, stop

def test_runtime_tracker_writes_file(tmp_path):
    # Redirect the paths.data function to use a temporary directory
    original_data = None
    from llmxive_toolkit import paths
    original_data = paths.data
    
    def temp_data(*parts):
        return Path(tmp_path, *parts)
    
    paths.data = temp_data
    
    try:
        start()
        time.sleep(0.01)  # short pause
        elapsed, within = stop(10)  # 10‑second limit
        
        # Verify returned values
        assert isinstance(elapsed, float)
        assert isinstance(within, bool)
        
        # Verify JSON file exists and contents are correct
        runtime_file = temp_data("runtime", "pipeline_runtime.json")
        assert runtime_file.is_file()
        
        with runtime_file.open() as f:
            data = json.load(f)
        
        assert "total_seconds" in data
        assert "within_limit" in data
        assert data["within_limit"] == within
    finally:
        # Restore original function
        if original_data is not None:
            paths.data = original_data
