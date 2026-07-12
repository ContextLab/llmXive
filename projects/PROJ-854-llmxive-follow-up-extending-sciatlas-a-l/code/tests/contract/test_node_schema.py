import pytest
from src.models.node import Node

def test_node_has_required_fields():
    """
    Contract test: Verify that the Node dataclass has all required fields
    as specified in the design documents.
    """
    # Create a valid node instance
    node = Node(
        id="W123456",
        title="Sample Paper",
        citation_count=42,
        embedding_vector=None,
        primary_cluster=1,
        topic_cluster=5
    )

    # Check existence of fields
    assert hasattr(node, 'id')
    assert hasattr(node, 'title')
    assert hasattr(node, 'citation_count')
    assert hasattr(node, 'embedding_vector')
    assert hasattr(node, 'primary_cluster')
    assert hasattr(node, 'topic_cluster')

    # Check types/values
    assert node.id == "W123456"
    assert node.title == "Sample Paper"
    assert node.citation_count == 42
    assert node.primary_cluster == 1
    assert node.topic_cluster == 5
    
    # Test with None values for optional fields
    node_partial = Node(
        id="W789",
        title="Partial",
        citation_count=0,
        embedding_vector=None,
        primary_cluster=None,
        topic_cluster=None
    )
    assert node_partial.primary_cluster is None
    assert node_partial.topic_cluster is None

def test_node_embedding_vector_type():
    """
    Contract test: Verify embedding_vector can hold a numpy array or None.
    """
    import numpy as np
    vec = np.array([0.1, 0.2, 0.3])
    node = Node(
        id="W999",
        title="Vec Test",
        citation_count=0,
        embedding_vector=vec,
        primary_cluster=0,
        topic_cluster=0
    )
    assert isinstance(node.embedding_vector, np.ndarray)
    assert len(node.embedding_vector) == 3
