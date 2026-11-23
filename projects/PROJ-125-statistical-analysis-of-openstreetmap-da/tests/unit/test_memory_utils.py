"""
Unit tests for code/utils/memory.py
Verifies that the memory safety utilities work correctly with the tuned MAX_BLOCKS.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.memory import (
    estimate_array_memory_mb,
    estimate_raster_memory_mb,
    check_memory_safety,
    generate_spatial_blocks
)
from code.config import MAX_BLOCKS, MEMORY_LIMIT_MB

def test_estimate_array_memory_mb():
    """Test memory estimation for a numpy array."""
    # 1000x1000 float64 array = 8MB
    arr = np.zeros((1000, 1000), dtype=np.float64)
    est_mb = estimate_array_memory_mb(arr)
    assert abs(est_mb - 8.0) < 0.1

def test_estimate_raster_memory_mb():
    """Test memory estimation for a hypothetical raster."""
    # 10000x10000 pixels, 1 band, float32
    est_mb = estimate_raster_memory_mb(width=10000, height=10000, bands=1, dtype=np.float32)
    # 100M pixels * 4 bytes = 400MB
    assert abs(est_mb - 400.0) < 1.0

def test_check_memory_safety():
    """Test that check_memory_safety returns True for small data."""
    # Simulate a small dataset
    is_safe, reason = check_memory_safety(estimated_mb=100, limit_mb=MEMORY_LIMIT_MB)
    assert is_safe
    assert reason is None

def test_check_memory_safety_exceeded():
    """Test that check_memory_safety returns False for large data."""
    # Simulate a dataset exceeding 6GB
    is_safe, reason = check_memory_safety(estimated_mb=7000, limit_mb=MEMORY_LIMIT_MB)
    assert not is_safe
    assert "exceeds" in reason.lower()

def test_generate_spatial_blocks_count():
    """
    Test that generate_spatial_blocks respects MAX_BLOCKS.
    This verifies the interaction between config tuning and utility logic.
    """
    # Simulate a grid of 1000x1000 blocks
    # The function should limit the output to MAX_BLOCKS
    blocks = generate_spatial_blocks(
        grid_width=1000, 
        grid_height=1000, 
        max_blocks=MAX_BLOCKS
    )
    assert len(blocks) <= MAX_BLOCKS
    assert len(blocks) > 0
