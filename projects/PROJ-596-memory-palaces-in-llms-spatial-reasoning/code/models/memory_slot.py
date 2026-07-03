"""
2-D grid memory slot data structures for the Memory Palace architecture.

Implements the spatial indexing mechanism where episodic traces are deposited
into a fixed 2D grid, mimicking the place cell organization in the hippocampus.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import torch
import numpy as np


@dataclass
class MemorySlot:
    """
    Represents a single slot in the 2D memory grid.

    Each slot can hold a vector of information (embedding) and metadata about
    occupancy and retrieval frequency.
    """
    coordinate: tuple[int, int]
    embedding: Optional[torch.Tensor] = None
    occupancy_count: int = 0
    last_accessed: int = -1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_occupied(self) -> bool:
        return self.embedding is not None

    def update_embedding(self, embedding: torch.Tensor) -> None:
        """Update the embedding in this slot, accumulating if necessary."""
        if self.embedding is None:
            self.embedding = embedding.clone()
        else:
            # Simple accumulation or replacement strategy could be parameterized
            # For now, we average to smooth the memory trace (biological consolidation)
            self.embedding = (self.embedding + embedding) / 2.0
        self.occupancy_count += 1

    def retrieve(self) -> Optional[torch.Tensor]:
        """Retrieve the content of this slot."""
        return self.embedding.clone() if self.embedding is not None else None


@dataclass
class MemoryGrid:
    """
    A 2D grid of MemorySlots acting as the spatial memory palace.

    This structure provides the "address" (coordinate) vs "content" (embedding)
    distinction required for spatial reasoning.
    """
    rows: int
    cols: int
    slot_dim: int
    slots: List[MemorySlot] = field(default_factory=list)
    occupancy_map: Optional[torch.Tensor] = None  # Binary mask of occupied slots

    def __post_init__(self):
        self._initialize_grid()

    def _initialize_grid(self) -> None:
        """Initialize the 2D grid with empty slots."""
        self.slots = []
        for r in range(self.rows):
            for c in range(self.cols):
                self.slots.append(MemorySlot(coordinate=(r, c)))
        
        # Pre-allocate occupancy map for efficiency
        self.occupancy_map = torch.zeros((self.rows, self.cols), dtype=torch.bool)

    def get_slot(self, row: int, col: int) -> MemorySlot:
        """Retrieve a specific slot by coordinate."""
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise IndexError(f"Coordinate ({row}, {col}) out of bounds for grid {self.rows}x{self.cols}")
        index = row * self.cols + col
        return self.slots[index]

    def set_occupancy(self, row: int, col: int, occupied: bool) -> None:
        """Update the occupancy map for a specific coordinate."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.occupancy_map[row, col] = occupied

    def get_occupancy_rate(self) -> float:
        """Calculate the percentage of occupied slots."""
        return float(self.occupancy_map.sum().item()) / (self.rows * self.cols)

    def get_neighboring_slots(self, row: int, col: int, radius: int = 1) -> List[MemorySlot]:
        """Retrieve all slots within a given radius of a coordinate."""
        neighbors = []
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    neighbors.append(self.get_slot(nr, nc))
        return neighbors

    def to_tensor(self) -> torch.Tensor:
        """
        Convert the grid embeddings into a single tensor for model input.
        Shape: (rows * cols, slot_dim)
        """
        embeddings = []
        for slot in self.slots:
            if slot.embedding is not None:
                embeddings.append(slot.embedding)
            else:
                # Use zero vector for empty slots
                embeddings.append(torch.zeros(self.slot_dim))
        return torch.stack(embeddings, dim=0)
