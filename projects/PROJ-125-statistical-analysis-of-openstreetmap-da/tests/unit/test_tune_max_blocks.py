"""
Unit tests for the MAX_BLOCKS tuning logic (T038b).
"""
import sys
from pathlib import Path
import pytest
import math

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.scripts.tune_max_blocks import (
    _theoretical_memory_per_block,
    calculate_max_blocks,
    TARGET_MEMORY_MB,
    SAFETY_FACTOR
)

class TestMemoryEstimation:
    def test_theoretical_memory_per_block_positive(self):
        """Test that theoretical memory estimation returns a positive value."""
        mem = _theoretical_memory_per_block()
        assert mem > 0, "Memory per block must be positive"

    def test_theoretical_memory_order_of_magnitude(self):
        """
        Verify the order of magnitude is reasonable.
        A 1km block at 30m resolution is ~1.2M pixels.
        6 layers * 1.2M * 8 bytes = ~57MB raw.
        With 2x overhead, we expect ~115MB.
        Allow a factor of 2 tolerance for implementation differences.
        """
        mem = _theoretical_memory_per_block()
        expected_raw = 1111 * 1111 * 6 * 8 / (1024**2) # ~57.6 MB
        expected_with_overhead = expected_raw * 2.0
        
        # Check within 50% tolerance
        assert 0.5 * expected_with_overhead < mem < 1.5 * expected_with_overhead

class TestMaxBlocksCalculation:
    def test_calculate_max_blocks_basic(self):
        """Test basic calculation of max blocks."""
        # If memory per block is 100MB, and limit is 6144MB * 0.9 = 5529.6
        # Max blocks should be floor(5529.6 / 100) = 55
        mem_per_block = 100.0
        result = calculate_max_blocks(mem_per_block)
        expected = int((TARGET_MEMORY_MB * SAFETY_FACTOR) / mem_per_block)
        assert result == expected

    def test_calculate_max_blocks_small_block(self):
        """Test with a very small block size (high block count)."""
        mem_per_block = 10.0 # 10 MB per block
        result = calculate_max_blocks(mem_per_block)
        expected = int((TARGET_MEMORY_MB * SAFETY_FACTOR) / mem_per_block)
        assert result == expected

    def test_calculate_max_blocks_large_block(self):
        """Test with a large block size (low block count)."""
        mem_per_block = 6000.0 # Larger than target limit
        result = calculate_max_blocks(mem_per_block)
        # Should return at least 1
        assert result >= 1

    def test_calculate_max_blocks_zero_memory(self):
        """Test handling of zero/negative memory estimate."""
        result = calculate_max_blocks(0.0)
        assert result == 1, "Should return minimum of 1 block"

        result = calculate_max_blocks(-10.0)
        assert result == 1, "Should return minimum of 1 block for negative"

class TestSafetyThreshold:
    def test_target_memory_is_6gb(self):
        """Verify the target memory constant is 6GB in MB."""
        assert TARGET_MEMORY_MB == 6144

    def test_safety_factor_applied(self):
        """Verify safety factor is less than 1.0."""
        assert 0.0 < SAFETY_FACTOR < 1.0
        assert SAFETY_FACTOR == 0.9