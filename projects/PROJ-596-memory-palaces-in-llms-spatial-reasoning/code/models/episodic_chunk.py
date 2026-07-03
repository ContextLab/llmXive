"""
EpisodicChunk Schema for Spatial Memory Storage.

Defines the data structure for episodic traces stored in the Memory Palace,
including content, metadata, and spatial coordinates.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


@dataclass
class EpisodicChunk:
    """
    Represents a single episodic memory trace stored in the spatial memory grid.

    Each chunk contains the encoded content, temporal metadata, and spatial
    addressing information necessary for retrieval and reconstruction.

    This schema aligns with the Memory Palace methodology by explicitly
    storing the spatial coordinate (room/locus) where the memory is placed.

    Attributes:
        chunk_id: Unique identifier for this episodic chunk.
        content: The encoded content of the episodic trace (e.g., token sequence,
                embedding vector, or text representation).
        content_type: Type of content stored (e.g., 'text', 'embedding', 'sequence').
        timestamp: Logical timestamp when the episode was encoded.
        source_dataset: Name of the dataset this chunk came from (e.g., 'babi', 'lambada').
        source_id: Original identifier from the source dataset.
        spatial_coordinate: (row, col) tuple indicating where this chunk is stored.
        confidence_score: Model's confidence in the accuracy of this memory.
        retrieval_count: Number of times this chunk has been retrieved.
        last_retrieved: Timestamp of last retrieval.
        metadata: Additional context or auxiliary information.
    """
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: Any = None
    content_type: str = "text"
    timestamp: float = field(default_factory=datetime.now().timestamp)
    source_dataset: Optional[str] = None
    source_id: Optional[str] = None
    spatial_coordinate: Optional[tuple] = None
    confidence_score: float = 1.0
    retrieval_count: int = 0
    last_retrieved: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Check if this chunk has required fields populated."""
        return (
            self.content is not None and
            self.spatial_coordinate is not None and
            self.content_type in ["text", "embedding", "sequence"]
        )

    @property
    def age(self) -> float:
        """Calculate age of the chunk in seconds since creation."""
        return datetime.now().timestamp() - self.timestamp

    def increment_retrieval(self) -> None:
        """Update retrieval statistics when this chunk is accessed."""
        self.retrieval_count += 1
        self.last_retrieved = datetime.now().timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the chunk to a dictionary for storage/transmission."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "content_type": self.content_type,
            "timestamp": self.timestamp,
            "source_dataset": self.source_dataset,
            "source_id": self.source_id,
            "spatial_coordinate": list(self.spatial_coordinate) if self.spatial_coordinate else None,
            "confidence_score": self.confidence_score,
            "retrieval_count": self.retrieval_count,
            "last_retrieved": self.last_retrieved,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpisodicChunk":
        """Deserialize a dictionary back to an EpisodicChunk."""
        # Handle coordinate conversion from list to tuple
        spatial_coord = data.get("spatial_coordinate")
        if spatial_coord is not None:
            spatial_coord = tuple(spatial_coord)

        return cls(
            chunk_id=data.get("chunk_id", str(uuid.uuid4())),
            content=data.get("content"),
            content_type=data.get("content_type", "text"),
            timestamp=data.get("timestamp", datetime.now().timestamp()),
            source_dataset=data.get("source_dataset"),
            source_id=data.get("source_id"),
            spatial_coordinate=spatial_coord,
            confidence_score=data.get("confidence_score", 1.0),
            retrieval_count=data.get("retrieval_count", 0),
            last_retrieved=data.get("last_retrieved"),
            metadata=data.get("metadata", {})
        )

    def __repr__(self) -> str:
        coord_str = f"({self.spatial_coordinate[0]}, {self.spatial_coordinate[1]})" if self.spatial_coordinate else "None"
        return (
            f"EpisodicChunk(id={self.chunk_id[:8]}..., "
            f"type={self.content_type}, coord={coord_str}, "
            f"retrievals={self.retrieval_count})"
        )


