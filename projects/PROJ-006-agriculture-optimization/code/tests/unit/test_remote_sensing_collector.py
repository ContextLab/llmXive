"""
Unit tests for RemoteSensingCollector.
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.data.collectors.remote_sensing_collector import RemoteSensingCollector
from src.utils.io_helpers import write_csv_strict

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_survey_df():
    data = {
        'household_id': [1, 2, 3],
        'latitude': [-12.345, -12.346, -12.347],
        'longitude': [34.567, 34.568, 34.569],
        'land_size': [1.0, 1.5, 2.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_survey_csv(sample_survey_df, temp_output_dir):
    csv_path = temp_output_dir / "survey.csv"
    write_csv_strict(csv_path, sample_survey_df)
    return csv_path

class TestRemoteSensingCollector:
    def test_init(self, sample_survey_csv, temp_output_dir):
        cache_dir = temp_output_dir / "cache"
        collector = RemoteSensingCollector(str(sample_survey_csv), str(temp_output_dir), str(cache_dir))
        assert len(collector.survey_df) == 3
        assert collector.output_dir == temp_output_dir
        assert collector.cache_dir == cache_dir

    def test_get_survey_coordinates(self, sample_survey_csv, temp_output_dir):
        cache_dir = temp_output_dir / "cache"
        collector = RemoteSensingCollector(str(sample_survey_csv), str(temp_output_dir), str(cache_dir))
        coords = collector._get_survey_coordinates()
        assert len(coords) == 3
        assert ( -12.345, 34.567 ) in coords

    def test_generate_synthetic_granules(self, sample_survey_csv, temp_output_dir):
        cache_dir = temp_output_dir / "cache"
        collector = RemoteSensingCollector(str(sample_survey_csv), str(temp_output_dir), str(cache_dir))
        
        lat, lon = -12.345, 34.567
        granules = collector._generate_synthetic_granules(lat, lon, count=5)
        
        assert len(granules) == 5
        for g in granules:
            assert 'ndvi_value' in g
            assert 0.0 <= g['ndvi_value'] <= 1.0
            assert 'cloud_cover' in g
            assert 0.0 <= g['cloud_cover'] <= 0.95
            assert g['latitude'] == lat
            assert g['longitude'] == lon

    def test_create_synthetic_tif(self, sample_survey_csv, temp_output_dir):
        cache_dir = temp_output_dir / "cache"
        collector = RemoteSensingCollector(str(sample_survey_csv), str(temp_output_dir), str(cache_dir))
        
        granule = {
            'latitude': -12.345,
            'longitude': 34.567,
            'day_of_year': 150,
            'ndvi_value': 0.65,
            'granule_id': 'test_123'
        }
        
        tif_path = collector._create_synthetic_tif(granule)
        assert tif_path.exists()
        assert tif_path.suffix == '.tif'

    def test_collect_fallback(self, sample_survey_csv, temp_output_dir):
        cache_dir = temp_output_dir / "cache"
        collector = RemoteSensingCollector(str(sample_survey_csv), str(temp_output_dir), str(cache_dir))
        
        result = collector.collect()
        
        assert 'total_granules' in result
        assert result['total_granules'] > 0
        assert 'cached_files' in result
        assert len(result['cached_files']) > 0
        
        # Check summary file
        summary_path = temp_output_dir / "collection_summary.json"
        assert summary_path.exists()
        with open(summary_path, 'r') as f:
            summary = json.load(f)
        assert summary['total_granules'] == result['total_granules']
