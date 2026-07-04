"""
Unit tests for the monitoring module.
"""
import os
import json
import tempfile
import time

import pytest
import psutil

# Import the module under test
from code.monitoring import (
    get_ram_usage_mb,
    get_cpu_utilization,
    capture_snapshot,
    track_inference_time,
    record_batch_metrics,
    save_metrics_to_file,
    get_peak_ram_for_batch,
)


def test_get_ram_usage_mb_returns_positive_float():
    """Test that RAM usage is returned as a positive float."""
    ram = get_ram_usage_mb()
    assert isinstance(ram, float)
    assert ram > 0


def test_get_cpu_utilization_returns_float():
    """Test that CPU utilization is returned as a float."""
    cpu = get_cpu_utilization()
    assert isinstance(cpu, float)
    # CPU percent can be 0.0 up to 100.0 * num_cpus, but should be non-negative
    assert cpu >= 0


def test_capture_snapshot_structure():
    """Test that snapshot contains expected keys and types."""
    snapshot = capture_snapshot()

    assert "timestamp" in snapshot
    assert isinstance(snapshot["timestamp"], float)

    assert "process_ram_mb" in snapshot
    assert isinstance(snapshot["process_ram_mb"], float)
    assert snapshot["process_ram_mb"] > 0

    assert "process_cpu_pct" in snapshot
    assert isinstance(snapshot["process_cpu_pct"], float)
    assert snapshot["process_cpu_pct"] >= 0

    assert "system_ram_mb" in snapshot
    assert isinstance(snapshot["system_ram_mb"], float)
    assert snapshot["system_ram_mb"] > 0

    assert "system_cpu_pct" in snapshot
    assert isinstance(snapshot["system_cpu_pct"], float)
    assert snapshot["system_cpu_pct"] >= 0


def test_track_inference_time_context():
    """Test the inference time context manager tracks duration."""
    with track_inference_time() as metrics:
        # Simulate some work
        time.sleep(0.1)

    assert "duration_seconds" in metrics
    assert metrics["duration_seconds"] >= 0.09  # Allow small variance
    assert "start_timestamp" in metrics
    assert "end_timestamp" in metrics
    assert metrics["end_timestamp"] >= metrics["start_timestamp"]

    # Check RAM metrics exist
    assert "start_process_ram_mb" in metrics
    assert "end_process_ram_mb" in metrics
    assert "peak_process_ram_mb" in metrics
    assert "ram_delta_mb" in metrics


def test_record_batch_metrics():
    """Test that batch metrics are recorded correctly."""
    batch_id = 1
    mock_metrics = {
        "duration_seconds": 1.5,
        "start_process_ram_mb": 100.0,
        "end_process_ram_mb": 105.0,
        "peak_process_ram_mb": 105.0,
    }

    record = record_batch_metrics(batch_id, mock_metrics)

    assert record["batch_id"] == batch_id
    assert "timestamp" in record
    assert record["duration_seconds"] == 1.5


def test_save_and_load_metrics_to_file():
    """Test saving metrics to a JSON file and reading them back."""
    records = [
        {"batch_id": 1, "duration_seconds": 1.0},
        {"batch_id": 2, "duration_seconds": 2.0},
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    try:
        save_metrics_to_file(records, temp_path)

        assert os.path.exists(temp_path)

        with open(temp_path, 'r') as f:
            loaded_records = json.load(f)

        assert len(loaded_records) == 2
        assert loaded_records[0]["batch_id"] == 1
        assert loaded_records[1]["batch_id"] == 2
    finally:
        os.unlink(temp_path)


def test_get_peak_ram_for_batch():
    """Test retrieving peak RAM for a specific batch."""
    records = [
        {"batch_id": 1, "peak_process_ram_mb": 150.0},
        {"batch_id": 2, "peak_process_ram_mb": 200.0},
    ]

    assert get_peak_ram_for_batch(records, 1) == 150.0
    assert get_peak_ram_for_batch(records, 2) == 200.0
    assert get_peak_ram_for_batch(records, 999) is None
