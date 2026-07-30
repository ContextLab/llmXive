"""
Tests for taxonomy_builder module.
"""
import json
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "projects" / "PROJ-924-llmxive-follow-up-extending-agentdog-1-5" / "code"))

from taxonomy_builder import load_taxonomy, build_centroids, save_centroids, MemoryLimitExceededError
from config import get_path

@pytest.fixture
def sample_taxonomy():
    """Sample taxonomy for testing."""
    return [
        {
            "category": "Safe",
            "examples": [
                "This is a safe message.",
                "Another safe message here."
            ]
        },
        {
            "category": "Attack",
            "examples": [
                "This is an attack message.",
                "Another attack message here."
            ]
        }
    ]

@pytest.fixture
def temp_taxonomy_file(sample_taxonomy):
    """Create a temporary taxonomy file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_taxonomy, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_output_file():
    """Create a temporary output file path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    os.unlink(temp_path)  # Remove the file, we just need the path
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_load_taxonomy(temp_taxonomy_file):
    """Test loading taxonomy from file."""
    taxonomy = load_taxonomy(temp_taxonomy_file)
    assert len(taxonomy) == 2
    assert taxonomy[0]['category'] == 'Safe'
    assert taxonomy[1]['category'] == 'Attack'

def test_build_centroids(sample_taxonomy):
    """Test building centroids from taxonomy."""
    try:
        centroids_data = build_centroids(sample_taxonomy)
        assert 'categories' in centroids_data
        assert 'embeddings' in centroids_data
        assert 'model_used' in centroids_data
        assert len(centroids_data['categories']) == 2
        assert len(centroids_data['embeddings']) == 2
        assert centroids_data['metadata']['num_categories'] == 2
    except ImportError:
        pytest.skip("sentence-transformers not installed")

def test_save_centroids(sample_taxonomy, temp_output_file):
    """Test saving centroids to file."""
    try:
        centroids_data = build_centroids(sample_taxonomy)
        output_path = save_centroids(centroids_data, temp_output_file)
        
        assert os.path.exists(output_path)
        
        # Verify the saved file
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['categories'] == centroids_data['categories']
        assert saved_data['metadata']['num_categories'] == centroids_data['metadata']['num_categories']
    except ImportError:
        pytest.skip("sentence-transformers not installed")

def test_save_centroids_creates_directory(temp_taxonomy_file):
    """Test that save_centroids creates the output directory if it doesn't exist."""
    try:
        taxonomy = load_taxonomy(temp_taxonomy_file)
        centroids_data = build_centroids(taxonomy)
        
        # Create a path in a non-existent directory
        temp_dir = tempfile.mkdtemp()
        nested_path = os.path.join(temp_dir, "nested", "path", "centroids.json")
        
        output_path = save_centroids(centroids_data, nested_path)
        
        assert os.path.exists(output_path)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    except ImportError:
        pytest.skip("sentence-transformers not installed")

def test_load_taxonomy_file_not_found():
    """Test that load_taxonomy raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_taxonomy("/nonexistent/path/taxonomy.json")

def test_build_centroids_empty_taxonomy():
    """Test building centroids from empty taxonomy."""
    try:
        centroids_data = build_centroids([])
        assert centroids_data['categories'] == []
        assert centroids_data['embeddings'] == []
    except ImportError:
        pytest.skip("sentence-transformers not installed")
