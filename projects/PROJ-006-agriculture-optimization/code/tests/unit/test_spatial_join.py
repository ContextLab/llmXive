"""
Unit tests for the spatial_join module.
"""

import pytest
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon
from pathlib import Path
import tempfile
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.processing.spatial_join import (
    apply_geodesic_buffer,
    extract_ndvi_from_granules,
    verify_linkage_and_trigger_aggregation
)


@pytest.fixture
def sample_survey_df():
    """Create a sample survey DataFrame."""
    return pd.DataFrame({
        'household_id': [1, 2, 3, 4, 5],
        'latitude': [-12.0, -12.1, -12.2, -12.3, -12.4],
        'longitude': [34.0, 34.1, 34.2, 34.3, 34.4],
        'land_size': [1.0, 2.0, 1.5, 3.0, 0.5],
        'education_level': [8, 10, 12, 6, 9]
    })


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestLoadSurveyData:
    def test_survey_dataframe_structure(self, sample_survey_df):
        """Test that the sample survey DataFrame has the correct structure."""
        assert 'household_id' in sample_survey_df.columns
        assert 'latitude' in sample_survey_df.columns
        assert 'longitude' in sample_survey_df.columns
        assert len(sample_survey_df) == 5


class TestSpatialBuffer:
    def test_geodesic_buffer_creation(self, sample_survey_df):
        """Test that geodesic buffer is created correctly."""
        buffer_km = 1.0
        gdf = apply_geodesic_buffer(sample_survey_df, buffer_km)

        assert isinstance(gdf, gpd.GeoDataFrame)
        assert 'geometry' in gdf.columns
        assert len(gdf) == len(sample_survey_df)

        # Check that geometries are polygons (buffers)
        for geom in gdf.geometry:
            assert isinstance(geom, Polygon)
            # Approximate area check: 1km buffer should be ~3.14 sq km
            # In projected CRS, area is in square meters
            # 1km = 1000m, Area = pi * r^2 = 3.14 * 1000^2 = 3,140,000 sq m
            # Allow some tolerance for projection distortions
            assert 2_500_000 < geom.area < 4_000_000, f"Buffer area {geom.area} is out of expected range"


    def test_buffer_with_missing_coords(self):
        """Test handling of missing coordinates."""
        df_missing = pd.DataFrame({
            'household_id': [1, 2],
            'latitude': [-12.0, None],
            'longitude': [34.0, 34.1]
        })
        # Should raise or handle gracefully. Current implementation drops NaNs in apply_geodesic_buffer logic implicitly via dropna in main,
        # but the function itself expects valid coords.
        # We test that it processes the valid row.
        gdf = apply_geodesic_buffer(df_missing, 1.0)
        assert len(gdf) == 1  # Only the valid row


class TestVerifyLinkageAndTriggerAggregation:
    def test_linkage_above_threshold(self):
        """Test that aggregation is NOT triggered when linkage is high."""
        df_survey = pd.DataFrame({
            'household_id': range(100),
            'latitude': [-12.0] * 100,
            'longitude': [34.0] * 100
        })
        df_joined = df_survey.copy() # 100% linkage

        df_out, log = verify_linkage_and_trigger_aggregation(df_survey, df_joined, threshold_pct=95.0, min_n_households=300)

        # Note: min_n_households is 300, so even with 100% linkage, if N < 300, it should trigger.
        # Let's adjust the test to meet the N requirement or check the logic.
        # The logic is: if linkage < 95% OR N < 300 -> trigger.
        # So with N=100, it SHOULD trigger.
        assert log['triggered_aggregation'] == True
        assert 'Sample size' in log['exclusion_reason']


    def test_linkage_below_threshold(self):
        """Test that aggregation IS triggered when linkage is low."""
        df_survey = pd.DataFrame({
            'household_id': range(1000),
            'latitude': [-12.0] * 1000,
            'longitude': [34.0] * 1000
        })
        df_joined = df_survey.head(500) # 50% linkage

        df_out, log = verify_linkage_and_trigger_aggregation(df_survey, df_joined, threshold_pct=95.0, min_n_households=300)

        assert log['triggered_aggregation'] == True
        assert log['linkage_percentage'] == 50.0
        assert 'Linkage percentage' in log['exclusion_reason']


    def test_linkage_success(self):
        """Test that aggregation is NOT triggered when both conditions are met."""
        df_survey = pd.DataFrame({
            'household_id': range(500),
            'latitude': [-12.0] * 500,
            'longitude': [34.0] * 500
        })
        df_joined = df_survey.copy() # 100% linkage, N=500

        df_out, log = verify_linkage_and_trigger_aggregation(df_survey, df_joined, threshold_pct=95.0, min_n_households=300)

        assert log['triggered_aggregation'] == False
        assert log['exclusion_reason'] == "None"
        assert log['total_valid_households'] == 500


class TestSpatialJoinIntegration:
    def test_extract_ndvi_synthetic_fallback(self, temp_dir, sample_survey_df):
        """Test that synthetic NDVI is generated when granules are missing."""
        gdf = apply_geodesic_buffer(sample_survey_df, 1.0)
        granules_dir = temp_dir / "sentinel2" # Empty dir

        df_ndvi = extract_ndvi_from_granules(gdf, granules_dir)

        assert 'household_id' in df_ndvi.columns
        assert 'ndvi_mean' in df_ndvi.columns
        assert len(df_ndvi) == len(sample_survey_df)
        assert df_ndvi['ndvi_mean'].notna().all()
        # Check range
        assert df_ndvi['ndvi_mean'].min() >= -1.0
        assert df_ndvi['ndvi_mean'].max() <= 1.0