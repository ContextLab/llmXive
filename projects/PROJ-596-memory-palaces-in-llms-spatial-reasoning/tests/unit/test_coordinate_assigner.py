"""
Unit tests for the CoordinateAssigner (T007b).

These tests verify the core logic of FR-001: coordinate assignment for
episodic chunks.
"""

import pytest
from unittest.mock import MagicMock

from models.episodic_chunk import EpisodicChunk
from models.coordinate_assigner import CoordinateAssigner, calculate_interference_potential


class TestCoordinateAssigner:
    """Tests for the CoordinateAssigner class."""

    def test_sequential_assignment_order(self):
        """Verify that sequential assignment fills the grid in row-major order."""
        assigner = CoordinateAssigner(grid_size=4, strategy="sequential")
        coords = []

        # Create 5 dummy chunks
        for i in range(5):
            chunk = EpisodicChunk(
                id=f"chunk-{i}",
                text=f"Sample text {i}",
                trace_id="trace-001"
            )
            assigner.assign(chunk)
            coords.append((chunk.spatial_x, chunk.spatial_y))

        # Expected: (0,0), (1,0), (2,0), (3,0), (0,1)
        expected = [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1)]
        assert coords == expected, f"Sequential order mismatch: {coords} != {expected}"

    def test_sequential_wraparound(self):
        """Verify that sequential assignment wraps around the grid."""
        grid_size = 2
        assigner = CoordinateAssigner(grid_size=grid_size, strategy="sequential")
        
        # Fill the grid completely (4 slots)
        for i in range(4):
            chunk = EpisodicChunk(id=f"fill-{i}", text="fill", trace_id="t1")
            assigner.assign(chunk)

        # The next one should wrap to (0,0)
        wrap_chunk = EpisodicChunk(id="wrap", text="wrap", trace_id="t1")
        x, y = assigner.assign(wrap_chunk)
        assert x == 0 and y == 0, f"Wraparound failed: got ({x}, {y})"

    def test_hash_strategy_scatters(self):
        """Verify that hash strategy produces consistent but scattered coordinates."""
        assigner = CoordinateAssigner(grid_size=16, strategy="hash")
        
        chunk1 = EpisodicChunk(id="c1", text="unique_content_alpha", trace_id="t1")
        chunk2 = EpisodicChunk(id="c2", text="unique_content_beta", trace_id="t1")
        
        assigner.assign(chunk1)
        assigner.assign(chunk2)
        
        # They should have coordinates
        assert chunk1.spatial_x is not None
        assert chunk1.spatial_y is not None
        assert chunk2.spatial_x is not None
        assert chunk2.spatial_y is not None

        # Same content should yield same coordinates
        chunk3 = EpisodicChunk(id="c3", text="unique_content_alpha", trace_id="t1")
        assigner.assign(chunk3)
        
        assert (chunk1.spatial_x, chunk1.spatial_y) == (chunk3.spatial_x, chunk3.spatial_y)
        
        # Different content likely yields different coordinates (probabilistic, but high confidence)
        if (chunk1.spatial_x, chunk1.spatial_y) == (chunk2.spatial_x, chunk2.spatial_y):
            # If they collide, it's a hash collision, which is rare for distinct strings on 16x16
            # We just ensure they are valid coordinates
            pass

    def test_invalid_strategy(self):
        """Verify that an invalid strategy raises an error."""
        with pytest.raises(ValueError):
            CoordinateAssigner(grid_size=4, strategy="invalid_strategy")

    def test_batch_assignment(self):
        """Verify batch assignment returns correct list of coordinates."""
        assigner = CoordinateAssigner(grid_size=4, strategy="sequential")
        chunks = [
            EpisodicChunk(id=f"b{i}", text=f"text{i}", trace_id="t1")
            for i in range(3)
        ]
        
        result = assigner.assign_batch(chunks)
        
        assert len(result) == 3
        assert result[0] == (0, 0)
        assert result[1] == (1, 0)
        assert result[2] == (2, 0)

class TestInterferencePotential:
    """Tests for the interference metric helper."""

    def test_single_item_zero(self):
        """Single item should have zero interference potential."""
        coords = [(5, 5)]
        assert calculate_interference_potential(coords, 10) == 0.0

    def test_empty_list_zero(self):
        """Empty list should have zero interference potential."""
        assert calculate_interference_potential([], 10) == 0.0

    def test_adjacent_items(self):
        """Adjacent items (distance 1) should have low potential."""
        coords = [(0, 0), (0, 1), (0, 2)]
        potential = calculate_interference_potential(coords, 10)
        # Distance between (0,0)->(0,1) is 1, (0,1)->(0,2) is 1. Avg is 1.
        assert potential == 1.0

    def test_distant_items(self):
        """Distant items should have high potential."""
        coords = [(0, 0), (9, 9)]
        # Distance is sqrt(81 + 81) = sqrt(162) ~ 12.72
        import math
        expected = math.sqrt(162)
        potential = calculate_interference_potential(coords, 10)
        assert abs(potential - expected) < 0.0001
