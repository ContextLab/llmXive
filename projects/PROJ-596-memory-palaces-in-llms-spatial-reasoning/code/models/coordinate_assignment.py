"""
Coordinate assignment logic for episodic chunks (FR-001).

This module implements the logic to assign 2D spatial coordinates to episodic
chunks within the Memory Palace grid. The assignment is deterministic based on
the chunk's content hash to ensure reproducibility, while distributing chunks
to minimize immediate collision in the local neighborhood (simulating a hash
map with open addressing or a deterministic scatter).
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import math
import hashlib
import numpy as np
from models.memory_slot import MemoryGrid
from models.episodic_chunk import EpisodicChunk


@dataclass
class CoordinateAssignmentResult:
    """Result of assigning coordinates to a set of episodic chunks."""
    chunk_id: str
    assigned_coordinate: Tuple[int, int]
    hash_input: str
    interference_potential: float
    is_collision: bool = False
    collision_resolution_steps: int = 0


class CoordinateAssigner:
    """
    Assigns 2D coordinates to episodic chunks based on their content hash.

    The strategy uses the SHA-256 hash of the chunk's text content to derive
    an initial (x, y) coordinate. If that slot is occupied (collision), a
    deterministic probing sequence is used to find the next available slot.
    This implements a form of open addressing in the spatial memory grid.
    """

    def __init__(self, grid: MemoryGrid):
        """
        Initialize the assigner with a reference to the memory grid.

        Args:
            grid: The MemoryGrid instance representing the 2D spatial slots.
        """
        self.grid = grid
        self.grid_size = grid.size
        self.max_probes = grid.size * grid.size  # Safety limit

    def _compute_hash_coordinates(self, text_content: str) -> Tuple[int, int]:
        """
        Derive a 2D coordinate from the SHA-256 hash of the text content.

        The first 8 hex characters (32 bits) are used:
        - First 16 bits -> x coordinate
        - Next 16 bits -> y coordinate

        Args:
            text_content: The text content of the episodic chunk.

        Returns:
            A tuple (x, y) representing the initial coordinate.
        """
        hash_obj = hashlib.sha256(text_content.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()

        # Extract bits for coordinates
        x_bits = int(hash_hex[0:4], 16)
        y_bits = int(hash_hex[4:8], 16)

        # Map to grid dimensions
        x = x_bits % self.grid_size
        y = y_bits % self.grid_size

        return x, y

    def _calculate_interference_potential(self, x: int, y: int) -> float:
        """
        Calculate the interference potential for a given coordinate.

        This metric estimates the likelihood of retrieval interference based on
        the density of existing chunks in the local neighborhood (3x3 window).
        Higher density implies higher potential for interference.

        Args:
            x: X coordinate.
            y: Y coordinate.

        Returns:
            A float representing the interference potential (0.0 to 1.0).
        """
        neighborhood_count = 0
        total_slots = 0

        # Define a 3x3 neighborhood
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                # Wrap around for toroidal grid (optional, but good for boundaries)
                nx = nx % self.grid_size
                ny = ny % self.grid_size

                if self.grid.is_occupied(nx, ny):
                    neighborhood_count += 1
                total_slots += 1

        return neighborhood_count / total_slots

    def assign_coordinate(self, chunk: EpisodicChunk) -> CoordinateAssignmentResult:
        """
        Assign a coordinate to a single episodic chunk.

        Args:
            chunk: The EpisodicChunk to assign.

        Returns:
            CoordinateAssignmentResult containing the assigned coordinate and metadata.
        """
        text_content = chunk.text_content
        initial_coords = self._compute_hash_coordinates(text_content)
        x, y = initial_coords

        probes = 0
        is_collision = False
        final_x, final_y = x, y

        # Open addressing with linear probing
        while self.grid.is_occupied(x, y):
            is_collision = True
            probes += 1
            if probes >= self.max_probes:
                raise RuntimeError(f"Failed to assign coordinate for chunk {chunk.id}: grid full or infinite loop.")

            # Linear probe: move to next slot in a pseudo-random but deterministic order
            # Using the next 4 hex digits of the hash for the offset direction
            hash_obj = hashlib.sha256(text_content.encode('utf-8'))
            hash_hex = hash_obj.hexdigest()
            offset_val = int(hash_hex[8:12], 16)

            # Move diagonally or orthogonally based on offset
            x = (x + (offset_val % self.grid_size)) % self.grid_size
            y = (y + ((offset_val // self.grid_size) % self.grid_size)) % self.grid_size

        # Mark the slot as occupied in the grid
        self.grid.assign_slot(x, y, chunk.id)

        interference = self._calculate_interference_potential(x, y)

        return CoordinateAssignmentResult(
            chunk_id=chunk.id,
            assigned_coordinate=(x, y),
            hash_input=text_content[:50] + "...", # Truncate for logging
            interference_potential=interference,
            is_collision=is_collision,
            collision_resolution_steps=probes
        )

    def assign_coordinates_batch(self, chunks: List[EpisodicChunk]) -> List[CoordinateAssignmentResult]:
        """
        Assign coordinates to a list of episodic chunks.

        Args:
            chunks: List of EpisodicChunk instances.

        Returns:
            List of CoordinateAssignmentResult instances.
        """
        results = []
        for chunk in chunks:
            result = self.assign_coordinate(chunk)
            results.append(result)
        return results


def calculate_interference_potential(grid: MemoryGrid, x: int, y: int) -> float:
    """
    Standalone helper to calculate interference potential for a coordinate.

    Args:
        grid: The MemoryGrid instance.
        x: X coordinate.
        y: Y coordinate.

    Returns:
        Float interference potential.
    """
    assigner = CoordinateAssigner(grid)
    return assigner._calculate_interference_potential(x, y)


def main():
    """
    Main entry point for testing coordinate assignment logic.
    """
    # Initialize a small grid for testing
    test_grid = MemoryGrid(size=10)

    # Create some dummy chunks
    chunks = [
        EpisodicChunk(id="chunk_1", text_content="The cat sat on the mat."),
        EpisodicChunk(id="chunk_2", text_content="The quick brown fox jumps."),
        EpisodicChunk(id="chunk_3", text_content="Memory palaces require spatial reasoning."),
        EpisodicChunk(id="chunk_4", text_content="Repetition enhances synaptic strength."),
    ]

    assigner = CoordinateAssigner(test_grid)
    results = assigner.assign_coordinates_batch(chunks)

    print("Coordinate Assignment Results:")
    print("-" * 60)
    for res in results:
        print(f"Chunk ID: {res.chunk_id}")
        print(f"  Assigned Coordinate: {res.assigned_coordinate}")
        print(f"  Collision: {res.is_collision} (Steps: {res.collision_resolution_steps})")
        print(f"  Interference Potential: {res.interference_potential:.2f}")
        print("-" * 60)


if __name__ == "__main__":
    main()