@dataclass
class EpisodicMemoryCollection:
    """
    A collection of EpisodicChunk instances with indexing and retrieval capabilities.

    Provides a higher-level interface for managing multiple episodic memories,
    including batch operations, filtering, and spatial queries.

    Attributes:
        chunks: List of all EpisodicChunk instances in the collection.
        chunk_index: Dictionary mapping chunk_id to EpisodicChunk for fast lookup.
        spatial_index: Dictionary mapping coordinate tuples to lists of chunk_ids.
    """
    chunks: List[EpisodicChunk] = field(default_factory=list)
    chunk_index: Dict[str, EpisodicChunk] = field(init=False, default_factory=dict)
    spatial_index: Dict[tuple, List[str]] = field(init=False, default_factory=dict)

    def __post_init__(self):
        """Build indexes from existing chunks."""
        self._rebuild_indexes()

    def _rebuild_indexes(self) -> None:
        """Rebuild chunk_index and spatial_index from chunks list."""
        self.chunk_index.clear()
        self.spatial_index.clear()
        for chunk in self.chunks:
            self.chunk_index[chunk.chunk_id] = chunk
            if chunk.spatial_coordinate:
                coord = chunk.spatial_coordinate
                if coord not in self.spatial_index:
                    self.spatial_index[coord] = []
                self.spatial_index[coord].append(chunk.chunk_id)

    def add_chunk(self, chunk: EpisodicChunk) -> None:
        """Add a new chunk to the collection and update indexes."""
        self.chunks.append(chunk)
        self.chunk_index[chunk.chunk_id] = chunk
        if chunk.spatial_coordinate:
            coord = chunk.spatial_coordinate
            if coord not in self.spatial_index:
                self.spatial_index[coord] = []
            self.spatial_index[coord].append(chunk.chunk_id)

    def get_chunk(self, chunk_id: str) -> Optional[EpisodicChunk]:
        """Retrieve a chunk by its ID."""
        return self.chunk_index.get(chunk_id)

    def get_chunks_at_coordinate(self, row: int, col: int) -> List[EpisodicChunk]:
        """Get all chunks stored at a specific spatial coordinate."""
        coord = (row, col)
        chunk_ids = self.spatial_index.get(coord, [])
        return [self.chunk_index[cid] for cid in chunk_ids if cid in self.chunk_index]

    def get_chunks_by_source(self, source_dataset: str) -> List[EpisodicChunk]:
        """Filter chunks by source dataset."""
        return [
            chunk for chunk in self.chunks
            if chunk.source_dataset == source_dataset
        ]

    def get_recent_chunks(self, n: int = 10) -> List[EpisodicChunk]:
        """Get the n most recently created chunks."""
        sorted_chunks = sorted(self.chunks, key=lambda c: c.timestamp, reverse=True)
        return sorted_chunks[:n]

    def get_chunks_by_retrieval_count(self, min_count: int = 1) -> List[EpisodicChunk]:
        """Get chunks that have been retrieved at least min_count times."""
        return [
            chunk for chunk in self.chunks
            if chunk.retrieval_count >= min_count
        ]

    def remove_chunk(self, chunk_id: str) -> bool:
        """
        Remove a chunk from the collection and update indexes.

        Returns:
            True if the chunk was found and removed, False otherwise.
        """
        if chunk_id not in self.chunk_index:
            return False

        chunk = self.chunk_index[chunk_id]
        self.chunks.remove(chunk)
        del self.chunk_index[chunk_id]

        if chunk.spatial_coordinate:
            coord = chunk.spatial_coordinate
            if coord in self.spatial_index:
                self.spatial_index[coord].remove(chunk_id)
                if not self.spatial_index[coord]:
                    del self.spatial_index[coord]

        return True

    def clear(self) -> None:
        """Remove all chunks and clear indexes."""
        self.chunks.clear()
        self.chunk_index.clear()
        self.spatial_index.clear()

    def __len__(self) -> int:
        return len(self.chunks)

    def __iter__(self):
        return iter(self.chunks)

    def __repr__(self) -> str:
        return f"EpisodicMemoryCollection(count={len(self.chunks)}, spatial_locations={len(self.spatial_index)})"
