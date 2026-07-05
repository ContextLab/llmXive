"""
Unit tests for the acquisition module.

These tests verify the acquisition logic without making actual API calls.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import tempfile

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.acquisition import (
    fetch_metadata,
    filter_records_by_quality,
    download_audio,
    download_batch_audio,
    create_metadata_csv
)
from src.utils.config import get_raw_data_dir, get_interim_data_dir


class TestFetchMetadata:
    """Tests for the fetch_metadata function."""
    
    @patch('src.data.acquisition.requests.get')
    def test_fetch_metadata_success(self, mock_get):
        """Test successful metadata fetch."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'count': '2',
            'recordings': [
                {'id': '1', 'species': 'Turdus merula', 'file': '1.mp3', 'dur': '10'},
                {'id': '2', 'species': 'Parus major', 'file': '2.mp3', 'dur': '15'}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Call function
        records = fetch_metadata("Q", max_records=2)
        
        # Assertions
        assert len(records) == 2
        assert records[0]['id'] == '1'
        assert records[1]['id'] == '2'
        mock_get.assert_called_once()
    
    @patch('src.data.acquisition.requests.get')
    def test_fetch_metadata_empty_response(self, mock_get):
        """Test fetch with empty response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'count': '0',
            'recordings': []
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        records = fetch_metadata("Q", max_records=10)
        
        assert len(records) == 0
    
    @patch('src.data.acquisition.requests.get')
    def test_fetch_metadata_request_exception(self, mock_get):
        """Test fetch with request exception."""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            fetch_metadata("Q", max_records=10)


class TestFilterRecordsByQuality:
    """Tests for the filter_records_by_quality function."""
    
    def test_filter_valid_records(self):
        """Test filtering with valid records."""
        records = [
            {'id': '1', 'species': 'A', 'lat': 1.0, 'lon': 1.0, 'dur': '10'},
            {'id': '2', 'species': 'B', 'lat': 2.0, 'lon': 2.0, 'dur': '20'},
            {'id': '3', 'species': 'C', 'lat': 3.0, 'lon': 3.0, 'dur': '30'}
        ]
        
        filtered = filter_records_by_quality(records, min_duration=5, max_duration=100)
        
        assert len(filtered) == 3
    
    def test_filter_by_duration(self):
        """Test filtering by duration."""
        records = [
            {'id': '1', 'species': 'A', 'lat': 1.0, 'lon': 1.0, 'dur': '3'},  # Too short
            {'id': '2', 'species': 'B', 'lat': 2.0, 'lon': 2.0, 'dur': '10'},  # Valid
            {'id': '3', 'species': 'C', 'lat': 3.0, 'lon': 3.0, 'dur': '500'}  # Too long
        ]
        
        filtered = filter_records_by_quality(records, min_duration=5, max_duration=100)
        
        assert len(filtered) == 1
        assert filtered[0]['id'] == '2'
    
    def test_filter_missing_fields(self):
        """Test filtering with missing required fields."""
        records = [
            {'id': '1', 'species': 'A', 'lat': 1.0, 'lon': 1.0, 'dur': '10'},  # Valid
            {'id': '2', 'species': 'B', 'lat': None, 'lon': 2.0, 'dur': '15'},  # Missing lat
            {'id': '3', 'species': 'C', 'dur': '20'}  # Missing lat and lon
        ]
        
        filtered = filter_records_by_quality(records, min_duration=5, max_duration=100)
        
        assert len(filtered) == 1
        assert filtered[0]['id'] == '1'
    
    def test_filter_invalid_duration(self):
        """Test filtering with invalid duration."""
        records = [
            {'id': '1', 'species': 'A', 'lat': 1.0, 'lon': 1.0, 'dur': '10'},  # Valid
            {'id': '2', 'species': 'B', 'lat': 2.0, 'lon': 2.0, 'dur': 'invalid'},  # Invalid
            {'id': '3', 'species': 'C', 'lat': 3.0, 'lon': 3.0, 'dur': ''}  # Empty
        ]
        
        filtered = filter_records_by_quality(records, min_duration=5, max_duration=100)
        
        assert len(filtered) == 1
        assert filtered[0]['id'] == '1'


class TestDownloadAudio:
    """Tests for the download_audio function."""
    
    @patch('src.data.acquisition.requests.get')
    def test_download_audio_success(self, mock_get, tmp_path):
        """Test successful audio download."""
        # Mock response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b'fake_audio_data']
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        record = {
            'id': '123',
            'file': 'XC123.mp3',
            'species': 'Turdus merula'
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = download_audio(record, output_dir)
            
            assert result is not None
            assert result.exists()
            assert result.stat().st_size > 0
    
    def test_download_audio_missing_file(self, tmp_path):
        """Test download with missing file field."""
        record = {
            'id': '123',
            'species': 'Turdus merula'
        }
        
        result = download_audio(record, tmp_path)
        
        assert result is None
    
    @patch('src.data.acquisition.requests.get')
    def test_download_audio_request_exception(self, mock_get, tmp_path):
        """Test download with request exception."""
        mock_get.side_effect = Exception("Network error")
        
        record = {
            'id': '123',
            'file': 'XC123.mp3',
            'species': 'Turdus merula'
        }
        
        result = download_audio(record, tmp_path)
        
        assert result is None


class TestDownloadBatchAudio:
    """Tests for the download_batch_audio function."""
    
    @patch('src.data.acquisition.requests.get')
    def test_download_batch_audio(self, mock_get, tmp_path):
        """Test batch audio download."""
        # Mock response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b'fake_audio_data']
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        records = [
            {'id': '1', 'file': 'XC1.mp3', 'species': 'A'},
            {'id': '2', 'file': 'XC2.mp3', 'species': 'B'},
            {'id': '3', 'file': 'XC3.mp3', 'species': 'C'}
        ]
        
        stats = download_batch_audio(records, tmp_path, max_downloads=2)
        
        assert stats['total'] == 3
        assert stats['downloaded'] == 2
        assert stats['failed'] == 0


class TestCreateMetadataCSV:
    """Tests for the create_metadata_csv function."""
    
    def test_create_metadata_csv(self, tmp_path):
        """Test metadata CSV creation."""
        records = [
            {'id': '1', 'species': 'A', 'lat': 1.0, 'lon': 1.0, 'dur': '10', 'file': 'XC1.mp3'},
            {'id': '2', 'species': 'B', 'lat': 2.0, 'lon': 2.0, 'dur': '15', 'file': 'XC2.mp3'}
        ]
        
        output_path = tmp_path / 'metadata.csv'
        create_metadata_csv(records, output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
        # Verify CSV content
        with open(output_path, 'r') as f:
            content = f.read()
            assert 'id' in content
            assert 'species' in content
            assert '1' in content
            assert '2' in content
