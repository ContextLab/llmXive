"""
Unit tests for taxonomy_builder.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from taxonomy_builder import load_taxonomy, build_centroids, MEMORY_LIMIT_BYTES


@pytest.fixture
def sample_taxonomy():
    """Create a temporary taxonomy file for testing."""
    data = {
        "categories": [
            {"id": "cat_001", "definition": "This is a definition for category 1.", "name": "Category 1"},
            {"id": "cat_002", "definition": "Another definition for category 2.", "name": "Category 2"},
            {"id": "cat_003", "definition": "Third category definition.", "name": "Category 3"}
        ]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        return f.name

@pytest.fixture
def empty_taxonomy():
    """Create a temporary empty taxonomy file."""
    data = {"categories": []}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        return f.name

def test_load_taxonomy_valid(sample_taxonomy):
    """Test loading a valid taxonomy file."""
    result = load_taxonomy(sample_taxonomy)
    assert "categories" in result
    assert len(result["categories"]) == 3
    assert result["categories"][0]["id"] == "cat_001"
    os.unlink(sample_taxonomy)

def test_load_taxonomy_not_found():
    """Test loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_taxonomy("non_existent_path.json")

def test_load_taxonomy_empty_categories(empty_taxonomy):
    """Test loading a taxonomy with empty categories."""
    result = load_taxonomy(empty_taxonomy)
    assert len(result["categories"]) == 0
    os.unlink(empty_taxonomy)

@patch('taxonomy_builder.SentenceTransformer')
def test_build_centroids(mock_model_class, sample_taxonomy):
    """Test centroid building with mocked model."""
    # Setup mock
    mock_model = MagicMock()
    mock_model_class.return_value = mock_model
    
    # Mock encode to return random embeddings of shape (3, 384)
    # 3 categories, 384 dimensions (standard for all-MiniLM-L6-v2)
    mock_embeddings = np.random.rand(3, 384).astype(np.float32)
    mock_model.encode.return_value = mock_embeddings
    
    taxonomy = load_taxonomy(sample_taxonomy)
    centroids = build_centroids(taxonomy)
    
    # Verify results
    assert len(centroids) == 3
    assert "cat_001" in centroids
    assert "cat_002" in centroids
    assert "cat_003" in centroids
    assert len(centroids["cat_001"]) == 384
    
    # Verify model was called
    mock_model.encode.assert_called_once()
    os.unlink(sample_taxonomy)

@patch('taxonomy_builder.SentenceTransformer')
def test_build_centroids_memory_limit(mock_model_class, sample_taxonomy):
    """Test that MemoryError is raised if memory limit is exceeded."""
    # Setup mock
    mock_model = MagicMock()
    mock_model_class.return_value = mock_model
    
    # Mock encode
    mock_model.encode.return_value = np.random.rand(3, 384).astype(np.float32)
    
    # Mock tracemalloc to simulate high memory usage
    with patch('taxonomy_builder.tracemalloc.get_traced_memory') as mock_mem:
        # Simulate peak memory exceeding limit
        mock_mem.return_value = (1024, MEMORY_LIMIT_BYTES + 1024)
        
        taxonomy = load_taxonomy(sample_taxonomy)
        with pytest.raises(MemoryError):
            build_centroids(taxonomy)
    
    os.unlink(sample_taxonomy)

@patch('taxonomy_builder.SentenceTransformer')
def test_build_centroids_empty_taxonomy(mock_model_class, empty_taxonomy):
    """Test building centroids from empty taxonomy raises ValueError."""
    mock_model = MagicMock()
    mock_model_class.return_value = mock_model
    
    taxonomy = load_taxonomy(empty_taxonomy)
    with pytest.raises(ValueError, match="Taxonomy contains no categories"):
        build_centroids(taxonomy)
    
    os.unlink(empty_taxonomy)
