"""
Coordinate assignment logic for episodic chunks (FR-001).

Implements the deterministic assignment of 2D coordinates to episodic chunks
based on their content hash, ensuring consistent spatial placement within the
Memory Palace grid.
"""
from typing import List, Optional, Tuple, Dict, Any
import hashlib
import numpy as np

from models.episodic_chunk import EpisodicChunk
from models.memory_slot import MemoryGrid


class CoordinateAssigner:
    """
    Assigns 2D coordinates (x, y) to EpisodicChunks based on a deterministic
    hashing of their content.

    This implements FR-001: Coordinate assignment logic for episodic chunks.
    The logic ensures that identical content always maps to the same coordinate,
    while distinct content is distributed across the grid to minimize interference.
    """

    def __init__(self, grid_size: int = 16, seed: Optional[int] = None):
        """
        Initialize the CoordinateAssigner.

        Args:
            grid_size: The dimension of the square grid (grid_size x grid_size).
                       Valid coordinates are in range [0, grid_size - 1].
            seed: Optional seed for any stochastic components (currently unused
                  as the primary assignment is deterministic via hashing).
        """
        self.grid_size = grid_size
        self.seed = seed
        self._rng = np.random.default_rng(seed)

    def _hash_to_integer(self, content: str) -> int:
        """
        Converts a string content to a large integer using SHA-256.

        Args:
            content: The text content of the episodic chunk.

        Returns:
            A large integer derived from the hash.
        """
        if not content:
            # Fallback for empty content to ensure determinism
            content = "\x00"
        
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        # Convert first 16 hex chars to integer to avoid huge numbers
        return int(hash_hex[:16], 16)

    def assign_coordinate(self, chunk: EpisodicChunk) -> Tuple[int, int]:
        """
        Assigns a 2D coordinate (x, y) to the given episodic chunk.

        The coordinate is derived deterministically from the chunk's content
        to ensure reproducibility. The mapping distributes chunks across the
        grid to simulate spatial separation.

        Args:
            chunk: The EpisodicChunk to assign a coordinate to.

        Returns:
            A tuple (x, y) representing the assigned coordinates.
        """
        # Use content for deterministic assignment
        raw_value = self._hash_to_integer(chunk.content)
        
        # Map to x coordinate
        x = raw_value % self.grid_size
        
        # Map to y coordinate using a secondary transformation to ensure
        # better distribution (e.g., mixing bits or using a different modulus)
        # We use (raw_value // grid_size) % grid_size to utilize more of the hash
        y = (raw_value // self.grid_size) % self.grid_size

        return (x, y)

    def assign_coordinates_batch(self, chunks: List[EpisodicChunk]) -> List[Tuple[int, int]]:
        """
        Assigns coordinates to a list of episodic chunks.

        Args:
            chunks: List of EpisodicChunk objects.

        Returns:
            List of (x, y) tuples corresponding to the input chunks.
        """
        return [self.assign_coordinate(chunk) for chunk in chunks]

    def get_slot_key(self, x: int, y: int) -> str:
        """
        Generates a unique string key for a grid slot.

        Args:
            x: X coordinate.
            y: Y coordinate.

        Returns:
            String key in format "x_y".
        """
        return f"{x}_{y}"

    def calculate_interference_potential(
        self, 
        chunks: List[EpisodicChunk], 
        grid: Optional[MemoryGrid] = None
    ) -> Dict[str, float]:
        """
        Calculates the potential interference for a set of chunks based on
        their assigned coordinates.

        Interference is estimated by the density of chunks in shared or
        adjacent slots.

        Args:
            chunks: List of EpisodicChunk objects.
            grid: Optional MemoryGrid to check current occupancy. If provided,
                  interference is calculated relative to existing slots.

        Returns:
            Dictionary with metrics:
            - 'collision_count': Number of chunks mapping to already occupied slots.
            - 'max_occupancy': Highest number of chunks in any single slot.
            - 'average_distance': Average Euclidean distance between chunks.
        """
        if not chunks:
            return {
                "collision_count": 0.0,
                "max_occupancy": 0.0,
                "average_distance": 0.0
            }

        coordinates = self.assign_coordinates_batch(chunks)
        
        # Count occupancy per slot
        slot_counts: Dict[str, int] = {}
        collision_count = 0
        
        # If a grid is provided, check against its current state
        occupied_keys = set()
        if grid is not None:
            occupied_keys = set(grid.slots.keys())

        for (x, y) in coordinates:
            key = self.get_slot_key(x, y)
            slot_counts[key] = slot_counts.get(key, 0) + 1
            
            # Count collision if this slot was already occupied by a different entity
            # (In a pure assignment context without a persistent grid, this is 0)
            if key in occupied_keys:
                collision_count += 1

        max_occupancy = max(slot_counts.values()) if slot_counts else 0

        # Calculate average pairwise distance (approximate for performance)
        # Using a sample if too many chunks to avoid O(N^2) on large sets
        sample_size = min(len(coordinates), 100)
        if len(coordinates) > 1:
            # Simple heuristic: variance of coordinates
            xs = [c[0] for c in coordinates]
            ys = [c[1] for c in coordinates]
            avg_distance = np.sqrt(np.var(xs) + np.var(ys))
        else:
            avg_distance = 0.0

        return {
            "collision_count": float(collision_count),
            "max_occupancy": float(max_occupancy),
            "average_distance": float(avg_distance)
        }


def calculate_interference_potential(
    chunks: List[EpisodicChunk], 
    grid_size: int = 16,
    grid: Optional[MemoryGrid] = None
) -> Dict[str, float]:
    """
    Convenience function to calculate interference potential without instantiating
    the assigner directly.

    Args:
        chunks: List of EpisodicChunk objects.
        grid_size: Size of the grid to assume.
        grid: Optional existing MemoryGrid.

    Returns:
        Dictionary of interference metrics.
    """
    assigner = CoordinateAssigner(grid_size=grid_size)
    return assigner.calculate_interference_potential(chunks, grid)

def main():
    """
    Simple CLI entry point to demonstrate coordinate assignment.
    """
    import sys
    from models.episodic_chunk import EpisodicMemoryCollection

    # Create a mock collection for demonstration
    collection = EpisodicMemoryCollection()
    test_chunks = [
        EpisodicChunk(content="The cat sat on the mat.", source="story_1"),
        EpisodicChunk(content="The dog ran in the park.", source="story_1"),
        EpisodicChunk(content="The sun was bright.", source="story_2"),
        EpisodicChunk(content="The moon was full.", source="story_2"),
    ]
    
    for chunk in test_chunks:
        collection.add_chunk(chunk)

    assigner = CoordinateAssigner(grid_size=8)
    
    print("Coordinate Assignment Results:")
    print("-" * 30)
    for chunk in collection.chunks:
        x, y = assigner.assign_coordinate(chunk)
        print(f"Content: {chunk.content[:30]}... -> ({x}, {y})")

    metrics = assigner.calculate_interference_potential(collection.chunks)
    print("\nInterference Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
