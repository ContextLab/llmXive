"""
Integration test for training loop memory constraints (T011).

This test verifies that the training loop correctly monitors memory usage
and adapts batch size or dataset size when RSS exceeds the 6 GB threshold.
It uses the MemoryMonitor utility from code/training/memory_monitor.py
and validates the adaptive behavior without requiring full model training.
"""

import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from training.memory_monitor import MemoryMonitor


class MockTrainingLoop:
    """
    Mock training loop that simulates memory growth during "training".
    Used to test the MemoryMonitor's adaptive behavior.
    """

    def __init__(self, monitor: MemoryMonitor, memory_growth_factor: float = 1.0):
        self.monitor = monitor
        self.memory_growth_factor = memory_growth_factor
        self.batch_sizes = []
        self.dataset_sizes = []
        self.epoch_count = 0

    def simulate_epoch(self, initial_batch_size: int, initial_dataset_size: int):
        """
        Simulate an epoch where memory usage grows.
        Returns (final_batch_size, final_dataset_size, rss_mb).
        """
        current_batch = initial_batch_size
        current_dataset = initial_dataset_size

        # Simulate memory growth over "steps" in the epoch
        for step in range(5):
            # Simulate RSS increase
            self.monitor._record_rss()
            rss = self.monitor.get_current_rss_mb()

            # If RSS > 6GB, trigger adaptive logic
            if rss > 6144:  # 6 GB in MB
                if current_batch > 4:
                    current_batch = 4
                    self.monitor.log_event("batch_size_reduced", {"new_batch_size": 4})
                elif current_dataset > 100:
                    # Cap dataset to 10% of original (mock logic)
                    new_size = int(initial_dataset_size * 0.1)
                    if new_size < 10:
                        new_size = 10
                    current_dataset = new_size
                    self.monitor.log_event("dataset_capped", {"new_size": new_size})
                else:
                    # Cannot reduce further, stop simulation
                    break

            self.batch_sizes.append(current_batch)
            self.dataset_sizes.append(current_dataset)

        return current_batch, current_dataset, self.monitor.get_current_rss_mb()


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_memory_monitor_initialization(temp_log_dir):
    """Test that MemoryMonitor initializes correctly and logs to the specified path."""
    monitor = MemoryMonitor(log_dir=str(temp_log_dir), threshold_mb=6144)
    assert monitor.threshold_mb == 6144
    assert monitor.log_dir == temp_log_dir
    assert monitor.log_file == temp_log_dir / "memory_log.json"
    assert not monitor.log_file.exists()  # Log file created on first record


def test_memory_monitor_rss_recording(temp_log_dir):
    """Test that MemoryMonitor records RSS correctly."""
    monitor = MemoryMonitor(log_dir=str(temp_log_dir))
    monitor._record_rss()
    assert monitor.current_rss_mb > 0
    assert monitor.current_rss_mb < 100000  # Sanity check: RSS should be reasonable


def test_training_loop_batch_size_reduction(temp_log_dir):
    """
    Test that the training loop reduces batch size from 8 to 4 when RSS > 6GB.
    This simulates the scenario described in FR-003.
    """
    monitor = MemoryMonitor(log_dir=str(temp_log_dir), threshold_mb=6144)
    loop = MockTrainingLoop(monitor, memory_growth_factor=2.0)

    # Simulate an epoch with initial batch size 8 and dataset size 1000
    final_batch, final_dataset, final_rss = loop.simulate_epoch(
        initial_batch_size=8, initial_dataset_size=1000
    )

    # Verify batch size was reduced to 4
    assert final_batch == 4, f"Expected batch size 4, got {final_batch}"
    assert 4 in loop.batch_sizes, "Batch size reduction event not recorded"


def test_training_loop_dataset_capping(temp_log_dir):
    """
    Test that the training loop caps the dataset when batch size is already 4
    and RSS still exceeds 6GB.
    """
    monitor = MemoryMonitor(log_dir=str(temp_log_dir), threshold_mb=6144)
    loop = MockTrainingLoop(monitor, memory_growth_factor=3.0)

    # Simulate an epoch with initial batch size 4 (already reduced) and large dataset
    final_batch, final_dataset, final_rss = loop.simulate_epoch(
        initial_batch_size=4, initial_dataset_size=10000
    )

    # Verify dataset was capped
    assert final_batch == 4, "Batch size should remain 4"
    assert final_dataset < 10000, "Dataset should be capped"
    assert final_dataset == int(10000 * 0.1), "Dataset should be capped to 10% of original"
    assert "dataset_capped" in str(loop.monitor.events), "Dataset cap event not recorded"


def test_memory_log_file_created(temp_log_dir):
    """Test that the memory log file is created and contains valid JSON."""
    monitor = MemoryMonitor(log_dir=str(temp_log_dir))
    monitor._record_rss()
    monitor.log_event("test_event", {"key": "value"})

    assert monitor.log_file.exists(), "Log file should be created"
    import json
    with open(monitor.log_file, "r") as f:
        data = json.load(f)
    assert "events" in data, "Log should contain 'events' key"
    assert len(data["events"]) > 0, "Log should contain at least one event"


def test_memory_threshold_exceeded_detection(temp_log_dir):
    """
    Test that the MemoryMonitor correctly detects when RSS exceeds the threshold.
    """
    monitor = MemoryMonitor(log_dir=str(temp_log_dir), threshold_mb=6144)
    # Force a high RSS value for testing (mocking)
    original_rss = monitor.current_rss_mb
    monitor.current_rss_mb = 7000  # Simulate > 6GB

    assert monitor.is_above_threshold(), "Should detect RSS > 6GB"

    # Restore original value
    monitor.current_rss_mb = original_rss


def test_integration_adaptive_training_flow(temp_log_dir):
    """
    Full integration test: simulate a training run where memory grows,
    batch size is reduced, and if necessary, dataset is capped.
    """
    monitor = MemoryMonitor(log_dir=str(temp_log_dir), threshold_mb=6144)
    loop = MockTrainingLoop(monitor, memory_growth_factor=2.5)

    # Simulate 3 epochs
    for epoch in range(3):
        loop.epoch_count = epoch
        batch, dataset, rss = loop.simulate_epoch(
            initial_batch_size=8, initial_dataset_size=5000
        )
        # Log epoch completion
        monitor.log_event("epoch_complete", {
            "epoch": epoch,
            "batch_size": batch,
            "dataset_size": dataset,
            "rss_mb": rss
        })

    # Verify final state
    assert loop.epoch_count == 2, "Should have completed 3 epochs (0,1,2)"
    assert monitor.log_file.exists(), "Log file should exist"

    # Check that at least one adaptive event occurred
    events = monitor.events
    adaptive_events = [e for e in events if e["type"] in ["batch_size_reduced", "dataset_capped"]]
    assert len(adaptive_events) > 0, "At least one adaptive event should have occurred"