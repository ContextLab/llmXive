"""
EpisodicChunk schema for the Memory Palace architecture.

Defines the structure of an episodic memory trace that is to be
spatially organized and deposited into the memory grid.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import torch
import uuid


@dataclass
class EpisodicChunk:
    """
    Represents a single chunk of episodic memory.

    This data structure holds the content (embedding), the source context,
    and the assigned spatial coordinates (if any) within the memory palace.
    """
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content_embedding: Optional[torch.Tensor] = None
    raw_text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Spatial coordinates assigned by the coordinate assignment logic (T007b)
    spatial_coordinate: Optional[tuple[int, int]] = None
    
    # Temporal metadata for consolidation ordering
    created_at: float = field(default_factory=lambda: 0.0) # timestamp
    consolidation_strength: float = 0.0 # 0.0 to 1.0, representing memory strength

    def assign_coordinate(self, row: int, col: int) -> None:
        """Assign a spatial coordinate to this chunk."""
        self.spatial_coordinate = (row, col)

    def is_spatially_organized(self) -> bool:
        """Check if this chunk has been assigned a spatial location."""
        return self.spatial_coordinate is not None

    def validate(self) -> bool:
        """Ensure the chunk has necessary data."""
        if self.content_embedding is None and self.raw_text is None:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the chunk to a dictionary for logging/storage."""
        return {
            "chunk_id": self.chunk_id,
            "spatial_coordinate": self.spatial_coordinate,
            "metadata": self.metadata,
            "consolidation_strength": self.consolidation_strength,
            "created_at": self.created_at,
            "has_embedding": self.content_embedding is not None,
            "has_text": self.raw_text is not None
        }


@dataclass
class EpisodicTraceBatch:
    """
    A batch of episodic chunks ready for spatial assignment and storage.
    """
    chunks: List[EpisodicChunk] = field(default_factory=list)
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def add_chunk(self, chunk: EpisodicChunk) -> None:
        self.chunks.append(chunk)

    def get_unassigned_chunks(self) -> List[EpisodicChunk]:
        """Return chunks that do not yet have a spatial coordinate."""
        return [c for c in self.chunks if not c.is_spatially_organized()]

    def count_spatially_organized(self) -> int:
        """Count how many chunks have been assigned coordinates."""
        return sum(1 for c in self.chunks if c.is_spatially_organized())