"""
Unit tests for EpisodicChunk and EpisodicMemoryCollection.

Tests verify correct serialization, spatial indexing, and retrieval operations.
"""
import pytest
from code.models.episodic_chunk import EpisodicChunk, EpisodicMemoryCollection
from datetime import datetime


class TestEpisodicChunk:
    """Tests for the EpisodicChunk dataclass."""

    def test_initialization(self):
        """Test default initialization creates valid chunk with UUID."""
        chunk = EpisodicChunk(content="test content", spatial_coordinate=(1, 2))
        assert chunk.chunk_id is not None
        assert len(chunk.chunk_id) > 0
        assert chunk.content == "test content"
        assert chunk.content_type == "text"
        assert chunk.spatial_coordinate == (1, 2)
        assert chunk.confidence_score == 1.0

    def test_is_valid(self):
        """Test validation logic for required fields."""
        # Valid chunk
        chunk = EpisodicChunk(
            content="test",
            content_type="text",
            spatial_coordinate=(0, 0)
        )
        assert chunk.is_valid is True

        # Missing spatial coordinate
        chunk_no_coord = EpisodicChunk(content="test", content_type="text")
        assert chunk_no_coord.is_valid is False

        # Invalid content type
        chunk_bad_type = EpisodicChunk(
            content="test",
            content_type="invalid",
            spatial_coordinate=(0, 0)
        )
        assert chunk_bad_type.is_valid is False

    def test_age_calculation(self):
        """Test age calculation returns positive value."""
        chunk = EpisodicChunk(
            content="test",
            content_type="text",
            spatial_coordinate=(0, 0),
            timestamp=datetime.now().timestamp() - 100  # 100 seconds ago
        )
        age = chunk.age
        assert age >= 99  # Allow 1 second tolerance
        assert age <= 101

    def test_increment_retrieval(self):
        """Test retrieval count increments and timestamp updates."""
        chunk = EpisodicChunk(
            content="test",
            content_type="text",
            spatial_coordinate=(0, 0)
        )
        initial_count = chunk.retrieval_count
        chunk.increment_retrieval()
        assert chunk.retrieval_count == initial_count + 1
        assert chunk.last_retrieved is not None

    def test_to_dict(self):
        """Test serialization to dictionary."""
        chunk = EpisodicChunk(
            content="test content",
            content_type="text",
            timestamp=1000.0,
            source_dataset="babi",
            source_id="sample-1",
            spatial_coordinate=(2, 3),
            confidence_score=0.95,
            retrieval_count=5,
            last_retrieved=2000.0,
            metadata={"key": "value"}
        )
        data = chunk.to_dict()

        assert data["chunk_id"] == chunk.chunk_id
        assert data["content"] == "test content"
        assert data["content_type"] == "text"
        assert data["timestamp"] == 1000.0
        assert data["source_dataset"] == "babi"
        assert data["source_id"] == "sample-1"
        assert data["spatial_coordinate"] == [2, 3]  # Converted to list
        assert data["confidence_score"] == 0.95
        assert data["retrieval_count"] == 5
        assert data["last_retrieved"] == 2000.0
        assert data["metadata"] == {"key": "value"}

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "chunk_id": "test-id-123",
            "content": "reconstructed content",
            "content_type": "embedding",
            "timestamp": 3000.0,
            "source_dataset": "lambada",
            "source_id": "sample-2",
            "spatial_coordinate": [4, 5],  # Provided as list
            "confidence_score": 0.85,
            "retrieval_count": 10,
            "last_retrieved": 4000.0,
            "metadata": {"extra": "data"}
        }
        chunk = EpisodicChunk.from_dict(data)

        assert chunk.chunk_id == "test-id-123"
        assert chunk.content == "reconstructed content"
        assert chunk.content_type == "embedding"
        assert chunk.timestamp == 3000.0
        assert chunk.source_dataset == "lambada"
        assert chunk.source_id == "sample-2"
        assert chunk.spatial_coordinate == (4, 5)  # Converted to tuple
        assert chunk.confidence_score == 0.85
        assert chunk.retrieval_count == 10
        assert chunk.last_retrieved == 4000.0
        assert chunk.metadata == {"extra": "data"}

    def test_from_dict_missing_fields(self):
        """Test that missing fields use defaults."""
        data = {
            "chunk_id": "minimal-id",
            "content": "minimal content"
        }
        chunk = EpisodicChunk.from_dict(data)

        assert chunk.chunk_id == "minimal-id"
        assert chunk.content == "minimal content"
        assert chunk.content_type == "text"  # Default
        assert chunk.spatial_coordinate is None  # Not provided
        assert chunk.confidence_score == 1.0  # Default

    def test_repr(self):
        """Test string representation."""
        chunk = EpisodicChunk(
            content="test",
            content_type="text",
            spatial_coordinate=(3, 7),
            retrieval_count=42
        )
        repr_str = repr(chunk)
        assert "EpisodicChunk" in repr_str
        assert "type=text" in repr_str
        assert "coord=(3, 7)" in repr_str
        assert "retrievals=42" in repr_str


