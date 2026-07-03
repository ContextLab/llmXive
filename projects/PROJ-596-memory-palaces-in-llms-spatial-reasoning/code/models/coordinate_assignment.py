"""
Coordinate assignment logic for episodic chunks.

Implements FR-001: Assigns 2D spatial coordinates to episodic chunks within
a logical memory grid to enable spatial indexing and retrieval.
"""
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import math
import hashlib
import numpy as np

from models.memory_slot import MemoryGrid
from models.episodic_chunk import EpisodicChunk, EpisodicMemoryCollection


@dataclass
class CoordinateAssignmentResult:
    """Result of assigning coordinates to a collection of chunks."""
    assigned_chunks: List[EpisodicChunk]
    grid_state: MemoryGrid
    assignment_log: List[Dict[str, Any]]


class CoordinateAssigner:
    """
    Assigns 2D coordinates to episodic chunks based on a deterministic
    hashing strategy and grid occupancy checks.

    This implements the 'Memory Palace' spatial indexing strategy where
    semantic content is mapped to specific (x, y) locations.
    """

    def __init__(self, grid_size: int = 10, seed: int = 42):
        """
        Initialize the coordinate assigner.

        Args:
            grid_size: The dimension of the square grid (grid_size x grid_size).
            seed: Random seed for any stochastic tie-breaking (currently deterministic).
        """
        self.grid_size = grid_size
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def _hash_content_to_seed(self, content: str) -> int:
        """
        Generate a deterministic integer seed from chunk content.

        Args:
            content: The text content of the episodic chunk.

        Returns:
            A 32-bit integer derived from the SHA-256 hash of the content.
        """
        if not content:
            return 0
        digest = hashlib.sha256(content.encode('utf-8')).digest()
        # Take first 4 bytes and convert to int
        return int.from_bytes(digest[:4], byteorder='big', signed=False)

    def _deterministic_coords(self, seed_val: int) -> Tuple[int, int]:
        """
        Generate a deterministic (x, y) coordinate pair from a seed integer.

        Uses a simple linear congruential generator approach for distribution
        across the grid.

        Args:
            seed_val: An integer seed derived from content.

        Returns:
            Tuple of (x, y) coordinates within [0, grid_size-1].
        """
        # Simple LCG to spread values across the grid
        a = 1103515245
        c = 12345
        m = 2**31

        x = (a * seed_val + c) % m % self.grid_size
        y = (a * (x + seed_val) + c) % m % self.grid_size

        return int(x), int(y)

    def assign_coordinates(
        self,
        chunks: List[EpisodicChunk],
        grid: Optional[MemoryGrid] = None
    ) -> CoordinateAssignmentResult:
        """
        Assign 2D coordinates to a list of episodic chunks.

        This method implements FR-001 by:
        1. Hashing content to a seed.
        2. Mapping seed to (x, y) coordinates.
        3. Resolving collisions by probing adjacent cells.
        4. Updating the MemoryGrid state.

        Args:
            chunks: List of EpisodicChunk objects to assign.
            grid: Optional existing MemoryGrid to update. If None, creates a new one.

        Returns:
            CoordinateAssignmentResult containing assigned chunks and final grid state.
        """
        if grid is None:
            grid = MemoryGrid(size=self.grid_size)

        assignment_log = []
        assigned_chunks = []

        for idx, chunk in enumerate(chunks):
            original_content = chunk.content
            seed_val = self._hash_content_to_seed(original_content)
            base_x, base_y = self._deterministic_coords(seed_val)

            # Collision resolution: probe neighbors in a spiral pattern
            assigned = False
            probe_x, probe_y = base_x, base_y
            probe_radius = 0

            while not assigned and probe_radius < self.grid_size:
                # Check current probe position
                if (0 <= probe_x < self.grid_size and
                    0 <= probe_y < self.grid_size):
                    slot = grid.get_slot(probe_x, probe_y)
                    if slot.is_empty:
                        # Assign this coordinate
                        chunk.spatial_x = probe_x
                        chunk.spatial_y = probe_y
                        slot.assign(chunk)
                        assigned = True
                    else:
                        # Slot occupied, continue probing
                        pass
                else:
                    # Out of bounds, expand radius
                    pass

                if not assigned:
                    # Spiral probe logic
                    # Right
                    for _ in range(2 * probe_radius + 1):
                        probe_x += 1
                        if (0 <= probe_x < self.grid_size and
                            0 <= probe_y < self.grid_size):
                            slot = grid.get_slot(probe_x, probe_y)
                            if slot.is_empty:
                                chunk.spatial_x = probe_x
                                chunk.spatial_y = probe_y
                                slot.assign(chunk)
                                assigned = True
                                break
                        if assigned: break
                    if assigned: break

                    # Down
                    for _ in range(2 * probe_radius + 1):
                        probe_y += 1
                        if (0 <= probe_x < self.grid_size and
                            0 <= probe_y < self.grid_size):
                            slot = grid.get_slot(probe_x, probe_y)
                            if slot.is_empty:
                                chunk.spatial_x = probe_x
                                chunk.spatial_y = probe_y
                                slot.assign(chunk)
                                assigned = True
                                break
                        if assigned: break
                    if assigned: break

                    # Left
                    for _ in range(2 * probe_radius + 2):
                        probe_x -= 1
                        if (0 <= probe_x < self.grid_size and
                            0 <= probe_y < self.grid_size):
                            slot = grid.get_slot(probe_x, probe_y)
                            if slot.is_empty:
                                chunk.spatial_x = probe_x
                                chunk.spatial_y = probe_y
                                slot.assign(chunk)
                                assigned = True
                                break
                        if assigned: break
                    if assigned: break

                    # Up
                    for _ in range(2 * probe_radius + 2):
                        probe_y -= 1
                        if (0 <= probe_x < self.grid_size and
                            0 <= probe_y < self.grid_size):
                            slot = grid.get_slot(probe_x, probe_y)
                            if slot.is_empty:
                                chunk.spatial_x = probe_x
                                chunk.spatial_y = probe_y
                                slot.assign(chunk)
                                assigned = True
                                break
                        if assigned: break
                    if assigned: break

                    probe_radius += 1
                    # Reset probe to base for next radius if needed, 
                    # but spiral logic above handles continuous movement.
                    # If we exhausted the grid, we break the inner loop.
                    if probe_radius >= self.grid_size:
                        break

            if not assigned:
                # Fallback: if grid is full, assign to a random empty slot if any,
                # or raise an error if completely full.
                empty_slots = grid.get_empty_slots()
                if empty_slots:
                    chosen = empty_slots[0]
                    chunk.spatial_x = chosen.x
                    chunk.spatial_y = chosen.y
                    chosen.assign(chunk)
                    assigned = True
                else:
                    # Grid is full. Log warning and skip or handle as needed.
                    # For now, we log and keep the base coordinate (even if collision)
                    # to indicate the pressure, but technically it's an error state.
                    assignment_log.append({
                        "chunk_id": chunk.id,
                        "status": "grid_full",
                        "attempted_x": base_x,
                        "attempted_y": base_y
                    })
                    # We still assign the base coordinates for tracking, 
                    # though the slot might be overwritten or invalid.
                    chunk.spatial_x = base_x
                    chunk.spatial_y = base_y

            log_entry = {
                "chunk_id": chunk.id,
                "content_hash": seed_val,
                "assigned_x": chunk.spatial_x,
                "assigned_y": chunk.spatial_y,
                "status": "assigned" if assigned else "failed"
            }
            assignment_log.append(log_entry)
            assigned_chunks.append(chunk)

        return CoordinateAssignmentResult(
            assigned_chunks=assigned_chunks,
            grid_state=grid,
            assignment_log=assignment_log
        )


