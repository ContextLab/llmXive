import os
import json
import pytest
import numpy as np
from pathlib import Path
from code.monitoring import (
    get_ram_usage_mb,
    get_cpu_utilization,
    record_batch_metrics,
    save_metrics_to_file,
    capture_snapshot,
    get_peak_ram_for_batch
)
from code.config import get_results_path

def test_resource_queries():
    """Verify that resource queries return plausible positive numbers."""
    ram = get_ram_usage_mb()
    cpu = get_cpu_utilization()
    assert ram > 0
    assert 0 <= cpu <= 100

def test_capture_snapshot():
    """Verify that the capture_snapshot context manager records timing and resources."""
    with capture_snapshot() as snap:
        # Perform a small real task
        _ = [i**2 for i in range(10000)]
    
    assert "start_ram_mb" in snap
    assert "end_ram_mb" in snap
    assert "duration_sec" in snap
    assert snap["duration_sec"] >= 0

def test_batch_recording_and_persistence(tmp_path):
    """Verify that batch metrics are recorded and correctly persisted to JSON."""
    # Use a temporary path to avoid overwriting real results during tests
    test_file = tmp_path / "test_metrics.json"
    
    # Clear global state for test consistency
    import code.monitoring
    code.monitoring._metrics_log = []
    code.monitoring._peak_ram_mb = 0.0
    
    record_batch_metrics(
        batch_idx=0,
        batch_size=10,
        time_sec=1.5,
        ram_mb=500.0,
        cpu_pct=45.0
    )
    
    # Verify peak RAM was updated
    assert get_peak_ram_for_batch() == 500.0
    
    # Persist to temp file
    save_metrics_to_file(path=test_file)
    
    assert test_file.exists()
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["batch_idx"] == 0
    assert data[0]["ram_mb"] == 500.0
    assert data[0]["time_sec"] == 1.5

def test_peak_ram_tracking():
    """Verify that the global peak RAM is correctly tracked across multiple batches."""
    import code.monitoring
    code.monitoring._metrics_log = []
    code.monitoring._peak_ram_mb = 0.0
    
    record_batch_metrics(0, 10, 1.0, 100.0, 10.0)
    assert get_peak_ram_for_batch() == 100.0
    
    record_batch_metrics(1, 10, 1.0, 250.0, 10.0)
    assert get_peak_ram_for_batch() == 250.0
    
    record_batch_metrics(2, 10, 1.0, 150.0, 10.0)
    assert get_peak_ram_for_batch() == 250.0