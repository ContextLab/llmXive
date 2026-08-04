import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

from src.data.acquisition import (
    get_osm_land_use,
    map_land_use_to_noise,
    map_noise_levels,
    save_noise_mapped_data,
    main
)

class TestOSMMapping:
    """Unit tests for OSM land-use to noise mapping logic."""

    def test_map_land_use_to_noise_residential(self):
        """Test mapping of residential land-use to noise level."""
        assert map_land_use_to_noise('residential') == 60
        assert map_land_use_to_noise('Residential') == 60
        assert map_land_use_to_noise('RESIDENTIAL') == 60

    def test_map_land_use_to_noise_rural(self):
        """Test mapping of rural land-use to noise level."""
        assert map_land_use_to_noise('rural') == 40
        assert map_land_use_to_noise('farm') == 40
        assert map_land_use_to_noise('farmland') == 40

    def test_map_land_use_to_noise_wild(self):
        """Test mapping of wild/natural land-use to noise level."""
        assert map_land_use_to_noise('forest') == 30
        assert map_land_use_to_noise('wild') == 30
        assert map_land_use_to_noise('natural') == 30

    def test_map_land_use_to_noise_partial_match(self):
        """Test partial matching of land-use categories."""
        assert map_land_use_to_noise('residential_area') == 60
        assert map_land_use_to_noise('urban_centre') == 60
        assert map_land_use_to_noise('rural_village') == 40

    def test_map_land_use_to_noise_unknown(self):
        """Test mapping of unknown land-use returns None."""
        assert map_land_use_to_noise('unknown_type') is None
        assert map_land_use_to_noise('') is None
        assert map_land_use_to_noise(None) is None

    def test_map_noise_levels_with_land_use(self):
        """Test map_noise_levels returns correct tuple."""
        noise, found = map_noise_levels('residential')
        assert noise == 60
        assert found is True

    def test_map_noise_levels_without_land_use(self):
        """Test map_noise_levels when no land-use provided."""
        noise, found = map_noise_levels(None)
        assert noise is None
        assert found is False

class TestSaveNoiseMappedData:
    """Unit tests for saving noise-mapped data to CSV."""

    def test_save_noise_mapped_data_creates_files(self):
        """Test that save_noise_mapped_data creates output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "noise_mapped.csv"
            dropped_path = Path(tmpdir) / "dropped_missing_osm.csv"
            
            mapped_data = [
                {'recording_id': '1', 'species': 'Turdus merula', 'latitude': 51.5, 'longitude': -0.1, 'land_use': 'urban', 'noise_level_db': 60}
            ]
            dropped_data = [
                {'recording_id': '2', 'species': 'Turdus merula', 'latitude': 52.0, 'longitude': 0.0, 'reason': 'OSM data missing'}
            ]
            
            save_noise_mapped_data(mapped_data, output_path, dropped_data, dropped_path)
            
            assert output_path.exists()
            assert dropped_path.exists()
            
            df_mapped = pd.read_csv(output_path)
            df_dropped = pd.read_csv(dropped_path)
            
            assert len(df_mapped) == 1
            assert len(df_dropped) == 1
            assert df_mapped['noise_level_db'].iloc[0] == 60
            assert df_dropped['reason'].iloc[0] == 'OSM data missing'

    def test_save_noise_mapped_data_empty_mapped(self):
        """Test saving when no mapped data exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "noise_mapped.csv"
            dropped_path = Path(tmpdir) / "dropped_missing_osm.csv"
            
            save_noise_mapped_data([], output_path, [], dropped_path)
            
            assert output_path.exists()
            assert dropped_path.exists()
            
            df_mapped = pd.read_csv(output_path)
            df_dropped = pd.read_csv(dropped_path)
            
            assert len(df_mapped) == 0
            assert len(df_dropped) == 0

class TestMainFunction:
    """Unit tests for the main function of T015."""

    @patch('src.data.acquisition.fetch_metadata_from_xeno_canto')
    @patch('src.data.acquisition.filter_records_by_quality')
    @patch('src.data.acquisition.get_osm_land_use')
    @patch('src.data.acquisition.save_noise_mapped_data')
    def test_main_executes_successfully(
        self,
        mock_save,
        mock_get_osm,
        mock_filter,
        mock_fetch
    ):
        """Test main function executes end-to-end."""
        mock_fetch.return_value = [
            {'id': '1', 'sp': 'Turdus merula', 'lat': 51.5, 'lng': -0.1, 'q': 'A', 'rec-id': '123', 'file': 'http://example.com/audio.mp3'}
        ]
        mock_filter.return_value = [
            {'recording_id': '123', 'species': 'Turdus merula', 'latitude': 51.5, 'longitude': -0.1}
        ]
        mock_get_osm.return_value = 'urban'
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the config functions to use temp directory
            with patch('src.data.acquisition.get_interim_data_dir') as mock_config:
                mock_config.return_value = Path(tmpdir)
                
                with patch('src.data.acquisition.ensure_directories'):
                    noise_path, dropped_path = main(query="Turdus merula", max_results=10)
                    
                    assert noise_path.exists()
                    assert dropped_path.exists()
                    mock_save.assert_called_once()
    @patch('src.data.acquisition.fetch_metadata_from_xeno_canto')
    def test_main_handles_empty_fetch(self, mock_fetch):
        """Test main function handles empty fetch results."""
        mock_fetch.return_value = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.data.acquisition.get_interim_data_dir') as mock_config:
                mock_config.return_value = Path(tmpdir)
                
                with patch('src.data.acquisition.ensure_directories'):
                    noise_path, dropped_path = main(query="Turdus merula", max_results=10)
                    
                    assert noise_path.exists()
                    assert dropped_path.exists()
                    # Files should exist but be empty
                    df = pd.read_csv(noise_path)
                    assert len(df) == 0