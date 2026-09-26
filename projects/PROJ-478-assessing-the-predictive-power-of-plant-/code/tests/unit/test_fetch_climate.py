"""
Unit tests for climate data fetching and processing.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock

from src.data.fetch_climate import (
    get_convex_hull_bbox,
    extract_raster_values,
    process_climate_data
)

@pytest.fixture
def sample_occurrences():
    """Sample occurrence data."""
    return pd.DataFrame({
        'species': ['Test'] * 5,
        'decimalLatitude': [34.0, 34.1, 34.2, 34.3, 34.4],
        'decimalLongitude': [-118.0, -118.1, -118.2, -118.3, -118.4],
        'eventDate': ['2020-01-01'] * 5
    })

@pytest.fixture
def sample_occurrences_with_nan():
    """Sample data with NaN coordinates."""
    return pd.DataFrame({
        'species': ['Test'] * 5,
        'decimalLatitude': [34.0, np.nan, 34.2, 34.3, 34.4],
        'decimalLongitude': [-118.0, -118.1, np.nan, -118.3, -118.4],
        'eventDate': ['2020-01-01'] * 5
    })

@pytest.fixture
def empty_occurrences():
    """Empty DataFrame."""
    return pd.DataFrame(columns=['species', 'decimalLatitude', 'decimalLongitude'])

@pytest.fixture
def single_point_occurrences():
    """Single point."""
    return pd.DataFrame({
        'species': ['Test'],
        'decimalLatitude': [34.0],
        'decimalLongitude': [-118.0],
        'eventDate': ['2020-01-01']
    })

class TestConvexHullBBox:
    def test_basic_bbox(self, sample_occurrences):
        """Test bounding box calculation."""
        bbox = get_convex_hull_bbox(sample_occurrences)
        assert len(bbox) == 4
        minx, miny, maxx, maxy = bbox
        assert minx < maxx
        assert miny < maxy
        # Check that bbox includes all points
        assert minx <= sample_occurrences['decimalLongitude'].min()
        assert maxx >= sample_occurrences['decimalLongitude'].max()
        assert miny <= sample_occurrences['decimalLatitude'].min()
        assert maxy >= sample_occurrences['decimalLatitude'].max()

    def test_single_point_bbox(self, single_point_occurrences):
        """Test bbox with single point."""
        bbox = get_convex_hull_bbox(single_point_occurrences)
        assert len(bbox) == 4
        # Should have some buffer around the point
        assert bbox[0] < single_point_occurrences['decimalLongitude'].iloc[0]
        assert bbox[2] > single_point_occurrences['decimalLongitude'].iloc[0]

    def test_empty_bbox_raises(self, empty_occurrences):
        """Test that empty DataFrame raises error."""
        with pytest.raises(ValueError, match="empty DataFrame"):
            get_convex_hull_bbox(empty_occurrences)

class TestExtractRasterValues:
    @patch('rasterio.open')
    def test_extract_raster_values(self, mock_rasterio, sample_occurrences, tmp_path):
        """Test raster value extraction."""
        # Create a mock raster
        mock_src = MagicMock()
        mock_src.sample.return_value = iter([[1.0]])
        mock_rasterio.return_value.__enter__.return_value = mock_src
        
        # Create dummy raster file
        raster_file = tmp_path / "test.tif"
        raster_file.write_text("dummy")
        
        result = extract_raster_values(
            sample_occurrences,
            [raster_file],
            ['bio1']
        )
        
        assert 'bio1' in result.columns
        assert len(result) == len(sample_occurrences)

class TestProcessClimateData:
    def test_process_climate_data_structure(self, sample_occurrences, tmp_path):
        """Test the overall structure of climate processing."""
        # Mock the download and extraction functions
        with patch('src.data.fetch_climate.download_worldclim_raster') as mock_download:
            mock_download.return_value = tmp_path / "bio1.tif"
            
            with patch('src.data.fetch_climate.extract_raster_values') as mock_extract:
                mock_extract.return_value = sample_occurrences.copy()
                mock_extract.return_value['bio1'] = 1.0
                
                result = process_climate_data(
                    sample_occurrences,
                    output_dir=tmp_path,
                    variables=['bio1']
                )
                
                assert 'bio1' in result.columns
                assert len(result) == len(sample_occurrences)

class TestIntegration:
    def test_full_pipeline_mocked(self, sample_occurrences, tmp_path):
        """Test the full pipeline with mocked dependencies."""
        with patch('src.data.fetch_climate.get_convex_hull_bbox') as mock_bbox:
            mock_bbox.return_value = (-119, 33, -117, 35)
            
            with patch('src.data.fetch_climate.download_worldclim_raster') as mock_download:
                mock_download.return_value = tmp_path / "bio1.tif"
                
                with patch('src.data.fetch_climate.extract_raster_values') as mock_extract:
                    mock_df = sample_occurrences.copy()
                    mock_df['bio1'] = np.random.rand(len(mock_df))
                    mock_extract.return_value = mock_df
                    
                    result = process_climate_data(
                        sample_occurrences,
                        output_dir=tmp_path,
                        variables=['bio1']
                    )
                    
                    assert result is not None
                    assert 'bio1' in result.columns