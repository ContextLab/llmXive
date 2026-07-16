import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data_download import search_metabolomics_workbench, validate_studies, create_session

def test_search_metabolomics_workbench_empty_response():
    """Test search behavior when API returns empty results."""
    session = create_session()
    
    with patch('code.data_download.requests.Session.get') as mock_get:
        # Mock empty response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        results = search_metabolomics_workbench(session, ["terpenoid"])
        assert len(results) == 0

def test_search_metabolomics_workbench_with_plant_data():
    """Test search behavior when API returns plant-related data."""
    session = create_session()
    
    mock_study = {
        'STUDY_ID': 'MW_TEST_001',
        'TITLE': 'Metabolomic profiling of Arabidopsis under herbivore stress',
        'ABSTRACT': 'Analysis of terpenoids and alkaloids in Arabidopsis thaliana.'
    }
    
    with patch('code.data_download.requests.Session.get') as mock_get:
        # Mock response with plant study
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [mock_study]
        mock_get.return_value = mock_response
        
        results = search_metabolomics_workbench(session, ["terpenoid"])
        
        assert len(results) == 1
        assert results[0]['study_id'] == 'MW_TEST_001'
        assert 'Arabidopsis' in results[0]['title']

def test_validate_studies_with_samples():
    """Test validation of studies that have samples."""
    session = create_session()
    study = {
        'study_id': 'MW_TEST_001',
        'title': 'Test Study',
        'source': 'Metabolomics Workbench'
    }
    
    mock_samples = [
        {'SAMPLE_ID': 'S1', 'SAMPLE_NAME': 'Sample 1'},
        {'SAMPLE_ID': 'S2', 'SAMPLE_NAME': 'Sample 2'}
    ]
    
    with patch('code.data_download.requests.Session.get') as mock_get:
        # First call is for study summary (already mocked in search), 
        # second call is for sample summary
        mock_sample_response = MagicMock()
        mock_sample_response.status_code = 200
        mock_sample_response.json.return_value = mock_samples
        mock_get.return_value = mock_sample_response
        
        valid_studies = validate_studies(session, [study])
        
        assert len(valid_studies) == 1
        assert valid_studies[0]['sample_count'] == 2
        assert 'samples' in valid_studies[0]

def test_validate_studies_no_samples():
    """Test validation of studies that have no samples."""
    session = create_session()
    study = {
        'study_id': 'MW_TEST_002',
        'title': 'Test Study No Samples',
        'source': 'Metabolomics Workbench'
    }
    
    with patch('code.data_download.requests.Session.get') as mock_get:
        mock_sample_response = MagicMock()
        mock_sample_response.status_code = 200
        mock_sample_response.json.return_value = []
        mock_get.return_value = mock_sample_response
        
        valid_studies = validate_studies(session, [study])
        
        assert len(valid_studies) == 0
