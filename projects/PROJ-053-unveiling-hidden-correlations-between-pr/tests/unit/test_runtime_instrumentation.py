"""
Unit tests for runtime instrumentation (T039).
Verifies that runtime is measured and saved correctly.
"""
import json
import os
import tempfile
import time
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

# Mock config paths for testing
@pytest.fixture
def mock_paths(tmp_path):
    # Create temporary directory structure
    logs_dir = tmp_path / "logs"
    results_dir = tmp_path / "results"
    logs_dir.mkdir()
    results_dir.mkdir()
    return tmp_path

def test_save_runtime_metrics(mock_paths, tmp_path):
    """Test that save_runtime_metrics correctly writes to metrics.json."""
    # Patch config functions to use temp paths
    with patch('utils.logger.get_results_dir', return_value=tmp_path / "results"):
        from utils.logger import save_runtime_metrics
        
        results_dir = tmp_path / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        metrics_path = results_dir / "metrics.json"
        
        # Test case 1: Runtime within limit
        save_runtime_metrics(100.0, 21600)
        
        assert metrics_path.exists()
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        assert metrics['total_runtime_seconds'] == 100.0
        assert metrics['time_limit_seconds'] == 21600
        assert metrics['runtime_status'] == 'PASS'
        
        # Test case 2: Runtime exceeds limit
        save_runtime_metrics(30000.0, 21600)
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        assert metrics['total_runtime_seconds'] == 30000.0
        assert metrics['runtime_status'] == 'FAIL'

def test_runtime_measurement_logic():
    """Test that runtime measurement logic works correctly."""
    start = time.time()
    time.sleep(0.1)  # Sleep for 100ms
    end = time.time()
    
    elapsed = end - start
    assert elapsed >= 0.1
    assert elapsed < 0.2  # Should not take more than 200ms

def test_config_time_limit_constant():
    """Test that the time limit constant is correctly defined."""
    from config import get_time_limit_seconds
    
    limit = get_time_limit_seconds()
    assert limit == 21600  # 6 hours in seconds