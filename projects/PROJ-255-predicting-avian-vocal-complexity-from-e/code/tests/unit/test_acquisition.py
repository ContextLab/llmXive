"""
Unit tests for the acquisition module.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import tempfile
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

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

@pytest.fixture
def sample_record():
    return {
        'r': '123456',
        'file': 'https://xeno-canto.org/audio/123456.flac',
        'sp': 'Turdus merula',
        'snt': 'Turdus merula',
        'rec': 'John Doe',
        'date': '2023-01-15',
        'cnt': 'United Kingdom',
        'lat': 51.5074,
        'lon': -0.1278,
        'q': 'A',
        'lc': 'CC BY-NC 4.0',
        'url': 'https://xeno-canto.org/123456',
        'fl': 'flac',
        'dur': 10.5,
        'sz': 1024000
    }

@pytest.fixture
def sample_records(sample_record):
    return [
        sample_record,
        {**sample_record, 'r': '123457', 'q': 'B'},
        {**sample_record, 'r': '123458', 'q': 'C'},
        {**sample_record, 'r': '123459', 'q': 'D'},
        {**sample_record, 'r': '123460', 'q': 'E'},
    ]

class TestFetchMetadata:
    @patch('src.data.acquisition.requests.get')
    def test_fetch_metadata_success(self, mock_get, sample_record):
        """Test successful metadata fetch from API"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'recordings': [sample_record],
            'numPages': 1
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        records = fetch_metadata(species_query="Turdus merula", max_records=10)
        
        assert len(records) == 1
        assert records[0]['sp'] == 'Turdus merula'
        mock_get.assert_called_once()

    @patch('src.data.acquisition.requests.get')
    def test_fetch_metadata_quality_filtering(self, mock_get, sample_records):
        """Test that low quality records are filtered"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'recordings': sample_records,
            'numPages': 1
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        records = fetch_metadata(species_query="all", max_records=10, min_quality='C')
        
        # Should only include A, B, C quality
        assert len(records) == 3
        assert all(r['q'] in ['A', 'B', 'C'] for r in records)

    def test_fetch_metadata_invalid_quality(self):
        """Test that invalid quality grade raises error"""
        with pytest.raises(ValueError, match="Invalid quality grade"):
            fetch_metadata(species_query="all", min_quality='X')

class TestFilterRecordsByQuality:
    def test_filter_by_quality_a(self, sample_records):
        """Test filtering for quality A only"""
        filtered = filter_records_by_quality(sample_records, min_quality='A')
        assert len(filtered) == 1
        assert filtered[0]['q'] == 'A'

    def test_filter_by_quality_c(self, sample_records):
        """Test filtering for quality C and above"""
        filtered = filter_records_by_quality(sample_records, min_quality='C')
        assert len(filtered) == 3
        assert all(r['q'] in ['A', 'B', 'C'] for r in filtered)

    def test_filter_invalid_quality(self, sample_records):
        """Test that invalid quality raises error"""
        with pytest.raises(ValueError):
            filter_records_by_quality(sample_records, min_quality='X')

    def test_filter_empty_list(self):
        """Test filtering empty list"""
        filtered = filter_records_by_quality([], min_quality='A')
        assert len(filtered) == 0

class TestDownloadAudio:
    @patch('src.data.acquisition.requests.get')
    def test_download_audio_success(self, mock_get, sample_record, tmp_path):
        """Test successful audio download"""
        mock_response = MagicMock()
        mock_response.content = b'fake_audio_data'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = download_audio(sample_record, tmp_path)
        
        assert result is not None
        assert result.exists()
        assert result.stat().st_size > 0
        assert result.suffix == '.flac'

    def test_download_audio_missing_id(self, tmp_path):
        """Test download fails with missing recording ID"""
        record = {**sample_record, 'r': ''}
        result = download_audio(record, tmp_path)
        assert result is None

    def test_download_audio_missing_url(self, tmp_path):
        """Test download fails with missing file URL"""
        record = {**sample_record, 'file': ''}
        result = download_audio(record, tmp_path)
        assert result is None

    @patch('src.data.acquisition.requests.get')
    def test_download_audio_empty_file(self, mock_get, sample_record, tmp_path):
        """Test download fails with empty file"""
        mock_response = MagicMock()
        mock_response.content = b''
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = download_audio(sample_record, tmp_path)
        assert result is None
        assert not (tmp_path / f"{sample_record['r']}_Turdus_merula_John_Doe.flac").exists()

class TestDownloadBatchAudio:
    @patch('src.data.acquisition.requests.get')
    def test_download_batch_success(self, mock_get, sample_records, tmp_path):
        """Test batch download success"""
        mock_response = MagicMock()
        mock_response.content = b'fake_audio_data'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        downloaded, failed = download_batch_audio(sample_records, tmp_path, batch_size=2)
        
        assert len(downloaded) == 5
        assert len(failed) == 0

    @patch('src.data.acquisition.requests.get')
    def test_download_batch_partial_failure(self, mock_get, sample_records, tmp_path):
        """Test batch download with some failures"""
        def side_effect(*args, **kwargs):
            mock_response = MagicMock()
            if '123457' in str(args):
                mock_response.content = b''  # Simulate empty file
            else:
                mock_response.content = b'fake_audio_data'
            mock_response.raise_for_status = MagicMock()
            return mock_response
        
        mock_get.side_effect = side_effect
        
        downloaded, failed = download_batch_audio(sample_records, tmp_path, batch_size=2)
        
        assert len(downloaded) == 4
        assert len(failed) == 1

class TestCreateMetadataCSV:
    def test_create_metadata_csv(self, sample_records, tmp_path):
        """Test CSV creation from records"""
        output_path = tmp_path / "metadata.csv"
        create_metadata_csv(sample_records, output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_create_metadata_csv_empty(self, tmp_path):
        """Test CSV creation with empty records"""
        output_path = tmp_path / "metadata.csv"
        create_metadata_csv([], output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size == 0

    def test_create_metadata_csv_columns(self, sample_record, tmp_path):
        """Test that CSV has expected columns"""
        output_path = tmp_path / "metadata.csv"
        create_metadata_csv([sample_record], output_path)
        
        import pandas as pd
        df = pd.read_csv(output_path)
        
        expected_columns = [
            'recording_id', 'file', 'species_id', 'species_common',
            'species_scientific', 'recorder', 'date', 'country',
            'latitude', 'longitude', 'quality', 'license', 'url',
            'file_type', 'file_duration', 'file_size', 'downloaded_path'
        ]
        
        for col in expected_columns:
            assert col in df.columns

class TestOSMMapping:
    def test_get_osm_land_use_placeholder(self):
        """Test that OSM land-use returns None (placeholder)"""
        result = get_osm_land_use(51.5074, -0.1278)
        assert result is None

    def test_map_land_use_to_noise_urban(self):
        """Test noise mapping for urban land-use"""
        assert map_land_use_to_noise('urban') == 60.0
        assert map_land_use_to_noise('Urban') == 60.0
        assert map_land_use_to_noise('URBAN') == 60.0

    def test_map_land_use_to_noise_wild(self):
        """Test noise mapping for wild land-use"""
        assert map_land_use_to_noise('wild') == 30.0
        assert map_land_use_to_noise('forest') == 30.0

    def test_map_land_use_to_noise_none(self):
        """Test noise mapping with None input"""
        assert map_land_use_to_noise(None) is None

    def test_map_land_use_to_noise_unknown(self):
        """Test noise mapping with unknown land-use"""
        assert map_land_use_to_noise('unknown') is None

class TestMapNoiseLevels:
    def test_map_noise_levels_with_coordinates(self, sample_record):
        """Test noise mapping with valid coordinates"""
        records = [sample_record]
        result = map_noise_levels(records)
        
        assert result[0]['land_use'] is None  # OSM placeholder
        assert result[0]['noise_level_db'] is None

    def test_map_noise_levels_missing_coordinates(self, sample_record):
        """Test noise mapping with missing coordinates"""
        record = {**sample_record, 'lat': None, 'lon': None}
        result = map_noise_levels([record])
        
        assert result[0]['land_use'] is None
        assert result[0]['noise_level_db'] is None

    def test_map_noise_levels_invalid_coordinates(self, sample_record):
        """Test noise mapping with invalid coordinates"""
        record = {**sample_record, 'lat': 200, 'lon': -200}
        result = map_noise_levels([record])
        
        assert result[0]['land_use'] is None
        assert result[0]['noise_level_db'] is None
