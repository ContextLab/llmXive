import pytest
from src.models.feature_vector import FeatureVector, create_feature_vector


def test_feature_vector_creation():
    """Test that a FeatureVector can be created with explicit values."""
    vector = FeatureVector(
        ast_depth=5,
        cyclomatic_complexity=10,
        node_count=100,
        taint_api_count=2,
        sanitization_present=True,
        embedding_similarity_score=[0.1, 0.5, 0.9]
    )
    
    assert vector.ast_depth == 5
    assert vector.cyclomatic_complexity == 10
    assert vector.node_count == 100
    assert vector.taint_api_count == 2
    assert vector.sanitization_present is True
    assert vector.embedding_similarity_score == [0.1, 0.5, 0.9]
    assert vector.id is not None


def test_create_feature_vector_factory():
    """Test the factory function creates a valid vector with all fields."""
    vector = create_feature_vector(
        ast_depth=3,
        cyclomatic_complexity=4,
        node_count=50,
        taint_api_count=0,
        sanitization_present=False,
        embedding_similarity_score=[0.2]
    )
    
    assert vector.ast_depth == 3
    assert vector.cyclomatic_complexity == 4
    assert vector.node_count == 50
    assert vector.taint_api_count == 0
    assert vector.sanitization_present is False
    assert vector.embedding_similarity_score == [0.2]


def test_feature_vector_defaults():
    """Test that default values are set correctly when no arguments are provided."""
    vector = create_feature_vector()
    
    assert vector.ast_depth is None
    assert vector.cyclomatic_complexity is None
    assert vector.node_count is None
    assert vector.taint_api_count is None
    assert vector.sanitization_present is None
    assert vector.embedding_similarity_score == []
    assert vector.id is not None


def test_feature_vector_uniqueness():
    """Test that each created vector gets a unique ID."""
    v1 = create_feature_vector(ast_depth=1)
    v2 = create_feature_vector(ast_depth=1)
    
    assert v1.id != v2.id


def test_feature_vector_invalid_embedding_type():
    """Test that passing a non-list for embedding_similarity_score raises ValueError."""
    with pytest.raises(ValueError):
        create_feature_vector(embedding_similarity_score="not a list")
        
    with pytest.raises(ValueError):
        create_feature_vector(embedding_similarity_score=0.5)