def main():
    """
    Demonstration of coordinate assignment logic.
    Reads from a hypothetical data source or creates dummy data for testing.
    """
    print("Initializing Coordinate Assignment Logic (FR-001)...")
    
    # Create sample chunks
    sample_data = [
        EpisodicChunk(
            content="The cat sat on the mat.",
            timestamp="2023-01-01T10:00:00Z",
            source="babi_task3"
        ),
        EpisodicChunk(
            content="The dog barked at the mailman.",
            timestamp="2023-01-01T10:05:00Z",
            source="babi_task3"
        ),
        EpisodicChunk(
            content="The ball rolled under the sofa.",
            timestamp="2023-01-01T10:10:00Z",
            source="babi_task3"
        ),
        EpisodicChunk(
            content="John moved the cup to the kitchen.",
            timestamp="2023-01-01T10:15:00Z",
            source="babi_task3"
        ),
        EpisodicChunk(
            content="The cup was then moved to the garden.",
            timestamp="2023-01-01T10:20:00Z",
            source="babi_task3"
        )
    ]

    assigner = CoordinateAssigner(grid_size=5)
    grid = MemoryGrid(size=5)

    result = assigner.assign_coordinates(sample_data, grid)

    print(f"Assigned {len(result.assigned_chunks)} chunks to grid.")
    print("Assignment Log:")
    for entry in result.assignment_log:
        print(f"  Chunk {entry['chunk_id'][:8]}... -> ({entry['assigned_x']}, {entry['assigned_y']}) [{entry['status']}]")

    print("\nGrid State:")
    grid.print_grid()

    # Save the result to a data file as per project conventions
    import json
    import os
    from pathlib import Path

    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "coordinate_assignment_results.json"

    serializable_result = {
        "grid_size": assigner.grid_size,
        "total_chunks": len(result.assigned_chunks),
        "assignments": [
            {
                "chunk_id": c.id,
                "content_preview": c.content[:50],
                "x": c.spatial_x,
                "y": c.spatial_y
            }
            for c in result.assigned_chunks
        ],
        "grid_occupancy": grid.get_occupancy_stats()
    }

    with open(output_file, 'w') as f:
        json.dump(serializable_result, f, indent=2)

    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    main()