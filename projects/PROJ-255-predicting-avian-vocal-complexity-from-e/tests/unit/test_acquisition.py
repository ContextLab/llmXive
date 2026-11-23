"""
Unit tests for the acquisition module.

These tests verify the core functionality of fetching metadata,
filtering records, and downloading audio from Xeno-canto.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import tempfile
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.acquisition import (
    fetch_metadata,
    filter_records_by_quality,
    download_audio,
    download_batch_audio,
    create_metadata_csv,
    map_land_use_to_noise,
    get_osm_land_use,
    map_noise_levels
)

class TestFetchMetadata:
    """Tests for fetch_metadata function."""
    
    @patch('src.data.acquisition.requests.get')
    def test_fetch_metadata_success(self, mock_get):
        """Test successful metadata fetch."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'recordings': [
                {'id': '1', 'sp': 'Turdus merula', 'cnt': 'GB'},
                {'id': '2', 'sp': 'Erithacus rubecula', 'cnt': 'GB'}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Call function
        result = fetch_metadata(species='Turdus merula', limit=100)
        
        # Verify
        assert len(result) == 2
        assert result[0]['id'] == '1'
        assert result[1]['id'] == '2'
        mock_get.assert_called_once()
    
    @patch('src.data.acquisition.requests.get')
    def test_fetch_metadata_with_country(self, mock_get):
        """Test metadata fetch with country filter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'recordings': []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        fetch_metadata(country='US')
        
        # Verify country was in query
        call_args = mock_get.call_args
        assert 'q' in call_args[1]['params']
        assert 'cnt:"US"' in call_args[1]['params']['q']
    
    @patch('src.data.acquisition.requests.get')
    def test_fetch_metadata_request_exception(self, mock_get):
        """Test handling of request exceptions."""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            fetch_metadata()

class TestFilterRecordsByQuality:
    """Tests for filter_records_by_quality function."""
    
    def test_filter_quality_a(self):
        """Test filtering for quality A."""
        records = [
            {'id': '1', 'Q': 'A'},
            {'id': '2', 'Q': 'B'},
            {'id': '3', 'Q': 'A'},
            {'id': '4', 'Q': 'C'}
        ]
        
        result = filter_records_by_quality(records, min_quality='A')
        
        assert len(result) == 2
        assert all(r['Q'] == 'A' for r in result)
    
    def test_filter_quality_b(self):
        """Test filtering for quality B or better."""
        records = [
            {'id': '1', 'Q': 'A'},
            {'id': '2', 'Q': 'B'},
            {'id': '3', 'Q': 'C'}
        ]
        
        result = filter_records_by_quality(records, min_quality='B')
        
        assert len(result) == 2
        assert all(r['Q'] in ['A', 'B'] for r in result)
    
    def test_filter_empty_records(self):
        """Test filtering empty list."""
        result = filter_records_by_quality([], min_quality='A')
        assert result == []

class TestDownloadAudio:
    """Tests for download_audio function."""
    
    @patch('src.data.acquisition.requests.get')
    def test_download_audio_success(self, mock_get, tmp_path):
        """Test successful audio download."""
        # Mock response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b'dummy audio data']
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        record = {
            'id': '12345',
            'sp': 'Turdus merula',
            'file': 'recordings/12345.wav'
        }
        
        result = download_audio(record, tmp_path)
        
        assert result is not None
        assert result.exists()
        assert result.stat().st_size > 0
    
    @patch('src.data.acquisition.requests.get')
    def test_download_audio_missing_id(self, mock_get, tmp_path):
        """Test download with missing ID."""
        record = {
            'sp': 'Turdus merula',
            'file': 'recordings/12345.wav'
        }
        
        result = download_audio(record, tmp_path)
        
        assert result is None
    
    @patch('src.data.acquisition.requests.get')
    def test_download_audio_missing_file(self, mock_get, tmp_path):
        """Test download with missing file field."""
        record = {
            'id': '12345',
            'sp': 'Turdus merula'
        }
        
        result = download_audio(record, tmp_path)
        
        assert result is None
    
    @patch('src.data.acquisition.requests.get')
    def test_download_audio_empty_file(self, mock_get, tmp_path):
        """Test download that results in empty file."""
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b'']
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        record = {
            'id': '12345',
            'sp': 'Turdus merula',
            'file': 'recordings/12345.wav'
        }
        
        result = download_audio(record, tmp_path)
        
        assert result is None

class TestDownloadBatchAudio:
    """Tests for download_batch_audio function."""
    
    @patch('src.data.acquisition.download_audio')
    @patch('src.data.acquisition.time.sleep')
    def test_download_batch_success(self, mock_sleep, mock_download, tmp_path):
        """Test successful batch download."""
        mock_download.return_value = tmp_path / "test.wav"
        
        records = [
            {'id': '1', 'sp': 'Species1', 'file': 'file1.wav'},
            {'id': '2', 'sp': 'Species2', 'file': 'file2.wav'}
        ]
        
        result = download_batch_audio(records, tmp_path, max_downloads=2)
        
        assert len(result) == 2
        assert mock_download.call_count == 2
    
    @patch('src.data.acquisition.download_audio')
    @patch('src.data.acquisition.time.sleep')
    def test_download_batch_partial_success(self, mock_sleep, mock_download, tmp_path):
        """Test batch download with partial success."""
        mock_download.side_effect = [tmp_path / "test.wav", None]
        
        records = [
            {'id': '1', 'sp': 'Species1', 'file': 'file1.wav'},
            {'id': '2', 'sp': 'Species2', 'file': 'file2.wav'}
        ]
        
        result = download_batch_audio(records, tmp_path, max_downloads=2)
        
        assert len(result) == 1

class TestCreateMetadataCSV:
    """Tests for create_metadata_csv function."""
    
    def test_create_metadata_csv_success(self, tmp_path):
        """Test successful CSV creation."""
        records = [
            {'id': '1', 'sp': 'Turdus merula', 'cnt': 'GB'},
            {'id': '2', 'sp': 'Erithacus rubecula', 'cnt': 'FR'}
        ]
        
        output_path = tmp_path / "metadata.csv"
        create_metadata_csv(records, output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
        # Verify content
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert 'recording_id' in df.columns
        assert 'species' in df.columns
    
    def test_create_metadata_csv_empty(self, tmp_path):
        """Test CSV creation with empty records."""
        output_path = tmp_path / "metadata.csv"
        create_metadata_csv([], output_path)
        
        # Should create empty file or handle gracefully
        # Implementation may vary

class TestMapLandUseToNoise:
    """Tests for map_land_use_to_noise function."""
    
    def test_map_land_use_urban(self):
        """Test urban land-use mapping."""
        # TODO: Update when implementation is complete
        result = map_land_use_to_noise('urban')
        # Currently returns None as not yet implemented
        assert result is None
    
    def test_map_land_use_rural(self):
        """Test rural land-use mapping."""
        result = map_land_use_to_noise('rural')
        assert result is None
    
    def test_map_land_use_wild(self):
        """Test wild land-use mapping."""
        result = map_land_use_to_noise('wild')
        assert result is None

class TestGetOSMLandUse:
    """Tests for get_osm_land_use function."""
    
    def test_get_osm_land_use(self):
        """Test OSM land-use lookup."""
        # TODO: Update when implementation is complete
        result = get_osm_land_use(51.5074, -0.1278)
        assert result is None

class TestMapNoiseLevels:
    """Tests for map_noise_levels function."""
    
    def test_map_noise_levels(self):
        """Test noise level mapping."""
        records = [
            {'id': '1', 'lat': 51.5, 'lng': -0.1},
            {'id': '2', 'lat': 48.8, 'lng': 2.3}
        ]
        
        result = map_noise_levels(records)
        
        # Currently returns records unchanged as not yet implemented
        assert len(result) == len(records)
        assert all('noise_level_db' not in r for r in result)

# Import pandas for CSV test
import pandas as pd