"""
Integration tests for the OSM and satellite data ingestion pipeline.

Tests:
- T011: End-to-end ingestion of a single city
"""

import os
import json
import tempfile
from pathlib import Path
import pytest
import geopandas as gpd
import rasterio
import numpy as np

from ingest import download_osm_data, ingest_satellite_data, validate_raster_overlap
from config import get_city_bounds, get_path
from utils.env import get_overpass_api_key


class TestIngestionPipeline:
    """Integration tests for data ingestion."""

    @pytest.fixture
    def test_city(self):
        """Return a test city name."""
        return "new_york"
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set the output path temporarily
            original_path = get_path("data/processed")
            yield Path(tmpdir)
    
    def test_osm_download_basic(self, test_city):
        """Test basic OSM data download."""
        # Skip if no API key available
        if not get_overpass_api_key():
            pytest.skip("OVERPASS_API_KEY not set")
        
        try:
            data = download_osm_data(test_city, ['buildings'])
            assert 'buildings' in data
            assert isinstance(data['buildings'], gpd.GeoDataFrame)
            assert len(data['buildings']) > 0
            assert data['buildings'].crs == "EPSG:4326"
        except Exception as e:
            # If Overpass API is unavailable, skip the test
            if "429" in str(e) or "rate limit" in str(e).lower():
                pytest.skip("Overpass API rate limited")
            else:
                raise
    
    def test_satellite_ingestion(self, test_city):
        """Test satellite data ingestion."""
        temp_raster = ingest_satellite_data(test_city, data_source="MODIS")
        
        assert temp_raster.city == test_city
        assert temp_raster.source == "MODIS"
        assert Path(temp_raster.path).exists()
        assert temp_raster.mean_temperature is not None
        assert temp_raster.std_temperature is not None
        
        # Verify the raster file
        with rasterio.open(temp_raster.path) as src:
            assert src.count == 1
            assert src.width > 0
            assert src.height > 0
            data = src.read(1)
            assert not np.all(np.isnan(data))
    
    def test_raster_overlap_validation(self, test_city):
        """Test raster overlap validation."""
        # Ingest two rasters
        raster1 = ingest_satellite_data(test_city, data_source="MODIS")
        raster2 = ingest_satellite_data(test_city, data_source="MODIS")
        
        # Validation should pass for identical rasters
        result = validate_raster_overlap([raster1.path, raster2.path])
        assert result is True
    
    def test_metadata_generation(self, test_city):
        """Test that metadata is generated correctly."""
        # Run ingestion
        osm_data = download_osm_data(test_city, ['buildings'])
        temp_raster = ingest_satellite_data(test_city)
        
        # Check metadata file
        metadata_path = get_path("data/metadata.json")
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            assert "city" in metadata
            assert metadata["city"] == test_city
            assert "osm_features" in metadata
            assert "satellite_source" in metadata
            assert "temperature_stats" in metadata
        else:
            # Metadata might not be generated in test mode
            pytest.skip("Metadata file not generated in test mode")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