class TestEpisodicMemoryCollection:
    """Tests for the EpisodicMemoryCollection class."""

    def test_initialization(self):
        """Test empty collection initializes correctly."""
        collection = EpisodicMemoryCollection()
        assert len(collection) == 0
        assert len(collection.chunk_index) == 0
        assert len(collection.spatial_index) == 0

    def test_add_chunk(self):
        """Test adding a chunk updates all indexes."""
        collection = EpisodicMemoryCollection()
        chunk = EpisodicChunk(
            content="test",
            content_type="text",
            spatial_coordinate=(1, 2)
        )
        collection.add_chunk(chunk)

        assert len(collection) == 1
        assert chunk.chunk_id in collection.chunk_index
        assert (1, 2) in collection.spatial_index
        assert chunk.chunk_id in collection.spatial_index[(1, 2)]

    def test_get_chunk(self):
        """Test retrieving chunk by ID."""
        collection = EpisodicMemoryCollection()
        chunk = EpisodicChunk(
            content="test",
            content_type="text",
            spatial_coordinate=(0, 0)
        )
        collection.add_chunk(chunk)

        retrieved = collection.get_chunk(chunk.chunk_id)
        assert retrieved is chunk
        assert retrieved.content == "test"

    def test_get_chunk_not_found(self):
        """Test retrieving non-existent chunk returns None."""
        collection = EpisodicMemoryCollection()
        result = collection.get_chunk("non-existent-id")
        assert result is None

    def test_get_chunks_at_coordinate(self):
        """Test retrieving chunks at a specific coordinate."""
        collection = EpisodicMemoryCollection()
        chunk1 = EpisodicChunk(
            content="chunk1",
            content_type="text",
            spatial_coordinate=(2, 2)
        )
        chunk2 = EpisodicChunk(
            content="chunk2",
            content_type="text",
            spatial_coordinate=(2, 2)
        )
        chunk3 = EpisodicChunk(
            content="chunk3",
            content_type="text",
            spatial_coordinate=(3, 3)
        )

        collection.add_chunk(chunk1)
        collection.add_chunk(chunk2)
        collection.add_chunk(chunk3)

        at_2_2 = collection.get_chunks_at_coordinate(2, 2)
        assert len(at_2_2) == 2
        assert chunk1 in at_2_2
        assert chunk2 in at_2_2

        at_3_3 = collection.get_chunks_at_coordinate(3, 3)
        assert len(at_3_3) == 1
        assert chunk3 in at_3_3

    def test_get_chunks_by_source(self):
        """Test filtering by source dataset."""
        collection = EpisodicMemoryCollection()
        chunk1 = EpisodicChunk(
            content="babi content",
            content_type="text",
            spatial_coordinate=(0, 0),
            source_dataset="babi"
        )
        chunk2 = EpisodicChunk(
            content="lambada content",
            content_type="text",
            spatial_coordinate=(1, 1),
            source_dataset="lambada"
        )
        chunk3 = EpisodicChunk(
            content="babi content 2",
            content_type="text",
            spatial_coordinate=(2, 2),
            source_dataset="babi"
        )

        collection.add_chunk(chunk1)
        collection.add_chunk(chunk2)
        collection.add_chunk(chunk3)

        babi_chunks = collection.get_chunks_by_source("babi")
        assert len(babi_chunks) == 2
        assert chunk1 in babi_chunks
        assert chunk3 in babi_chunks

    def test_get_recent_chunks(self):
        """Test retrieving most recently created chunks."""
        collection = EpisodicMemoryCollection()
        # Create chunks with different timestamps
        chunk1 = EpisodicChunk(
            content="old",
            content_type="text",
            spatial_coordinate=(0, 0),
            timestamp=1000.0
        )
        chunk2 = EpisodicChunk(
            content="newer",
            content_type="text",
            spatial_coordinate=(1, 1),
            timestamp=2000.0
        )
        chunk3 = EpisodicChunk(
            content="newest",
            content_type="text",
            spatial_coordinate=(2, 2),
            timestamp=3000.0
        )

        collection.add_chunk(chunk1)
        collection.add_chunk(chunk2)
        collection.add_chunk(chunk3)

        recent = collection.get_recent_chunks(n=2)
        assert len(recent) == 2
        assert recent[0] == chunk3  # Newest first
        assert recent[1] == chunk2

    def test_remove_chunk(self):
        """Test removing a chunk updates all indexes."""
        collection = EpisodicMemoryCollection()
        chunk = EpisodicChunk(
            content="test",
            content_type="text",
            spatial_coordinate=(5, 5)
        )
        collection.add_chunk(chunk)

        assert collection.remove_chunk(chunk.chunk_id) is True
        assert len(collection) == 0
        assert chunk.chunk_id not in collection.chunk_index
        assert (5, 5) not in collection.spatial_index

    def test_remove_nonexistent_chunk(self):
        """Test removing non-existent chunk returns False."""
        collection = EpisodicMemoryCollection()
        result = collection.remove_chunk("non-existent")
        assert result is False

    def test_clear(self):
        """Test clearing all chunks."""
        collection = EpisodicMemoryCollection()
        for i in range(5):
            chunk = EpisodicChunk(
                content=f"chunk-{i}",
                content_type="text",
                spatial_coordinate=(i, i)
            )
            collection.add_chunk(chunk)

        assert len(collection) == 5
        collection.clear()
        assert len(collection) == 0
        assert len(collection.chunk_index) == 0
        assert len(collection.spatial_index) == 0

    def test_iteration(self):
        """Test iterating over collection yields chunks."""
        collection = EpisodicMemoryCollection()
        chunk1 = EpisodicChunk(content="c1", content_type="text", spatial_coordinate=(0, 0))
        chunk2 = EpisodicChunk(content="c2", content_type="text", spatial_coordinate=(1, 1))
        collection.add_chunk(chunk1)
        collection.add_chunk(chunk2)

        collected = list(collection)
        assert len(collected) == 2
        assert chunk1 in collected
        assert chunk2 in collected

    def test_repr(self):
        """Test string representation."""
        collection = EpisodicMemoryCollection()
        for i in range(3):
            chunk = EpisodicChunk(
                content=f"chunk-{i}",
                content_type="text",
                spatial_coordinate=(i, 0)
            )
            collection.add_chunk(chunk)

        repr_str = repr(collection)
        assert "EpisodicMemoryCollection" in repr_str
        assert "count=3" in repr_str
        assert "spatial_locations=3" in repr_str