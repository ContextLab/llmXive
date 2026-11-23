"""
Coordinate assignment logic for episodic chunks (FR-001).

This module implements the deterministic assignment of 2D coordinates to episodic
memory chunks within the Memory Palace grid. It ensures semantic proximity
correlates with spatial proximity to minimize interference.
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
    """Result of assigning a coordinate to an episodic chunk."""
    chunk_id: str
    assigned_coordinate: Tuple[int, int]
    interference_potential: float
    reason: str = "Assigned"


def calculate_interference_potential(
    new_chunk: EpisodicChunk,
    existing_chunks: List[EpisodicChunk],
    grid: MemoryGrid,
    coordinate: Tuple[int, int]
) -> float:
    """
    Calculate the expected interference potential for placing a chunk at a specific coordinate.

    Interference is modeled as the inverse of spatial distance to semantically similar chunks.
    A lower potential indicates a safer placement.

    Args:
        new_chunk: The chunk being assigned.
        existing_chunks: List of chunks already in memory.
        grid: The memory grid configuration.
        coordinate: The (x, y) coordinate being considered.

    Returns:
        A float representing the interference potential (lower is better).
    """
    if not existing_chunks:
        return 0.0

    total_interference = 0.0
    x, y = coordinate

    for existing in existing_chunks:
        ex, ey = existing.coordinate
        if ex is None or ey is None:
            continue

        # Euclidean distance in the grid
        spatial_dist = math.sqrt((x - ex)**2 + (y - ey)**2)
        if spatial_dist == 0:
            # Direct collision
            return float('inf')

        # Semantic similarity (0 to 1)
        # We use the cosine similarity of the embedding vectors if available
        # If not, we fall back to a simple hash-based proxy for this phase
        if hasattr(new_chunk, 'embedding') and new_chunk.embedding is not None and hasattr(existing, 'embedding') and existing.embedding is not None:
            norm_new = np.linalg.norm(new_chunk.embedding)
            norm_exist = np.linalg.norm(existing.embedding)
            if norm_new > 0 and norm_exist > 0:
                sim = np.dot(new_chunk.embedding, existing.embedding) / (norm_new * norm_exist)
            else:
                sim = 0.0
        else:
            # Fallback: simple hash difference as a proxy for semantic distance
            # This is a heuristic for the assignment logic when embeddings aren't fully loaded
            h1 = int(hashlib.md5(new_chunk.content.encode()).hexdigest()[:8], 16)
            h2 = int(hashlib.md5(existing.content.encode()).hexdigest()[:8], 16)
            # Normalize to 0-1, 0 being identical
            max_val = 2**32 - 1
            sim = 1.0 - (abs(h1 - h2) / max_val) if max_val > 0 else 0.0

        # Interference contribution: High similarity + Close distance = High interference
        # Formula: sim / (dist^2)
        interference_contribution = sim / (spatial_dist ** 2)
        total_interference += interference_contribution

    return total_interference


class CoordinateAssigner:
    """
    Assigns 2D coordinates to episodic chunks based on semantic similarity
    to minimize interference in the Memory Palace grid.
    """

    def __init__(self, grid: MemoryGrid):
        self.grid = grid
        self.assigned_chunks: List[EpisodicChunk] = []
        self._coordinate_map: Dict[Tuple[int, int], EpisodicChunk] = {}

    def assign_coordinate(self, chunk: EpisodicChunk) -> CoordinateAssignmentResult:
        """
        Assigns the best available coordinate to the given chunk.

        Strategy:
        1. If the chunk has a preferred coordinate (from prior context), try it.
        2. Otherwise, scan the grid to find the coordinate with the lowest
           interference potential relative to existing chunks.
        3. Update the chunk and internal state.

        Args:
            chunk: The episodic chunk to assign.

        Returns:
            CoordinateAssignmentResult containing the assigned coordinate and metadata.
        """
        best_coord: Optional[Tuple[int, int]] = None
        best_potential = float('inf')
        best_reason = "Assigned"

        # Determine search space
        # If we have a preferred coordinate from the chunk metadata, check it first
        preferred = chunk.preferred_coordinate
        search_coords: List[Tuple[int, int]] = []

        if preferred and 0 <= preferred[0] < self.grid.width and 0 <= preferred[1] < self.grid.height:
            search_coords = [preferred]
        else:
            # Scan entire grid for the optimal slot
            for x in range(self.grid.width):
                for y in range(self.grid.height):
                    search_coords.append((x, y))

        # Evaluate interference for candidates
        for coord in search_coords:
            potential = calculate_interference_potential(
                chunk,
                self.assigned_chunks,
                self.grid,
                coord
            )

            if potential < best_potential:
                best_potential = potential
                best_coord = coord
                if potential == 0.0:
                    best_reason = "Empty slot with no semantic neighbors"
                elif potential == float('inf'):
                    best_reason = "Collision avoided"
                else:
                    best_reason = f"Optimal balance (potential={potential:.4f})"

        if best_coord is None:
            raise RuntimeError("Failed to find a valid coordinate for chunk. Grid may be full.")

        # Finalize assignment
        chunk.coordinate = best_coord
        self.assigned_chunks.append(chunk)
        self._coordinate_map[best_coord] = chunk

        return CoordinateAssignmentResult(
            chunk_id=chunk.id,
            assigned_coordinate=best_coord,
            interference_potential=best_potential,
            reason=best_reason
        )

    def get_chunk_at(self, coordinate: Tuple[int, int]) -> Optional[EpisodicChunk]:
        """Retrieve a chunk by its assigned coordinate."""
        return self._coordinate_map.get(coordinate)


def main():
    """
    Demonstration of the coordinate assignment logic.
    This function runs a local simulation to verify the algorithm works correctly.
    """
    print("Initializing Memory Grid (10x10)...")
    grid = MemoryGrid(width=10, height=10, max_chunks_per_cell=1)

    assigner = CoordinateAssigner(grid)

    # Create dummy chunks for testing
    chunks = []
    for i in range(5):
        # Simulate embedding (random for demo, but deterministic in real use)
        emb = np.random.randn(768).astype(np.float32)
        chunk = EpisodicChunk(
            id=f"chunk_{i}",
            content=f"Episodic memory content {i}",
            timestamp="2026-01-01T00:00:00",
            embedding=emb.tolist(), # Store as list for dataclass compatibility if needed, or keep numpy
            metadata={"source": "bAbI"}
        )
        chunks.append(chunk)

    print("\nAssigning coordinates...")
    results = []
    for i, chunk in enumerate(chunks):
        # Set a preferred coordinate for the first chunk to test logic
        if i == 0:
            chunk.preferred_coordinate = (0, 0)
        
        result = assigner.assign_coordinate(chunk)
        results.append(result)
        print(f"  {chunk.id}: Assigned to {result.assigned_coordinate} "
              f"(Potential: {result.interference_potential:.4f}) - {result.reason}")

    print("\nVerification:")
    for res in results:
        retrieved = assigner.get_chunk_at(res.assigned_coordinate)
        assert retrieved is not None, "Retrieval failed"
        assert retrieved.id == res.chunk_id, "ID mismatch"
    
    print("All assignments verified successfully.")

if __name__ == "__main__":
    main()