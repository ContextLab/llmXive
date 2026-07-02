"""
Unit tests for GEO search functionality.
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data_search import search_geo, search_geo_organism_stress


def test_search_geo_url_construction():
    """Test that the correct URL and parameters are constructed."""
    with patch('code.data_search.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "ids": ["12345", "67890"],
                "uidterms": {}
            }
        }
        mock_get.return_value = mock_response

        search_geo("test query", retmax=10)

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        
        # Check URL
        assert "eutils.ncbi.nlm.nih.gov" in call_args[0][0]
        assert "esearch.fcgi" in call_args[0][0]
        
        # Check parameters
        params = call_args[1]['params']
        assert params['db'] == 'gds'
        assert params['term'] == 'test query'
        assert params['retmax'] == 10
        assert params['retmode'] == 'json'


def test_search_geo_empty_results():
    """Test handling of empty results."""
    with patch('code.data_search.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "ids": []
            }
        }
        mock_get.return_value = mock_response

        results = search_geo("empty query")
        assert results == []


def test_search_geo_organism_stress_query_construction():
    """Test that the query string is correctly constructed for organism search."""
    with patch('code.data_search.search_geo') as mock_search:
        mock_search.return_value = []
        
        organism = "Arabidopsis thaliana"
        keywords = ["herbivore", "insect"]
        
        search_geo_organism_stress(organism, keywords)
        
        expected_query = f'"{organism}" AND ({keywords[0]} OR {keywords[1]}) AND "plant"'
        mock_search.assert_called_once()
        assert mock_search.call_args[0][0] == expected_query


def test_search_geo_timeout_handling():
    """Test that timeout exceptions are propagated."""
    import requests
    
    with patch('code.data_search.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout()
        
        try:
            search_geo("test query", timeout=1)
            assert False, "Expected Timeout exception"
        except requests.exceptions.Timeout:
            pass  # Expected
