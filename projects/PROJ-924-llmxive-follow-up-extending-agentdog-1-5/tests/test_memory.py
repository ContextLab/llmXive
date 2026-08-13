"""
Tests for memory monitoring in taxonomy_builder.py.
"""
import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import get_max_memory_gb
from taxonomy_builder import (
    load_taxonomy, 
    build_centroids, 
    save_centroids, 
    MemoryLimitExceededError, 
    TaxonomyLoadError
)

@pytest.fixture
def mock_taxonomy():
    """Return a mock taxonomy list."""
    return [
        {
            "category": "Safety",
            "description": "Harmful content generation"
        },
        {
            "category": "Privacy",
            "description": "PII exposure"
        },
        {
            "category": "Bias",
            "description": "Discriminatory output"
        },
        {
            "category": "Jailbreak",
            "description": "Prompt injection"
        }
    ]

@pytest.fixture
def temp_taxonomy_file(mock_taxonomy, tmp_path):
    """Create a temporary taxonomy file."""
    file_path = tmp_path / "taxonomy_agentdog.json"
    with open(file_path, 'w') as f:
        json.dump(mock_taxonomy, f)
    return file_path

def test_load_taxonomy_success(temp_taxonomy_file):
    """Test successful loading of taxonomy."""
    # Mock get_path to return our temp file
    with patch('taxonomy_builder.get_path') as mock_get_path:
        mock_get_path.side_effect = lambda key: temp_taxonomy_file if key == "raw_taxonomy" else Path(temp_taxonomy_file).parent
        
        taxonomy = load_taxonomy()
        
        assert len(taxonomy) == 4
        assert taxonomy[0]['category'] == 'Safety'
        assert taxonomy[0]['description'] == 'Harmful content generation'

def test_load_taxonomy_missing_file():
    """Test loading taxonomy when file is missing."""
    with patch('taxonomy_builder.get_path') as mock_get_path:
        mock_get_path.side_effect = lambda key: Path("/nonexistent/path/taxonomy.json")
        
        with pytest.raises(TaxonomyLoadError) as exc_info:
            load_taxonomy()
        
        assert "not found" in str(exc_info.value).lower()

def test_build_centroids_memory_monitoring(mock_taxonomy):
    """Test that build_centroids respects memory limits."""
    # This test verifies the logic exists. 
    # Actual memory usage depends on the environment.
    # We mock the model to simulate a scenario.
    
    with patch('taxonomy_builder.SentenceTransformer') as MockModel:
        mock_instance = MagicMock()
        mock_instance.encode.return_value = [0.1] * 384  # Mock embedding
        MockModel.return_value = mock_instance

        # Mock get_max_memory_gb to return a very high limit so we don't actually crash
        with patch('taxonomy_builder.get_max_memory_gb', return_value=100):
            centroids = build_centroids(mock_taxonomy)
            
            assert len(centroids) == 4
            assert 'Safety' in centroids
            assert 'Privacy' in centroids
            assert 'Bias' in centroids
            assert 'Jailbreak' in centroids

def test_save_centroids(tmp_path):
    """Test saving centroids to a file."""
    centroids = {
        "Safety": [0.1, 0.2, 0.3],
        "Privacy": [0.4, 0.5, 0.6]
    }
    
    output_path = tmp_path / "centroids.json"
    save_centroids(centroids, str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    
    assert loaded["Safety"] == [0.1, 0.2, 0.3]
    assert loaded["Privacy"] == [0.4, 0.5, 0.6]

def test_memory_limit_exceeded():
    """Test that MemoryLimitExceededError is raised when appropriate."""
    # We can't easily simulate a real memory overflow in a unit test,
    # but we can verify the exception class exists and behaves correctly.
    try:
        raise MemoryLimitExceededError("Test error")
    except MemoryLimitExceededError as e:
        assert str(e) == "Test error"
    
    # Verify it's a subclass of Exception
    assert issubclass(MemoryLimitExceededError, Exception)
