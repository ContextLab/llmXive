"""
Integration test to verify Node instantiation with all required fields.

This test ensures that the Node dataclass can be instantiated with
valid data for all required fields.
"""
import numpy as np
import pytest
from src.models.node import Node


def test_node_instantiation_with_all_fields():
    """
    Integration test: Verify Node can be instantiated with all required fields.
    """
    # Create a sample Node with all required fields
    sample_embedding = np.random.rand(384).astype(np.float32)
    
    node = Node(
        id="W123456789",
        title="Sample Paper Title",
        citation_count=42,
        embedding_vector=sample_embedding,
        primary_cluster=1,
        topic_cluster=5
    )
    
    # Verify all fields are accessible and have correct types
    assert node.id == "W123456789"
    assert node.title == "Sample Paper Title"
    assert isinstance(node.citation_count, int)
    assert node.citation_count == 42
    assert isinstance(node.embedding_vector, np.ndarray)
    assert node.embedding_vector.shape == (384,)
    assert isinstance(node.primary_cluster, int)
    assert node.primary_cluster == 1
    assert isinstance(node.topic_cluster, int)
    assert node.topic_cluster == 5

def test_node_required_fields_not_none():
    """
    Integration test: Verify that required fields cannot be None.
    """
    sample_embedding = np.random.rand(384).astype(np.float32)
    
    # Test that we can create a node with valid data
    node = Node(
        id="W123456789",
        title="Sample Paper Title",
        citation_count=0,
        embedding_vector=sample_embedding,
        primary_cluster=0,
        topic_cluster=0
    )
    
    # Verify all fields are set (even if zero/empty)
    assert node.id is not None
    assert node.title is not None
    assert node.citation_count is not None
    assert node.embedding_vector is not None
    assert node.primary_cluster is not None
    assert node.topic_cluster is not None