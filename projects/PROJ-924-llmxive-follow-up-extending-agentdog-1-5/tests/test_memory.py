"""
test_memory.py

Tests for memory monitoring logic in taxonomy_builder.py.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from taxonomy_builder import (
    build_centroids,
    MemoryLimitExceededError,
    load_taxonomy,
    save_centroids
)
from config import get_max_memory_gb

@pytest.fixture
def sample_taxonomy():
    """Create a sample taxonomy for testing."""
    return {
        "categories": {
            "Safe": {
                "texts": [
                    "This is a safe message.",
                    "Another safe message here.",
                    "Everything is fine.",
                    "No issues detected.",
                    "All clear."
                ]
            },
            "Attack": {
                "texts": [
                    "How to hack a system?",
                    "Stealing passwords is easy.",
                    "Bypass security controls.",
                    "Exploit this vulnerability.",
                    "Malware installation guide."
                ]
            },
            "Unknown": {
                "texts": [
                    "Random text here.",
                    "Some ambiguous content.",
                    "Unclear message.",
                    "Not sure about this.",
                    "Vague statement."
                ]
            }
        }
    }

@pytest.fixture
def temp_taxonomy_file(sample_taxonomy):
    """Create a temporary taxonomy file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_taxonomy, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_build_centroids_normal_operation(sample_taxonomy):
    """Test that centroids are built correctly under normal conditions."""
    centroids = build_centroids(sample_taxonomy)
    
    assert isinstance(centroids, dict)
    assert len(centroids) == 3
    assert "Safe" in centroids
    assert "Attack" in centroids
    assert "Unknown" in centroids
    
    # Check that centroids are lists of floats
    for category, embedding in centroids.items():
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

def test_build_centroids_empty_category(sample_taxonomy):
    """Test handling of categories with no texts."""
    sample_taxonomy["categories"]["Empty"] = {"texts": []}
    
    centroids = build_centroids(sample_taxonomy)
    
    assert "Empty" in centroids
    # Should be a zero vector
    assert all(x == 0.0 for x in centroids["Empty"])

def test_memory_limit_exceeded(sample_taxonomy):
    """Test that MemoryLimitExceededError is raised when memory limit is exceeded."""
    # Mock tracemalloc to simulate high memory usage
    with patch('taxonomy_builder.tracemalloc') as mock_tracemalloc:
        # Set up mock to return high memory values
        mock_tracemalloc.get_traced_memory.return_value = (
            100 * 1024 * 1024,  # current: 100 MB
            8 * 1024 * 1024 * 1024  # peak: 8 GB (exceeds 7 GB limit)
        )
        
        with pytest.raises(MemoryLimitExceededError) as exc_info:
            build_centroids(sample_taxonomy, max_ram_gb=7)
        
        assert "exceeded limit" in str(exc_info.value).lower()

def test_memory_limit_not_exceeded(sample_taxonomy):
    """Test that normal operation succeeds when memory is within limits."""
    # Mock tracemalloc to simulate low memory usage
    with patch('taxonomy_builder.tracemalloc') as mock_tracemalloc:
        mock_tracemalloc.get_traced_memory.return_value = (
            100 * 1024 * 1024,  # current: 100 MB
            2 * 1024 * 1024 * 1024  # peak: 2 GB (within 7 GB limit)
        )
        
        # This should not raise an exception
        centroids = build_centroids(sample_taxonomy, max_ram_gb=7)
        
        assert centroids is not None
        assert len(centroids) == 3

def test_load_taxonomy_from_file(temp_taxonomy_file):
    """Test loading taxonomy from a file."""
    taxonomy = load_taxonomy(temp_taxonomy_file)
    
    assert isinstance(taxonomy, dict)
    assert "categories" in taxonomy
    assert len(taxonomy["categories"]) == 3

def test_load_taxonomy_nonexistent_file():
    """Test that FileNotFoundError is raised for non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_taxonomy("/nonexistent/path/taxonomy.json")

def test_save_centroids(sample_taxonomy):
    """Test saving centroids to a file."""
    centroids = build_centroids(sample_taxonomy)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        saved_path = save_centroids(centroids, temp_path)
        
        assert os.path.exists(saved_path)
        
        # Verify the saved file can be loaded
        with open(saved_path, 'r') as f:
            saved_data = json.load(f)
        
        assert "centroids" in saved_data
        assert len(saved_data["centroids"]) == 3
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_memory_monitoring_integration():
    """Integration test for memory monitoring with real model (limited data)."""
    # Create a very small taxonomy to test with minimal memory
    small_taxonomy = {
        "categories": {
            "Test": {
                "texts": ["Short test text."]
            }
        }
    }
    
    # This should complete without memory issues
    centroids = build_centroids(small_taxonomy, max_ram_gb=7)
    
    assert "Test" in centroids
    assert len(centroids["Test"]) > 0