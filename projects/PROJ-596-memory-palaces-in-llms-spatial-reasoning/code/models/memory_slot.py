"""
Memory Slot Data Structures for Spatial Memory in LLMs.

Implements 2-D grid memory slots that serve as addressable locations
for episodic traces, following the Memory Palace methodology.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import math


@dataclass
class MemorySlot:
    """
    Represents a single addressable location in the 2-D spatial memory grid.

    Each slot holds a reference to an episodic chunk and metadata about
    its spatial position and occupancy state.

    Attributes:
        row: Row coordinate in the 2-D grid (0-indexed).
        col: Column coordinate in the 2-D grid (0-indexed).
        is_occupied: Whether this slot currently holds an episodic trace.
        occupancy_count: Number of times this slot has been written to (for decay).
        last_access_time: Logical timestamp of last access (for eviction policies).
        chunk_id: Optional reference to the EpisodicChunk stored here.
        metadata: Additional slot-specific metadata.
    """
    row: int
    col: int
    is_occupied: bool = False
    occupancy_count: int = 0
    last_access_time: int = 0
    chunk_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def coordinate(self) -> tuple:
        """Return the (row, col) coordinate tuple."""
        return (self.row, self.col)

    @property
    def distance_from_origin(self) -> float:
        """Calculate Euclidean distance from grid origin (0,0)."""
        return math.sqrt(self.row ** 2 + self.col ** 2)

    def activate(self, chunk_id: str, timestamp: int) -> None:
        """Mark this slot as occupied and update access metadata."""
        self.is_occupied = True
        self.occupancy_count += 1
        self.last_access_time = timestamp
        self.chunk_id = chunk_id

    def deactivate(self) -> None:
        """Mark this slot as empty and clear chunk reference."""
        self.is_occupied = False
        self.chunk_id = None


@dataclass
class MemoryGrid:
    """
    A 2-D grid of MemorySlot instances representing the Memory Palace.

    The grid provides spatial addressing for episodic memories, with
    methods for slot lookup, coordinate mapping, and occupancy analysis.

    Attributes:
        width: Number of columns in the grid.
        height: Number of rows in the grid.
        slots: 2-D list of MemorySlot instances.
        total_slots: Total number of slots (width * height).
        occupied_count: Current number of occupied slots.
    """
    width: int
    height: int
    slots: List[List[MemorySlot]] = field(init=False)
    total_slots: int = field(init=False)
    occupied_count: int = field(init=False, default=0)

    def __post_init__(self):
        """Initialize the grid with empty slots."""
        self.slots = [
            [MemorySlot(row=r, col=c) for c in range(self.width)]
            for r in range(self.height)
        ]
        self.total_slots = self.width * self.height
        self.occupied_count = 0

    def get_slot(self, row: int, col: int) -> MemorySlot:
        """
        Retrieve a slot by coordinate.

        Args:
            row: Row index (0 to height-1).
            col: Column index (0 to width-1).

        Returns:
            The MemorySlot at the given coordinates.

        Raises:
            IndexError: If coordinates are out of bounds.
        """
        if not (0 <= row < self.height and 0 <= col < self.width):
            raise IndexError(
                f"Coordinate ({row}, {col}) out of bounds for grid "
                f"of size {self.height}x{self.width}"
            )
        return self.slots[row][col]

    def get_slot_by_index(self, index: int) -> MemorySlot:
        """
        Retrieve a slot by flat index (row-major order).

        Args:
            index: Flat index from 0 to total_slots-1.

        Returns:
            The MemorySlot at the given index.

        Raises:
            IndexError: If index is out of bounds.
        """
        if not (0 <= index < self.total_slots):
            raise IndexError(
                f"Index {index} out of bounds for grid with "
                f"{self.total_slots} slots"
            )
        row = index // self.width
        col = index % self.width
        return self.get_slot(row, col)

    def find_nearest_empty_slot(self, start_row: int, start_col: int) -> Optional[MemorySlot]:
        """
        Find the nearest empty slot using spiral search from a starting point.

        This implements a biologically-inspired search pattern that explores
        nearby locations first before expanding outward.

        Args:
            start_row: Starting row coordinate.
            start_col: Starting column coordinate.

        Returns:
            The nearest empty MemorySlot, or None if all slots are occupied.
        """
        # Spiral offsets: right, down, left, up (expanding outward)
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        # Check the starting position first
        if 0 <= start_row < self.height and 0 <= start_col < self.width:
            slot = self.get_slot(start_row, start_col)
            if not slot.is_occupied:
                return slot

        # Spiral search
        radius = 1
        while radius <= max(self.height, self.width):
            # Move right along the top edge of the current radius
            for c in range(max(0, start_col - radius), min(self.width, start_col + radius + 1)):
                if 0 <= start_row < self.height:
                    slot = self.get_slot(start_row, c)
                    if not slot.is_occupied:
                        return slot

            # Move down along the right edge
            for r in range(max(0, start_row - radius), min(self.height, start_row + radius + 1)):
                if 0 <= start_col + radius < self.width:
                    slot = self.get_slot(r, start_col + radius)
                    if not slot.is_occupied:
                        return slot

            # Move left along the bottom edge
            for c in range(min(self.width - 1, start_col + radius), max(-1, start_col - radius - 1), -1):
                if 0 <= start_row + radius < self.height:
                    slot = self.get_slot(start_row + radius, c)
                    if not slot.is_occupied:
                        return slot

            # Move up along the left edge
            for r in range(min(self.height - 1, start_row + radius), max(-1, start_row - radius - 1), -1):
                if 0 <= start_col - radius < self.width:
                    slot = self.get_slot(r, start_col - radius)
                    if not slot.is_occupied:
                        return slot

            radius += 1

        return None

    def get_occupied_slots(self) -> List[MemorySlot]:
        """Return a list of all occupied slots."""
        return [
            slot for row in self.slots for slot in row if slot.is_occupied
        ]

    def get_occupancy_rate(self) -> float:
        """Calculate the fraction of occupied slots."""
        if self.total_slots == 0:
            return 0.0
        return sum(1 for row in self.slots for slot in row if slot.is_occupied) / self.total_slots

    def get_occupancy_distribution(self) -> Dict[int, int]:
        """
        Get distribution of occupancy counts across slots.

        Returns:
            Dictionary mapping occupancy_count to number of slots with that count.
        """
        distribution = {}
        for row in self.slots:
            for slot in row:
                if slot.is_occupied:
                    count = slot.occupancy_count
                    distribution[count] = distribution.get(count, 0) + 1
        return distribution

    def clear_all(self) -> None:
        """Reset all slots to empty state."""
        for row in self.slots:
            for slot in row:
                slot.deactivate()
        self.occupied_count = 0

    def __repr__(self) -> str:
        return (
            f"MemoryGrid(width={self.width}, height={self.height}, "
            f"occupied={self.occupied_count}/{self.total_slots})"
        )
