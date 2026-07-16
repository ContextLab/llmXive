import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data_download import create_session
from code.data_search import search_geo, search_geo_organism_stress

def test_search_geo_empty_response():
    """Test GEO search when API returns empty results."""
    session = create_session()
    
    with patch('code.data_search.requests.Session.get') as mock_get:
        # Mock empty response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": []}
        mock_get.return_value = mock_response
        
        results = search_geo(session, "Arabidopsis herbivore stress")
        assert len(results) == 0

def test_search_geo_with_results():
    """Test GEO search when API returns valid results."""
    session = create_session()
    
    mock_result = {
        "result": [
            {
                "accession": "GSE12345",
                "title": "Arabidopsis response to herbivore attack",
                "organism": "Arabidopsis thaliana",
                "status": "Public on Oct 01, 2023"
            }
        ]
    }
    
    with patch('code.data_search.requests.Session.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_result
        mock_get.return_value = mock_response
        
        results = search_geo(session, "Arabidopsis herbivore stress")
        
        assert len(results) == 1
        assert results[0]['accession'] == 'GSE12345'
        assert 'Arabidopsis' in results[0]['title']

def test_search_geo_organism_stress():
    """Test specialized search for organism and stress conditions."""
    session = create_session()
    
    mock_result = {
        "result": [
            {
                "accession": "GSE67890",
                "title": "Solanum lycopersicum under caterpillar stress",
                "organism": "Solanum lycopersicum",
                "status": "Public on Jan 15, 2023"
            }
        ]
    }
    
    with patch('code.data_search.requests.Session.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_result
        mock_get.return_value = mock_response
        
        results = search_geo_organism_stress(session, "Solanum", "herbivore")
        
        assert len(results) == 1
        assert results[0]['accession'] == 'GSE67890'
        assert 'Solanum' in results[0]['title']