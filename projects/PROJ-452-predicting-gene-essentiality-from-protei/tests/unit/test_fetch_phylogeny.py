"""
Unit tests for fetch_phylogeny module.

Tests the tree fetching logic, ID mapping, and file saving capabilities.
"""
import pytest
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

# Import the module under test
from fetch_phylogeny import (
    get_taxonomic_ids_for_organisms,
    fetch_supertree,
    save_newick_tree,
    PhylogenyFetchError
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_get_taxonomic_ids_for_organisms_known():
    """Test ID lookup for known model organisms."""
    organisms = ['saccharomyces_cerevisiae', 'homo_sapiens']
    result = get_taxonomic_ids_for_organisms(organisms)
    
    assert result['saccharomyces_cerevisiae'] == '4932'
    assert result['homo_sapiens'] == '9606'

def test_get_taxonomic_ids_for_organisms_unknown(caplog):
    """Test behavior when organism ID is not found."""
    organisms = ['unknown_organism_xyz']
    
    with caplog.at_level(logging.WARNING):
        result = get_taxonomic_ids_for_organisms(organisms)
    
    assert result['unknown_organism_xyz'] is None
    assert "No taxonomic ID found" in caplog.text

@patch('fetch_phylogeny.requests.post')
def test_fetch_supertree_success(mock_post):
    """Test successful tree fetch."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "tree": "(A:1.0, B:1.0);",
        "ott_taxa": ["123", "456"]
    }
    mock_post.return_value = mock_response
    
    result = fetch_supertree(["123", "456"])
    
    assert result == "(A:1.0, B:1.0);"
    mock_post.assert_called_once()

@patch('fetch_phylogeny.requests.post')
def test_fetch_supertree_timeout(mock_post):
    """Test handling of request timeout."""
    import requests
    mock_post.side_effect = requests.exceptions.Timeout()
    
    result = fetch_supertree(["123"])
    
    assert result is None

@patch('fetch_phylogeny.requests.post')
def test_fetch_supertree_404(mock_post):
    """Test handling of 404 response."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not found"
    mock_post.return_value = mock_response
    
    result = fetch_supertree(["123"])
    
    assert result is None

def test_save_newick_tree(temp_dir):
    """Test saving a tree to file."""
    newick = "(A:1.0, B:1.0);"
    output_path = temp_dir / "test_tree.newick"
    
    success = save_newick_tree(newick, output_path)
    
    assert success
    assert output_path.exists()
    assert output_path.read_text() == newick

def test_save_newick_tree_creates_dirs(temp_dir):
    """Test that save creates parent directories."""
    newick = "(A:1.0, B:1.0);"
    output_path = temp_dir / "subdir" / "nested" / "tree.newick"
    
    success = save_newick_tree(newick, output_path)
    
    assert success
    assert output_path.exists()