"""
Unit tests for code/data/download.py verifying Metabolomics Workbench HTTP fetch and file storage.

Tests verify:
1. HTTP fetch from Metabolomics Workbench API succeeds for known study IDs
2. Downloaded files are stored in the correct directory structure
3. File integrity is maintained after download
4. Error handling for invalid study IDs
5. Error handling for network failures
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import requests

# Import the function to test
from code.data.download import download_metabolomics_data

# Test fixtures
VALID_STUDY_ID = "C-STUDY-0001"  # Example valid study ID format
INVALID_STUDY_ID = "INVALID-STUDY-ID"

# Mock response for successful study metadata fetch
MOCK_METADATA_RESPONSE = {
    "study_id": VALID_STUDY_ID,
    "title": "Test Plant Disease Metabolomics Study",
    "organism": "Solanum lycopersicum",
    "diseases": ["Late Blight", "Early Blight"],
    "samples": [
        {
            "sample_id": "SAMPLE-001",
            "germplasm_id": "G-001",
            "treatment": "Control",
            "timepoint": "Pre-challenge",
            "file_url": "https://example.com/file1.zip"
        },
        {
            "sample_id": "SAMPLE-002",
            "germplasm_id": "G-002",
            "treatment": "Inoculated",
            "timepoint": "Post-challenge",
            "file_url": "https://example.com/file2.zip"
        }
    ],
    "files": [
        {
            "file_id": "FILE-001",
            "file_name": "metabolomics_data.zip",
            "file_url": "https://www.metabolomicsworkbench.org/data/download.php?STUDY_ID=C-STUDY-0001&FILE_ID=FILE-001",
            "file_type": "metabolite_data"
        }
    ]
}

# Mock response for successful file download
MOCK_FILE_CONTENT = b"sample metabolomics data content for testing"

class TestDownloadMetabolomicsData:
    """Test suite for download_metabolomics_data function"""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_successful_download_with_valid_study(self, temp_output_dir):
        """Test that a valid study ID results in successful download and file storage"""
        with patch('code.data.download.requests.get') as mock_get:
            # Setup mock responses
            metadata_response = MagicMock()
            metadata_response.status_code = 200
            metadata_response.json.return_value = MOCK_METADATA_RESPONSE
            
            file_response = MagicMock()
            file_response.status_code = 200
            file_response.content = MOCK_FILE_CONTENT
            file_response.headers = {'Content-Type': 'application/zip'}
            
            # First call returns metadata, second call returns file
            mock_get.side_effect = [metadata_response, file_response]
            
            # Execute download
            result = download_metabolomics_data(
                study_id=VALID_STUDY_ID,
                output_dir=temp_output_dir
            )
            
            # Verify results
            assert result['success'] is True
            assert result['study_id'] == VALID_STUDY_ID
            assert result['files_downloaded'] == 1
            assert 'output_path' in result
            
            # Verify file was actually created
            output_file = Path(result['output_path'])
            assert output_file.exists()
            assert output_file.stat().st_size > 0
            
            # Verify correct directory structure
            expected_dir = temp_output_dir / VALID_STUDY_ID
            assert expected_dir.exists()
    
    def test_invalid_study_id_raises_error(self, temp_output_dir):
        """Test that an invalid study ID raises appropriate error"""
        with patch('code.data.download.requests.get') as mock_get:
            # Setup mock to return 404 for invalid study
            error_response = MagicMock()
            error_response.status_code = 404
            error_response.json.return_value = {"error": "Study not found"}
            mock_get.return_value = error_response
            
            # Should raise an exception
            with pytest.raises(requests.HTTPError):
                download_metabolomics_data(
                    study_id=INVALID_STUDY_ID,
                    output_dir=temp_output_dir
                )
    
    def test_network_failure_handling(self, temp_output_dir):
        """Test that network failures are handled gracefully"""
        with patch('code.data.download.requests.get') as mock_get:
            # Setup mock to raise connection error
            mock_get.side_effect = requests.ConnectionError("Network error")
            
            # Should raise appropriate exception
            with pytest.raises(requests.ConnectionError):
                download_metabolomics_data(
                    study_id=VALID_STUDY_ID,
                    output_dir=temp_output_dir
                )
    
    def test_download_creates_directory_structure(self, temp_output_dir):
        """Test that download creates proper directory structure"""
        with patch('code.data.download.requests.get') as mock_get:
            # Setup successful mocks
            metadata_response = MagicMock()
            metadata_response.status_code = 200
            metadata_response.json.return_value = MOCK_METADATA_RESPONSE
            
            file_response = MagicMock()
            file_response.status_code = 200
            file_response.content = MOCK_FILE_CONTENT
            mock_get.side_effect = [metadata_response, file_response]
            
            # Execute download
            download_metabolomics_data(
                study_id=VALID_STUDY_ID,
                output_dir=temp_output_dir
            )
            
            # Verify directory structure
            study_dir = temp_output_dir / VALID_STUDY_ID
            assert study_dir.exists()
            assert study_dir.is_dir()
            
            # Check for expected subdirectories
            raw_dir = study_dir / "raw"
            assert raw_dir.exists()
    
    def test_multiple_files_download(self, temp_output_dir):
        """Test downloading multiple files from a study"""
        # Create mock with multiple files
        multi_file_metadata = MOCK_METADATA_RESPONSE.copy()
        multi_file_metadata['files'] = [
            {
                "file_id": "FILE-001",
                "file_name": "metabolomics_data1.zip",
                "file_url": "https://example.com/file1.zip",
                "file_type": "metabolite_data"
            },
            {
                "file_id": "FILE-002",
                "file_name": "metabolomics_data2.zip",
                "file_url": "https://example.com/file2.zip",
                "file_type": "metadata"
            }
        ]
        
        with patch('code.data.download.requests.get') as mock_get:
            # Setup mocks
            metadata_response = MagicMock()
            metadata_response.status_code = 200
            metadata_response.json.return_value = multi_file_metadata
            
            file_response = MagicMock()
            file_response.status_code = 200
            file_response.content = MOCK_FILE_CONTENT
            mock_get.side_effect = [metadata_response, file_response, file_response]
            
            # Execute download
            result = download_metabolomics_data(
                study_id=VALID_STUDY_ID,
                output_dir=temp_output_dir
            )
            
            # Verify multiple files were downloaded
            assert result['files_downloaded'] == 2
    
    def test_download_preserves_file_integrity(self, temp_output_dir):
        """Test that downloaded files maintain their integrity"""
        with patch('code.data.download.requests.get') as mock_get:
            # Setup mocks
            metadata_response = MagicMock()
            metadata_response.status_code = 200
            metadata_response.json.return_value = MOCK_METADATA_RESPONSE
            
            file_response = MagicMock()
            file_response.status_code = 200
            file_response.content = MOCK_FILE_CONTENT
            mock_get.side_effect = [metadata_response, file_response]
            
            # Execute download
            result = download_metabolomics_data(
                study_id=VALID_STUDY_ID,
                output_dir=temp_output_dir
            )
            
            # Verify file content matches
            output_file = Path(result['output_path'])
            with open(output_file, 'rb') as f:
                downloaded_content = f.read()
            
            assert downloaded_content == MOCK_FILE_CONTENT
    
    def test_download_with_custom_output_directory(self, temp_output_dir):
        """Test downloading to a custom output directory"""
        custom_dir = temp_output_dir / "custom_downloads"
        
        with patch('code.data.download.requests.get') as mock_get:
            # Setup mocks
            metadata_response = MagicMock()
            metadata_response.status_code = 200
            metadata_response.json.return_value = MOCK_METADATA_RESPONSE
            
            file_response = MagicMock()
            file_response.status_code = 200
            file_response.content = MOCK_FILE_CONTENT
            mock_get.side_effect = [metadata_response, file_response]
            
            # Execute download with custom directory
            result = download_metabolomics_data(
                study_id=VALID_STUDY_ID,
                output_dir=custom_dir
            )
            
            # Verify file was created in custom directory
            output_file = Path(result['output_path'])
            assert output_file.exists()
            assert custom_dir in output_file.parents
    
    def test_download_handles_empty_study_files(self, temp_output_dir):
        """Test handling of studies with no downloadable files"""
        empty_files_metadata = MOCK_METADATA_RESPONSE.copy()
        empty_files_metadata['files'] = []
        
        with patch('code.data.download.requests.get') as mock_get:
            # Setup mock
            metadata_response = MagicMock()
            metadata_response.status_code = 200
            metadata_response.json.return_value = empty_files_metadata
            mock_get.return_value = metadata_response
            
            # Should handle gracefully with 0 files downloaded
            result = download_metabolomics_data(
                study_id=VALID_STUDY_ID,
                output_dir=temp_output_dir
            )
            
            assert result['success'] is True
            assert result['files_downloaded'] == 0
    
    def test_download_verifies_study_has_required_metadata(self, temp_output_dir):
        """Test that download verifies study has required metadata fields"""
        incomplete_metadata = {
            "study_id": VALID_STUDY_ID,
            # Missing required fields like 'files'
        }
        
        with patch('code.data.download.requests.get') as mock_get:
            # Setup mock
            metadata_response = MagicMock()
            metadata_response.status_code = 200
            metadata_response.json.return_value = incomplete_metadata
            mock_get.return_value = metadata_response
            
            # Should handle gracefully
            result = download_metabolomics_data(
                study_id=VALID_STUDY_ID,
                output_dir=temp_output_dir
            )
            
            # Should succeed but with 0 files
            assert result['success'] is True
            assert result['files_downloaded'] == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
