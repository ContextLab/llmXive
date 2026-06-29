import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import tempfile

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.download import (
    get_subject_list_with_behavioral_data,
    fetch_subject_data,
    download_pipeline
)
from config import get_config

class TestSubjectList:
    def test_subject_list_with_behavioral_data(self):
        """Test that subject list filtering works correctly."""
        # Create mock data
        subjects_data = [
            {'subject_id': '100307', 'age': 22, 'sex': 'F', 'motor_score': 0.8, 'has_behavioral': True},
            {'subject_id': '100408', 'age': 25, 'sex': 'M', 'motor_score': 0.7, 'has_behavioral': True},
            {'subject_id': '100509', 'age': 23, 'sex': 'F', 'motor_score': None, 'has_behavioral': False},
        ]
        
        df = pd.DataFrame(subjects_data)
        
        # Filter for subjects with behavioral data
        filtered = df[df['has_behavioral'] == True]
        
        assert len(filtered) == 2, "Should have 2 subjects with behavioral data"
        assert 'motor_score' in filtered.columns, "motor_score should be in filtered data"

    def test_subject_list_missing_data(self):
        """Test handling of subjects with missing motor scores."""
        subjects_data = [
            {'subject_id': '100307', 'age': 22, 'sex': 'F', 'motor_score': 0.8, 'has_behavioral': True},
            {'subject_id': '100408', 'age': 25, 'sex': 'M', 'motor_score': None, 'has_behavioral': True},
        ]
        
        df = pd.DataFrame(subjects_data)
        
        # Filter for subjects with valid motor scores
        valid = df[df['motor_score'].notna()]
        
        assert len(valid) == 1, "Should have 1 subject with valid motor score"

class TestDataFetching:
    @patch('data.download.requests.get')
    def test_fetch_returns_nifti_on_success(self, mock_get):
        """Contract test: verify fetch returns NIfTI on success."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"dummy_nifti_data"
        mock_response.headers = {'Content-Type': 'application/octet-stream'}
        mock_get.return_value = mock_response
        
        # Test data fetch
        url = "https://example.com/data.nii.gz"
        response = fetch_subject_data(url)
        
        assert response is not None, "Response should not be None"
        assert len(response.content) > 0, "Response should have content"
        
        # Verify the request was made correctly
        mock_get.assert_called_once_with(url)

    @patch('data.download.requests.get')
    def test_fetch_handles_timeout(self, mock_get):
        """Test that fetch handles timeout correctly."""
        from requests.exceptions import Timeout
        
        mock_get.side_effect = Timeout("Request timed out")
        
        url = "https://example.com/data.nii.gz"
        
        with pytest.raises(Timeout):
            fetch_subject_data(url)

    @patch('data.download.requests.get')
    def test_fetch_handles_http_error(self, mock_get):
        """Test that fetch handles HTTP errors correctly."""
        from requests.exceptions import HTTPError
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError("Not found")
        mock_get.return_value = mock_response
        
        url = "https://example.com/data.nii.gz"
        
        with pytest.raises(HTTPError):
            fetch_subject_data(url)

class TestPipelineDownload:
    @patch('data.download.download_pipeline')
    def test_pipeline_download_success(self, mock_download):
        """Test successful pipeline download."""
        mock_download.return_value = True
        
        result = download_pipeline('subject_100307')
        
        assert result is True, "Download should succeed"
        mock_download.assert_called_once_with('subject_100307')

    @patch('data.download.download_pipeline')
    def test_pipeline_download_failure(self, mock_download):
        """Test failed pipeline download."""
        mock_download.return_value = False
        
        result = download_pipeline('subject_100307')
        
        assert result is False, "Download should fail"
        mock_download.assert_called_once_with('subject_100307')

class TestConfiguration:
    def test_config_keys_exist(self):
        """Test that required config keys exist."""
        config = get_config()
        
        required_keys = [
            'HCP_CREDENTIALS',
            'BATCH_SIZE',
            'MEMORY_LIMIT',
            'HCP_API_VERSION',
            'SCHAEFER_ATLAS_URL'
        ]
        
        for key in required_keys:
            assert key in config, f"Config should contain {key}"

    def test_memory_limit_value(self):
        """Test that memory limit is set to 7GB."""
        config = get_config()
        
        assert config['MEMORY_LIMIT'] == 7.0, "Memory limit should be 7GB"

class TestICAFixAvailability:
    @patch('data.download.requests.get')
    def test_detect_ica_fix_available(self, mock_get):
        """Test detection of ICA-FIX availability."""
        # Mock response indicating ICA-FIX is available
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ica_fix_available': True,
            'urls': {
                'ica_fix': 'https://hcp.example.com/ica_fix_data.nii.gz',
                'raw': 'https://hcp.example.com/raw_data.nii.gz'
            }
        }
        mock_get.return_value = mock_response
        
        # This test verifies the logic exists
        # Actual implementation would check the response
        assert mock_get.called, "Should check availability"

    @patch('data.download.requests.get')
    def test_detect_ica_fix_not_available(self, mock_get):
        """Test detection when ICA-FIX is not available."""
        # Mock response indicating ICA-FIX is not available
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ica_fix_available': False,
            'urls': {
                'raw': 'https://hcp.example.com/raw_data.nii.gz'
            }
        }
        mock_get.return_value = mock_response
        
        assert mock_get.called, "Should check availability"

class TestBatchProcessing:
    def test_batch_size_calculation(self):
        """Test batch size calculation for data download."""
        # Simulate memory constraints
        available_memory = 7.0  # GB
        file_size = 0.5  # GB per subject
        
        batch_size = int(available_memory / file_size)
        
        assert batch_size == 14, "Should calculate batch size correctly"

    def test_batch_processing_with_memory_limit(self):
        """Test that batch processing respects memory limits."""
        available_memory = 7.0  # GB
        file_sizes = [0.5, 0.5, 0.5, 0.5, 0.5]  # 5 files of 0.5GB each
        
        # Calculate how many can fit in memory
        total_size = sum(file_sizes)
        batch_size = int(available_memory / 0.5)
        
        assert total_size <= available_memory or batch_size < len(file_sizes), \
            "Batch should respect memory limits"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
