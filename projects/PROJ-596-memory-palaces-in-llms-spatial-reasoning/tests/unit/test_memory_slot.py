"""
Unit tests for MemorySlot and MemoryGrid data structures.

Tests verify correct initialization, coordinate access, occupancy tracking,
and search algorithms for the spatial memory implementation.
"""
import pytest
from code.models.memory_slot import MemorySlot, MemoryGrid


class TestMemorySlot:
    """Tests for the MemorySlot dataclass."""

    def test_initialization(self):
        """Test that a MemorySlot initializes with correct defaults."""
        slot = MemorySlot(row=2, col=3)
        assert slot.row == 2
        assert slot.col == 3
        assert slot.is_occupied is False
        assert slot.occupancy_count == 0
        assert slot.chunk_id is None

    def test_coordinate_property(self):
        """Test the coordinate property returns correct tuple."""
        slot = MemorySlot(row=5, col=7)
        assert slot.coordinate == (5, 7)

    def test_distance_from_origin(self):
        """Test Euclidean distance calculation."""
        slot = MemorySlot(row=3, col=4)
        assert slot.distance_from_origin == 5.0  # 3-4-5 triangle

    def test_activate(self):
        """Test activating a slot updates all required fields."""
        slot = MemorySlot(row=1, col=1)
        slot.activate(chunk_id="test-123", timestamp=1000)

        assert slot.is_occupied is True
        assert slot.occupancy_count == 1
        assert slot.last_access_time == 1000
        assert slot.chunk_id == "test-123"

    def test_activate_multiple_times(self):
        """Test that multiple activations increment occupancy count."""
        slot = MemorySlot(row=1, col=1)
        slot.activate(chunk_id="test-123", timestamp=1000)
        slot.activate(chunk_id="test-456", timestamp=2000)

        assert slot.occupancy_count == 2
        assert slot.last_access_time == 2000
        assert slot.chunk_id == "test-456"

    def test_deactivate(self):
        """Test deactivating a slot clears occupancy."""
        slot = MemorySlot(row=1, col=1)
        slot.activate(chunk_id="test-123", timestamp=1000)
        slot.deactivate()

        assert slot.is_occupied is False
        assert slot.chunk_id is None


class TestMemoryGrid:
    """Tests for the MemoryGrid class."""

    def test_initialization(self):
        """Test grid initializes with correct dimensions and empty slots."""
        grid = MemoryGrid(width=3, height=3)
        assert grid.width == 3
        assert grid.height == 3
        assert grid.total_slots == 9
        assert grid.occupied_count == 0

        # Verify all slots are empty
        for row in grid.slots:
            for slot in row:
                assert slot.is_occupied is False

    def test_get_slot(self):
        """Test retrieving a slot by coordinate."""
        grid = MemoryGrid(width=5, height=5)
        slot = grid.get_slot(2, 3)
        assert slot.row == 2
        assert slot.col == 3

    def test_get_slot_out_of_bounds(self):
        """Test that out-of-bounds coordinates raise IndexError."""
        grid = MemoryGrid(width=3, height=3)
        with pytest.raises(IndexError):
            grid.get_slot(3, 0)
        with pytest.raises(IndexError):
            grid.get_slot(0, 3)
        with pytest.raises(IndexError):
            grid.get_slot(-1, 0)

    def test_get_slot_by_index(self):
        """Test flat index to slot retrieval."""
        grid = MemoryGrid(width=3, height=3)
        # Index 4 should be at row 1, col 1 (row-major order)
        slot = grid.get_slot_by_index(4)
        assert slot.row == 1
        assert slot.col == 1

    def test_get_slot_by_index_out_of_bounds(self):
        """Test that out-of-bounds index raises IndexError."""
        grid = MemoryGrid(width=3, height=3)
        with pytest.raises(IndexError):
            grid.get_slot_by_index(9)
        with pytest.raises(IndexError):
            grid.get_slot_by_index(-1)

    def test_find_nearest_empty_slot_from_occupied(self):
        """Test finding nearest empty slot when starting from occupied."""
        grid = MemoryGrid(width=5, height=5)
        # Occupy the center
        center_slot = grid.get_slot(2, 2)
        center_slot.activate("chunk-1", 1000)

        # Find nearest empty from center
        nearest = grid.find_nearest_empty_slot(2, 2)
        assert nearest is not None
        assert nearest.is_occupied is False
        # Should be adjacent to center
        assert abs(nearest.row - 2) + abs(nearest.col - 2) == 1

    def test_find_nearest_empty_slot_full_grid(self):
        """Test that None is returned when grid is full."""
        grid = MemoryGrid(width=2, height=2)
        # Occupy all slots
        for row in range(2):
            for col in range(2):
                grid.get_slot(row, col).activate(f"chunk-{row}-{col}", 1000)

        nearest = grid.find_nearest_empty_slot(0, 0)
        assert nearest is None

    def test_get_occupied_slots(self):
        """Test retrieving list of occupied slots."""
        grid = MemoryGrid(width=3, height=3)
        grid.get_slot(0, 0).activate("chunk-1", 1000)
        grid.get_slot(1, 2).activate("chunk-2", 2000)

        occupied = grid.get_occupied_slots()
        assert len(occupied) == 2
        coordinates = [(s.row, s.col) for s in occupied]
        assert (0, 0) in coordinates
        assert (1, 2) in coordinates

    def test_get_occupancy_rate(self):
        """Test occupancy rate calculation."""
        grid = MemoryGrid(width=4, height=4)
        assert grid.get_occupancy_rate() == 0.0

        # Occupy 4 out of 16 slots
        for i in range(4):
            grid.get_slot(i // 4, i % 4).activate(f"chunk-{i}", 1000)

        assert grid.get_occupancy_rate() == 0.25

    def test_clear_all(self):
        """Test clearing all slots in the grid."""
        grid = MemoryGrid(width=3, height=3)
        for row in range(3):
            for col in range(3):
                grid.get_slot(row, col).activate(f"chunk-{row}-{col}", 1000)

        assert grid.get_occupied_slots()
        grid.clear_all()

        assert grid.occupied_count == 0
        assert len(grid.get_occupied_slots()) == 0

    def test_repr(self):
        """Test string representation."""
        grid = MemoryGrid(width=5, height=5)
        grid.get_slot(0, 0).activate("test", 1000)
        repr_str = repr(grid)
        assert "MemoryGrid" in repr_str
        assert "width=5" in repr_str
        assert "height=5" in repr_str
        assert "occupied=1/25" in repr_str
