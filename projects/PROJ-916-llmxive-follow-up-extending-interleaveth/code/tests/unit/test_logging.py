"""
Unit tests for logging infrastructure (T006).
"""
import time
import pytest
from src.utils.logging import (
    MemorySnapshot,
    StepTimer,
    RAMTracker,
    track_step,
    start_tracing,
    logger
)
import tracemalloc


def test_memory_snapshot_update():
    """Test that MemorySnapshot correctly updates values."""
    # Ensure tracing is on
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    
    snapshot = MemorySnapshot()
    snapshot.update()
    
    assert snapshot.current >= 0
    assert snapshot.peak >= 0
    assert snapshot.current_mb >= 0
    assert snapshot.peak_mb >= 0
    assert snapshot.timestamp is not None


def test_step_timer_success():
    """Test StepTimer records duration on successful execution."""
    # Capture log output (mocked via logger level check)
    with StepTimer("test_step") as timer:
        time.sleep(0.05)  # Sleep for 50ms
    
    assert timer.duration is not None
    assert timer.duration >= 0.05
    assert timer.step_name == "test_step"


def test_ram_tracker_context():
    """Test RAMTracker captures start and end memory."""
    if not tracemalloc.is_tracing():
        tracemalloc.start()

    with RAMTracker("memory_test") as tracker:
        # Allocate some memory
        _ = [0] * 100000
    
    assert tracker.snapshot_start is not None
    assert tracker.snapshot_end is not None
    assert tracker.snapshot_end.current >= tracker.snapshot_start.current


def test_track_step_integration():
    """Test the full track_step context manager."""
    if not tracemalloc.is_tracing():
        tracemalloc.start()

    results = {}
    with track_step("integration_test") as metrics:
        time.sleep(0.01)
        # Allocate memory
        _ = [0] * 50000
        results["captured"] = True
    
    assert results.get("captured") is True
    assert metrics["step_name"] == "integration_test"
    assert metrics["success"] is True
    assert metrics["duration_s"] > 0
    assert metrics["ram_start_mb"] >= 0
    assert metrics["ram_end_mb"] >= 0
    # Delta might be negative if garbage collected, but should be a number
    assert isinstance(metrics["ram_delta_mb"], float)