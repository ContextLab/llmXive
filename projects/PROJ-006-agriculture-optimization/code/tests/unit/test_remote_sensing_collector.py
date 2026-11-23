"""
Unit tests for RemoteSensingCollector (T016a).
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np

from src.data.collectors.remote_sensing_collector import RemoteSensingCollector


class TestRemoteSensingCollector:

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    def test_init_creates_directory(self, temp_dir):
        """Test that initialization creates the output directory."""
        collector = RemoteSensingCollector(output_dir=temp_dir)
        assert os.path.exists(temp_dir)

    def test_generate_ndvi_timeseries_range(self, temp_dir):
        """Test that generated NDVI values are within valid range [0, 1]."""
        collector = RemoteSensingCollector(output_dir=temp_dir)
        ndvi = collector._generate_synthetic_ndvi_timeseries(lat=0.0, lon=0.0, n_months=12)
        
        assert len(ndvi) == 12
        for val in ndvi:
            assert 0.0 <= val <= 1.0, f"NDVI value {val} out of range"

    def test_generate_cloud_cover_range(self, temp_dir):
        """Test that cloud cover is generated within [0.0, 0.9]."""
        collector = RemoteSensingCollector(output_dir=temp_dir)
        cloud = collector._generate_cloud_cover()
        assert 0.0 <= cloud <= 0.9, f"Cloud cover {cloud} out of range"

    def test_create_synthetic_tiff_structure(self, temp_dir):
        """Test that the synthetic TIFF file is created and contains data."""
        collector = RemoteSensingCollector(output_dir=temp_dir)
        ndvi = [0.5] * 12
        cloud = 0.5
        output_path = Path(temp_dir) / "test.tif"
        
        collector._create_synthetic_tiff(ndvi, cloud, output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
        # Verify it starts with TIFF magic bytes
        with open(output_path, 'rb') as f:
            header = f.read(4)
            assert header.startswith(b'II') or header.startswith(b'MM'), "Invalid TIFF header"

    def test_generate_granules_creates_metadata(self, temp_dir):
        """Test that generate_granules creates the metadata JSON sidecar."""
        collector = RemoteSensingCollector(output_dir=temp_dir)
        collector.generate_granules(household_ids=[1, 2, 3])
        
        metadata_path = Path(temp_dir) / "synthetic_granules_metadata.json"
        assert metadata_path.exists()
        
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        
        assert "granules" in data
        assert len(data["granules"]) > 0
        
        # Check structure of first entry
        entry = data["granules"][0]
        assert "filename" in entry
        assert "cloud_cover" in entry
        assert "latitude" in entry
        assert "longitude" in entry
        assert "ndvi_mean" in entry

    def test_generate_granules_with_survey_data(self, temp_dir):
        """Test generation using survey data coordinates."""
        # Create a dummy survey CSV
        survey_path = Path(temp_dir) / "survey.csv"
        with open(survey_path, 'w') as f:
            f.write("household_id,latitude,longitude\n")
            f.write("1,10.0,20.0\n")
            f.write("2,11.0,21.0\n")
        
        collector = RemoteSensingCollector(output_dir=temp_dir)
        collector.generate_granules(survey_data_path=survey_path)
        
        metadata_path = Path(temp_dir) / "synthetic_granules_metadata.json"
        assert metadata_path.exists()
        
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        
        # Should have processed the 2 rows from survey
        assert len(data["granules"]) == 2
        
        # Check that coordinates match (approximately)
        lats = [g["latitude"] for g in data["granules"]]
        assert 10.0 in lats or 11.0 in lats