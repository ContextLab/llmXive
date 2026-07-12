"""
Unit tests for the Node dataclass in src.models.node.
"""
import pytest
import numpy as np
from src.models.node import Node


class TestNodeInitialization:
    """Tests for basic Node instantiation and validation."""

    def test_node_creation_minimal(self):
        """Test creating a node with only required fields."""
        node = Node(id="test_123", title="Test Paper", citation_count=10)
        assert node.id == "test_123"
        assert node.title == "Test Paper"
        assert node.citation_count == 10
        assert node.embedding_vector is None
        assert node.primary_cluster is None
        assert node.topic_cluster is None

    def test_node_creation_with_optional_fields(self):
        """Test creating a node with all fields populated."""
        emb = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        node = Node(
            id="test_456",
            title="Advanced Topic",
            citation_count=100,
            embedding_vector=emb,
            primary_cluster=1,
            topic_cluster=5
        )
        assert node.id == "test_456"
        assert np.array_equal(node.embedding_vector, emb)
        assert node.primary_cluster == 1
        assert node.topic_cluster == 5

    def test_embedding_conversion_from_list(self):
        """Test that list embeddings are converted to numpy arrays."""
        node = Node(
            id="test_789",
            title="List Embedding",
            citation_count=5,
            embedding_vector=[0.5, 0.5, 0.5]
        )
        assert isinstance(node.embedding_vector, np.ndarray)
        assert node.embedding_vector.dtype == np.float32

    def test_embedding_dtype_normalization(self):
        """Test that float64 embeddings are converted to float32."""
        emb_float64 = np.array([1.0, 2.0], dtype=np.float64)
        node = Node(
            id="test_dtype",
            title="Dtype Test",
            citation_count=0,
            embedding_vector=emb_float64
        )
        assert node.embedding_vector.dtype == np.float32

    def test_negative_citation_count_raises(self):
        """Test that negative citation counts raise ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            Node(id="bad", title="Bad", citation_count=-1)


class TestNodeSerialization:
    """Tests for to_dict and from_dict methods."""

    def test_to_dict_roundtrip(self):
        """Test that converting to dict and back preserves data."""
        original = Node(
            id="roundtrip_1",
            title="Round Trip",
            citation_count=42,
            embedding_vector=[0.1, 0.2],
            primary_cluster=10,
            topic_cluster=20
        )
        data = original.to_dict()
        restored = Node.from_dict(data)

        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.citation_count == original.citation_count
        assert np.array_equal(restored.embedding_vector, original.embedding_vector)
        assert restored.primary_cluster == original.primary_cluster
        assert restored.topic_cluster == original.topic_cluster

    def test_to_dict_handles_none_embedding(self):
        """Test that None embedding is preserved in dict conversion."""
        node = Node(id="none_emb", title="No Emb", citation_count=0)
        data = node.to_dict()
        assert data["embedding_vector"] is None
        restored = Node.from_dict(data)
        assert restored.embedding_vector is None

    def test_from_dict_with_missing_optional_fields(self):
        """Test that missing optional fields in dict result in None."""
        data = {
            "id": "missing_opt",
            "title": "Missing Opt",
            "citation_count": 1
        }
        node = Node.from_dict(data)
        assert node.embedding_vector is None
        assert node.primary_cluster is None
        assert node.topic_cluster is None

class TestNodeRepr:
    """Tests for the __repr__ method."""

    def test_repr_truncates_long_title(self):
        """Test that long titles are truncated in repr."""
        long_title = "A" * 50
        node = Node(id="repr_test", title=long_title, citation_count=0)
        rep = repr(node)
        assert "..." in rep
        assert len(rep) < 100  # Sanity check on length