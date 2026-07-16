"""
Coordinate assignment logic for episodic chunks (FR-001).

This module implements the deterministic and interference-aware assignment of
(x, y) coordinates within the MemoryGrid for EpisodicChunk instances.

The logic ensures:
1. Deterministic assignment based on chunk content hash (reproducibility).
2. Interference avoidance by calculating a potential score for candidate slots.
3. Fallback to the slot with minimum interference potential if the preferred
   slot is occupied or high-interference.
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
    """Result of a coordinate assignment operation."""
    chunk_id: str
    assigned_x: int
    assigned_y: int
    interference_score: float
    is_occupied: bool
    assignment_method: str  # 'deterministic', 'interference_aware', 'fallback'


def calculate_interference_potential(
    grid: MemoryGrid,
    target_x: int,
    target_y: int,
    current_chunk_embedding: Optional[np.ndarray] = None
) -> float:
    """
    Calculate the interference potential for a specific coordinate.

    Interference is defined as the density of existing slots within a radius
    of the target coordinate, weighted by their semantic similarity if an
    embedding is provided.

    Args:
        grid: The current memory grid state.
        target_x: Target x coordinate.
        target_y: Target y coordinate.
        current_chunk_embedding: Optional embedding vector of the new chunk.

    Returns:
        A float representing the interference score (higher = more interference).
    """
    if grid.grid_size <= 0:
        return 0.0

    radius = math.ceil(grid.grid_size / 4.0)
    interference_score = 0.0
    neighbor_count = 0

    for slot in grid.slots:
        if slot.occupied:
            # Calculate Euclidean distance
            dist = math.sqrt((slot.x - target_x) ** 2 + (slot.y - target_y) ** 2)

            if dist <= radius and dist > 0:
                neighbor_count += 1
                weight = 1.0 / (1.0 + dist)  # Decay with distance

                if current_chunk_embedding is not None and slot.embedding is not None:
                    # Cosine similarity component (0 to 1, higher is more similar)
                    sim = np.dot(current_chunk_embedding, slot.embedding) / (
                        np.linalg.norm(current_chunk_embedding) * np.linalg.norm(slot.embedding) + 1e-8
                    )
                    # Normalize similarity to [0, 1] range
                    sim_normalized = (sim + 1) / 2
                    weight *= (0.5 + 0.5 * sim_normalized)

                interference_score += weight

    # Normalize by max possible neighbors to keep scale consistent
    max_neighbors = (2 * radius + 1) ** 2
    return interference_score / max_neighbors if max_neighbors > 0 else 0.0


class CoordinateAssigner:
    """
    Assigns 2D coordinates to episodic chunks based on FR-001 requirements.

    Strategy:
    1. Generate a deterministic candidate coordinate based on chunk ID/content hash.
    2. If the slot is free, assign it.
    3. If occupied or high interference, search neighbors in a spiral pattern
       for the slot with minimum interference potential.
    """

    def __init__(self, grid: MemoryGrid):
        self.grid = grid
        self.grid_size = grid.grid_size

    def _get_hash_coords(self, chunk: EpisodicChunk) -> Tuple[int, int]:
        """
        Generate deterministic coordinates from chunk content.
        Uses SHA-256 hash of the chunk's text content.
        """
        content_str = chunk.content or ""
        # Include metadata in hash to ensure uniqueness even for same text
        hash_input = f"{chunk.id}:{content_str}:{chunk.timestamp}".encode('utf-8')
        digest = hashlib.sha256(hash_input).hexdigest()

        # Take first 8 hex chars for x, next 8 for y
        x_val = int(digest[0:8], 16)
        y_val = int(digest[8:16], 16)

        x = x_val % self.grid_size
        y = y_val % self.grid_size
        return x, y

    def _spiral_search(self, start_x: int, start_y: int) -> List[Tuple[int, int]]:
        """
        Generate coordinates in a spiral pattern starting from (start_x, start_y).
        Returns a list of (x, y) tuples ordered by distance from start.
        """
        candidates = []
        # Spiral directions: right, up, left, down
        dx = [1, 0, -1, 0]
        dy = [0, 1, 0, -1]

        x, y = start_x, start_y
        step_size = 1
        steps_taken = 0
        direction_idx = 0

        # Limit search to full grid coverage
        max_iterations = self.grid_size * self.grid_size

        while len(candidates) < max_iterations:
            candidates.append((x, y))

            x += dx[direction_idx]
            y += dy[direction_idx]
            steps_taken += 1

            if steps_taken == step_size:
                steps_taken = 0
                direction_idx = (direction_idx + 1) % 4
                if direction_idx % 2 == 0:
                    step_size += 1

            # Wrap around grid (toroidal) for search continuity
            x = x % self.grid_size
            y = y % self.grid_size

            # Break if we've looped back to start without finding space (full grid)
            if len(candidates) >= max_iterations:
                break

        return candidates

    def assign_coordinate(
        self,
        chunk: EpisodicChunk,
        interference_threshold: float = 0.5
    ) -> CoordinateAssignmentResult:
        """
        Assign a coordinate to the given episodic chunk.

        Args:
            chunk: The episodic chunk to assign.
            interference_threshold: Max acceptable interference score.

        Returns:
            CoordinateAssignmentResult with the assigned coordinates and metadata.
        """
        # 1. Get deterministic candidate
        preferred_x, preferred_y = self._get_hash_coords(chunk)

        # Check if preferred slot is free
        preferred_slot = self.grid.get_slot(preferred_x, preferred_y)
        
        if not preferred_slot.occupied:
            self.grid.set_occupied(preferred_x, preferred_y, chunk)
            return CoordinateAssignmentResult(
                chunk_id=chunk.id,
                assigned_x=preferred_x,
                assigned_y=preferred_y,
                interference_score=0.0,
                is_occupied=False,
                assignment_method='deterministic'
            )

        # 2. If occupied, calculate interference and search
        embedding = chunk.embedding if hasattr(chunk, 'embedding') and chunk.embedding is not None else None
        base_interference = calculate_interference_potential(
            self.grid, preferred_x, preferred_y, embedding
        )

        if base_interference <= interference_threshold:
            # Even if occupied, if interference is low, we might still want to
            # place it here (e.g., if we are overwriting or merging). 
            # For this implementation, we treat "occupied" as a hard block for new unique chunks
            # and proceed to search.
            pass

        # 3. Spiral search for best slot
        search_order = self._spiral_search(preferred_x, preferred_y)
        
        best_slot = None
        best_score = float('inf')
        best_coords = None

        for cx, cy in search_order:
            slot = self.grid.get_slot(cx, cy)
            if not slot.occupied:
                score = calculate_interference_potential(self.grid, cx, cy, embedding)
                if score < best_score:
                    best_score = score
                    best_slot = slot
                    best_coords = (cx, cy)
                
                # Early exit if we find a very low interference slot
                if score < 0.1:
                    break

        if best_coords:
            self.grid.set_occupied(best_coords[0], best_coords[1], chunk)
            return CoordinateAssignmentResult(
                chunk_id=chunk.id,
                assigned_x=best_coords[0],
                assigned_y=best_coords[1],
                interference_score=best_score,
                is_occupied=False,
                assignment_method='interference_aware' if best_score < base_interference else 'fallback'
            )
        
        # Fallback: Grid full, return the slot with minimum interference even if occupied
        # (In a real scenario, this might trigger eviction or resizing)
        min_interference_slot = None
        min_interference_score = float('inf')
        min_interference_coords = None

        for slot in self.grid.slots:
            score = calculate_interference_potential(self.grid, slot.x, slot.y, embedding)
            if score < min_interference_score:
                min_interference_score = score
                min_interference_slot = slot
                min_interference_coords = (slot.x, slot.y)

        if min_interference_coords:
            # Force assignment (overwriting)
            self.grid.set_occupied(min_interference_coords[0], min_interference_coords[1], chunk)
            return CoordinateAssignmentResult(
                chunk_id=chunk.id,
                assigned_x=min_interference_coords[0],
                assigned_y=min_interference_coords[1],
                interference_score=min_interference_score,
                is_occupied=True,
                assignment_method='fallback'
            )

        # Should not reach here if grid_size > 0
        raise RuntimeError("Failed to assign coordinate to any slot in the grid.")


def main():
    """
    Entry point for testing coordinate assignment logic.
    Demonstrates assignment of multiple chunks to a grid.
    """
    print("Running Coordinate Assignment Logic Test...")
    
    # Initialize a 10x10 grid
    grid = MemoryGrid(grid_size=10)
    assigner = CoordinateAssigner(grid)

    # Create dummy chunks
    chunks = [
        EpisodicChunk(id=f"chunk_{i}", content=f"Memory content {i}", timestamp=f"2026-01-01T00:00:{i:02d}")
        for i in range(15)
    ]

    results = []
    for chunk in chunks:
        result = assigner.assign_coordinate(chunk, interference_threshold=0.3)
        results.append(result)
        print(f"Assigned {chunk.id} -> ({result.assigned_x}, {result.assigned_y}) "
              f"(Interference: {result.interference_score:.4f}, Method: {result.assignment_method})")

    # Verify grid state
    print(f"\nGrid Occupancy: {grid.get_occupancy_rate():.2%}")
    
    return results


if __name__ == "__main__":
    main()