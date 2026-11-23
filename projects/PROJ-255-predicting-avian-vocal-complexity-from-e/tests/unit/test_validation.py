"""
Unit tests for src/analysis/validation.py
"""
import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import csv

from src.analysis.validation import fetch_global_soundscapes_data, validate_osm_proxies, DEVIATION_THRESHOLD_DB

class TestValidationLogic:
    @pytest.fixture
    def temp_noise_csv(self):
        """Create a temporary noise_mapped.csv file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', dir=tempfile.gettempdir()) as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'latitude', 'longitude', 'noise_level_db', 'species_id'])
            writer.writerow(['rec1', '40.7128', '-74.0060', '60', 'sp1'])
            writer.writerow(['rec2', '51.5074', '-0.1278', '40', 'sp2'])
            writer.writerow(['rec3', '35.6762', '139.6503', '30', 'sp3'])
            temp_path = Path(f.name)
        yield temp_path
        os.unlink(temp_path)

    def test_validate_osm_proxies_missing_input(self, tmp_path):
        """Test validation when input file is missing."""
        # Pass a non-existent path
        log_path = validate_osm_proxies(tmp_path / "nonexistent.csv")
        
        assert log_path.exists()
        with open(log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['status'] == 'ERROR'
            assert 'Input file missing' in rows[0]['message']

    def test_validate_osm_proxies_unavailable_gs(self, temp_noise_csv, tmp_path):
        """Test validation when Global Soundscapes is unavailable."""
        with patch('src.analysis.validation.fetch_global_soundscapes_data', return_value=None):
            # We need to override the interim dir to use tmp_path for the log
            # Since validate_osm_proxies uses get_interim_data_dir, we mock that
            with patch('src.analysis.validation.get_interim_data_dir', return_value=tmp_path):
                log_path = validate_osm_proxies(temp_noise_csv)
                
                assert log_path.exists()
                with open(log_path, 'r') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    assert len(rows) == 3
                    # All should be marked UNAVAILABLE
                    for row in rows:
                        assert row['status'] == 'UNAVAILABLE'
                        assert 'Global Soundscapes dataset unavailable' in row['justification']

    def test_validate_osm_proxies_with_data_pass(self, temp_noise_csv, tmp_path):
        """Test validation with real data where deviation is within threshold."""
        mock_gs_data = [
            {'lat': 40.7128, 'lon': -74.0060, 'noise_db': 61.0}, # Deviation 1.0
            {'lat': 51.5074, 'lon': -0.1278, 'noise_db': 40.5}, # Deviation 0.5
            {'lat': 35.6762, 'lon': 139.6503, 'noise_db': 29.0} # Deviation 1.0
        ]
        
        with patch('src.analysis.validation.fetch_global_soundscapes_data', return_value=mock_gs_data):
            with patch('src.analysis.validation.get_interim_data_dir', return_value=tmp_path):
                log_path = validate_osm_proxies(temp_noise_csv)
                
                assert log_path.exists()
                with open(log_path, 'r') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    assert len(rows) == 3
                    for row in rows:
                        assert row['status'] == 'PASS'
                        assert float(row['deviation_db']) <= DEVIATION_THRESHOLD_DB

    def test_validate_osm_proxies_with_data_fail(self, temp_noise_csv, tmp_path):
        """Test validation with real data where deviation exceeds threshold."""
        mock_gs_data = [
            {'lat': 40.7128, 'lon': -74.0060, 'noise_db': 70.0}, # Deviation 10.0
            {'lat': 51.5074, 'lon': -0.1278, 'noise_db': 40.0},
            {'lat': 35.6762, 'lon': 139.6503, 'noise_db': 30.0}
        ]
        
        with patch('src.analysis.validation.fetch_global_soundscapes_data', return_value=mock_gs_data):
            with patch('src.analysis.validation.get_interim_data_dir', return_value=tmp_path):
                log_path = validate_osm_proxies(temp_noise_csv)
                
                assert log_path.exists()
                with open(log_path, 'r') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    # First row should be FAIL
                    assert rows[0]['status'] == 'FAIL'
                    assert float(rows[0]['deviation_db']) > DEVIATION_THRESHOLD_DB

class TestFetchGlobalSoundscapes:
    def test_fetch_global_soundscapes_returns_none_on_error(self):
        """Test that fetch returns None when API fails."""
        with patch('src.analysis.validation.requests.get', side_effect=Exception("Network error")):
            result = fetch_global_soundscapes_data([(40.0, -70.0)])
            assert result is None

    def test_fetch_global_soundscapes_empty_input(self):
        """Test fetch with empty coordinates."""
        result = fetch_global_soundscapes_data([])
        assert result is None