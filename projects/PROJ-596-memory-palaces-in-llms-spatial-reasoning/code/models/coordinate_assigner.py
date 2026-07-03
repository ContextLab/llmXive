"""
Coordinate assignment logic for episodic chunks (FR-001).

This module implements the spatial indexing strategy for episodic memories.
It assigns 2D grid coordinates to EpisodicChunk instances based on their
semantic content or sequential position, enabling the "Memory Palace" structure.
"""

import math
from typing import List, Optional, Tuple, Dict, Any
import hashlib
import numpy as np

from models.episodic_chunk import EpisodicChunk
from models.memory_slot import MemoryGrid


class CoordinateAssigner:
    """
    Assigns 2D spatial coordinates (x, y) to episodic chunks.

    Strategy:
    1.  **Sequential Filling**: Chunks are assigned to grid cells in a
        row-major order (left-to-right, top-to-bottom) to maximize
        spatial locality for sequential data (like bAbI stories).
    2.  **Hash-based Scattering**: For non-sequential or high-interference
        scenarios, a hash of the content is used to scatter items across
        the grid to minimize local collisions.

    The assigner updates the `episodic_chunk` object in-place to store
    the assigned coordinates.
    """

    def __init__(self, grid_size: int = 16, strategy: str = "sequential"):
        """
        Initialize the coordinate assigner.

        Args:
            grid_size: The dimension of the square grid (e.g., 16x16 = 256 slots).
            strategy: "sequential" for row-major filling, "hash" for scattering.
        """
        self.grid_size = grid_size
        self.total_slots = grid_size * grid_size
        self.strategy = strategy
        self._current_index = 0

        if strategy not in ("sequential", "hash"):
            raise ValueError(f"Unknown strategy: {strategy}. Must be 'sequential' or 'hash'.")

    def _get_sequential_coords(self) -> Tuple[int, int]:
        """Calculate coordinates for the next sequential slot."""
        x = self._current_index % self.grid_size
        y = self._current_index // self.grid_size
        self._current_index += 1

        # Wrap around if we exceed grid capacity (circular buffer behavior)
        if self._current_index >= self.total_slots:
            self._current_index = 0

        return x, y

    def _get_hash_coords(self, content: str) -> Tuple[int, int]:
        """Calculate coordinates based on content hash to scatter items."""
        # Use SHA-256 for a robust hash, then mod grid size
        h = hashlib.sha256(content.encode('utf-8')).hexdigest()
        # Take first 8 hex chars for a 32-bit integer
        val = int(h[:8], 16)

        x = val % self.grid_size
        y = (val >> 16) % self.grid_size
        return x, y

    def assign(self, chunk: EpisodicChunk) -> Tuple[int, int]:
        """
        Assign coordinates to a single episodic chunk.

        Args:
            chunk: The EpisodicChunk instance to update.

        Returns:
            A tuple (x, y) representing the assigned grid coordinates.
        """
        if self.strategy == "sequential":
            x, y = self._get_sequential_coords()
        elif self.strategy == "hash":
            # Fallback to a placeholder if content is missing, though unlikely in valid data
            content = chunk.text if hasattr(chunk, 'text') and chunk.text else str(chunk.id)
            x, y = self._get_hash_coords(content)
        else:
            raise RuntimeError(f"Invalid strategy state: {self.strategy}")

        chunk.spatial_x = x
        chunk.spatial_y = y
        return x, y

    def assign_batch(self, chunks: List[EpisodicChunk]) -> List[Tuple[int, int]]:
        """
        Assign coordinates to a list of episodic chunks.

        Args:
            chunks: List of EpisodicChunk instances.

        Returns:
            List of (x, y) tuples corresponding to each chunk.
        """
        coords = []
        for chunk in chunks:
          coords.append(self.assign(chunk))
        return coords

    def reset(self):
        """Reset the sequential index to 0."""
        self._current_index = 0


def calculate_interference_potential(
    coords: List[Tuple[int, int]],
    grid_size: int
) -> float:
    """
    Calculates a simple interference metric based on coordinate density.

    This is a helper utility for FR-003 (structural stability). It computes
    the average Euclidean distance between adjacent items in the assignment
    sequence. A lower average distance implies higher spatial clustering
    (potential for interference), while a higher distance implies scattering.

    Args:
        coords: List of (x, y) tuples assigned to a sequence of items.
        grid_size: The size of the grid.

    Returns:
        A float representing the average distance between consecutive items.
        Returns 0.0 if fewer than 2 items are provided.
    """
    if len(coords) < 2:
        return 0.0

    total_dist = 0.0
    count = 0

    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i+1]
        dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        total_dist += dist
        count += 1

    return total_dist / count
