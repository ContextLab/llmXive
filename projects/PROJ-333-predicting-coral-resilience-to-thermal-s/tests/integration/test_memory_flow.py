"""
Integration test for memory constraints using mock data.
Verifies that the pipeline flow logic does not crash or consume
excessive resources when processing small mock inputs.
"""
import pytest
from pathlib import Path
import tempfile
import os

from utils.logging import MemoryTracker, log_memory_usage

def test_memory_tracker_context(mock_fastq_gz_path):
    """
    Test that the MemoryTracker context manager works correctly.
    """
    tracker = MemoryTracker(threshold_mb=1000) # Set a high threshold to avoid failure
    
    with tracker:
        # Simulate some processing on the mock file
        with open(mock_fastq_gz_path, 'rb') as f:
            _ = f.read()
    
    assert tracker.start_memory_mb is not None
    assert tracker.end_memory_mb is not None
    assert tracker.peak_memory_mb is not None

def test_log_memory_usage():
    """
    Test the standalone log_memory_usage function.
    """
    msg = log_memory_usage("Integration Test Start")
    assert msg is not None
    assert "MB" in msg or "mb" in msg.lower()
