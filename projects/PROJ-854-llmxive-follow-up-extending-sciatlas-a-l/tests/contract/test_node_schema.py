"""
Contract tests for the Node schema defined in src/models/node.py.

This module validates that the Node dataclass contains all required fields
as specified in the project requirements and design documents.
"""
import pytest
from src.models.node import Node


def test_node_has_required_fields():
    """
    Contract test: Verify that the Node dataclass has all required fields.
    
    Required fields per spec:
    - id: Identifier for the node
    - title: Title of the paper/work
    - citation_count: Number of citations
    - embedding_vector: Vector representation of the title
    - primary_cluster: Cluster ID from Louvain community detection
    - topic_cluster: Cluster ID from k-means on embeddings
    """
    # Get the fields from the Node dataclass
    node_fields = {field.name for field in Node.__dataclass_fields__.values()}
    
    required_fields = {
        'id',
        'title',
        'citation_count',
        'embedding_vector',
        'primary_cluster',
        'topic_cluster'
    }
    
    # Assert all required fields are present
    missing_fields = required_fields - node_fields
    assert not missing_fields, (
        f"Node schema missing required fields: {missing_fields}. "
        f"Found: {node_fields}"
    )
    
    # Verify exact match (no unexpected extra fields in contract)
    extra_fields = node_fields - required_fields
    assert not extra_fields, (
        f"Node schema has unexpected fields: {extra_fields}. "
        f"Expected only: {required_fields}"
    )


def test_node_embedding_vector_type():
    """
    Contract test: Verify that the embedding_vector field accepts a numpy array.
    
    While the dataclass field type might be flexible, the contract implies
    that valid data will be a numpy array of floats.
    """
    import numpy as np
    
    # Create a sample embedding vector
    sample_vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    
    # Create a Node instance with the embedding vector
    node = Node(
        id="test_id",
        title="Test Title",
        citation_count=10,
        embedding_vector=sample_vector,
        primary_cluster=1,
        topic_cluster=2
    )
    
    # Verify the embedding vector is stored correctly
    assert isinstance(node.embedding_vector, np.ndarray)
    assert node.embedding_vector.dtype == np.float32
    assert len(node.embedding_vector) == 3