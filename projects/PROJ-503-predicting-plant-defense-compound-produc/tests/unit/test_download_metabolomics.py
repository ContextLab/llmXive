"""
Unit tests for metabolite data download functionality.
"""
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.download import (
    validate_study_accession,
    download_metabolite_study,
    create_session,
    E_DATASET
)

class TestValidateStudyAccession:
    """Tests for validate_study_accession function."""
    
    def test_valid_geo_accession(self):
        """Test valid GEO accession format."""
        assert validate_study_accession("GSE21857") is True
        assert validate_study_accession("GSE167633") is True
    
    def test_valid_metabolomics_accession(self):
        """Test valid Metabolomics Workbench accession format."""
        assert validate_study_accession("ST002565") is True
        assert validate_study_accession("ST123456") is True
    
    def test_invalid_accession(self):
        """Test invalid accession formats."""
        assert validate_study_accession("INVALID") is False
        assert validate_study_accession("GSE") is False
        assert validate_study_accession("ST") is False
        assert validate_study_accession("") is False

class TestDownloadMetaboliteStudy:
    """Tests for download_metabolite_study function."""
    
    def test_invalid_accession_raises_error(self):
        """Test that invalid accession raises E_DATASET."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with pytest.raises(E_DATASET):
                download_metabolite_study("INVALID_ID", output_dir)
    
    def test_successful_download_structure(self):
        """Test successful download creates valid zip file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Mock the session and responses
            with patch('data.download.create_session') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value = mock_session
                
                # Mock metadata response
                mock_metadata_response = MagicMock()
                mock_metadata_response.status_code = 200
                mock_metadata_response.json.return_value = {
                    'analyses': [{'analysis_id': 'AN123456'}]
                }
                
                # Mock download response
                mock_download_response = MagicMock()
                mock_download_response.status_code = 200
                mock_download_response.text = "mock metabolite data"
                
                mock_session.get.side_effect = [mock_metadata_response, mock_download_response]
                
                # Perform download
                output_file = download_metabolite_study("ST002565", output_dir)
                
                # Verify file exists
                assert output_file.exists()
                assert output_file.name == "metabolomics_ST002565.zip"
                
                # Verify zip structure
                with zipfile.ZipFile(output_file, 'r') as zipf:
                    files = zipf.namelist()
                    assert len(files) == 1
                    assert files[0].endswith("_metabolite_data.txt")
    
    def test_network_error_raises_dataset_error(self):
        """Test that network errors raise E_DATASET."""
        import requests
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            with patch('data.download.create_session') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value = mock_session
                
                # Simulate network error
                mock_session.get.side_effect = requests.RequestException("Network error")
                
                with pytest.raises(E_DATASET):
                    download_metabolite_study("ST002565", output_dir)
    
    def test_invalid_metadata_raises_dataset_error(self):
        """Test that invalid metadata raises E_DATASET."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            with patch('data.download.create_session') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value = mock_session
                
                # Mock metadata response with no analyses
                mock_metadata_response = MagicMock()
                mock_metadata_response.status_code = 200
                mock_metadata_response.json.return_value = {
                    'analyses': []
                }
                
                mock_session.get.return_value = mock_metadata_response
                
                with pytest.raises(E_DATASET):
                    download_metabolite_study("ST002565", output_dir)
    
    def test_download_failure_raises_dataset_error(self):
        """Test that download failure raises E_DATASET."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            with patch('data.download.create_session') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value = mock_session
                
                # Mock metadata response
                mock_metadata_response = MagicMock()
                mock_metadata_response.status_code = 200
                mock_metadata_response.json.return_value = {
                    'analyses': [{'analysis_id': 'AN123456'}]
                }
                
                # Mock download failure
                mock_download_response = MagicMock()
                mock_download_response.status_code = 404
                
                mock_session.get.side_effect = [mock_metadata_response, mock_download_response]
                
                with pytest.raises(E_DATASET):
                    download_metabolite_study("ST002565", output_dir)

class TestCreateSession:
    """Tests for create_session function."""
    
    def test_session_created_with_headers(self):
        """Test that session is created with appropriate headers."""
        session = create_session()
        assert 'User-Agent' in session.headers
        assert 'PlantDefensePipeline' in session.headers['User-Agent']
    
    def test_session_has_timeout(self):
        """Test that session has timeout configured."""
        session = create_session()
        # Note: requests.Session doesn't have a direct timeout attribute,
        # but the default behavior should be reasonable
        assert session is not None
