"""
Unit tests for the spatial join module (T017).
"""

import pytest
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon
from pathlib import Path
import tempfile
import os

from src.data.processing.spatial_join import SpatialJoinProcessor
from src.utils.io_helpers import FatalError, IntegrityError


class TestLoadSurveyData:
    """Tests for loading survey data."""

    def test_load_survey_data_success(self, tmp_path):
        """Test successful loading of survey data."""
        # Create a sample survey CSV
        survey_data = {
            'household_id': [1, 2, 3],
            'latitude': [-12.3, -12.4, -12.5],
            'longitude': [34.5, 34.6, 34.7],
            'other_field': ['a', 'b', 'c']
        }
        survey_df = pd.DataFrame(survey_data)
        survey_path = tmp_path / "survey.csv"
        survey_df.to_csv(survey_path, index=False)

        # Initialize processor
        processor = SpatialJoinProcessor(
            survey_data_path=survey_path,
            output_path=tmp_path / "output.csv"
        )

        # Load data
        gdf = processor.load_survey_data()

        # Assertions
        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) == 3
        assert 'geometry' in gdf.columns
        assert all(gdf['household_id'] == [1, 2, 3])

    def test_load_survey_data_missing_file(self, tmp_path):
        """Test error when survey file is missing."""
        processor = SpatialJoinProcessor(
            survey_data_path=tmp_path / "nonexistent.csv",
            output_path=tmp_path / "output.csv"
        )

        with pytest.raises(FatalError):
            processor.load_survey_data()

    def test_load_survey_data_missing_columns(self, tmp_path):
        """Test error when required columns are missing."""
        survey_data = {
            'household_id': [1, 2],
            'latitude': [-12.3, -12.4]
            # Missing 'longitude'
        }
        survey_df = pd.DataFrame(survey_data)
        survey_path = tmp_path / "survey.csv"
        survey_df.to_csv(survey_path, index=False)

        processor = SpatialJoinProcessor(
            survey_data_path=survey_path,
            output_path=tmp_path / "output.csv"
        )

        with pytest.raises(IntegrityError):
            processor.load_survey_data()


class TestVerifyLinkageAndTriggerAggregation:
    """Tests for linkage verification and aggregation triggering."""

    def test_linkage_above_threshold(self, tmp_path):
        """Test when linkage rate is above threshold."""
        # Create a DataFrame with high linkage
        data = {
            'household_id': [1, 2, 3, 4, 5],
            'pixel_id': [10, 11, 12, 13, 14],  # All linked
            'ndvi_mean': [0.5, 0.6, 0.7, 0.8, 0.9]
        }
        df = pd.DataFrame(data)

        processor = SpatialJoinProcessor(
            survey_data_path=tmp_path / "survey.csv",
            output_path=tmp_path / "output.csv",
            min_linkage_threshold=0.95,
            min_sample_size=300
        )

        # Manually set total count for testing
        total_count = len(df)
        linked_count = df['pixel_id'].notna().sum()
        linkage_rate = linked_count / total_count

        result_df, aggregation_triggered = processor.verify_linkage_and_trigger_aggregation(
            df, linkage_rate
        )

        assert aggregation_triggered is False
        assert all(result_df['needs_aggregation'] == False)

    def test_linkage_below_threshold(self, tmp_path):
        """Test when linkage rate is below threshold."""
        # Create a DataFrame with low linkage
        data = {
            'household_id': [1, 2, 3, 4, 5],
            'pixel_id': [10, 11, None, None, None],  # Only 2/5 linked (40%)
            'ndvi_mean': [0.5, 0.6, np.nan, np.nan, np.nan]
        }
        df = pd.DataFrame(data)

        processor = SpatialJoinProcessor(
            survey_data_path=tmp_path / "survey.csv",
            output_path=tmp_path / "output.csv",
            min_linkage_threshold=0.95,
            min_sample_size=300
        )

        total_count = len(df)
        linked_count = df['pixel_id'].notna().sum()
        linkage_rate = linked_count / total_count

        result_df, aggregation_triggered = processor.verify_linkage_and_trigger_aggregation(
            df, linkage_rate
        )

        assert aggregation_triggered is True
        # Check that needs_aggregation is set correctly
        assert result_df.loc[0, 'needs_aggregation'] == False  # Linked
        assert result_df.loc[2, 'needs_aggregation'] == True   # Not linked

    def test_sample_size_below_minimum(self, tmp_path):
        """Test when sample size is below minimum."""
        # Create a DataFrame with high linkage but low N
        data = {
            'household_id': [1, 2],
            'pixel_id': [10, 11],
            'ndvi_mean': [0.5, 0.6]
        }
        df = pd.DataFrame(data)

        processor = SpatialJoinProcessor(
            survey_data_path=tmp_path / "survey.csv",
            output_path=tmp_path / "output.csv",
            min_linkage_threshold=0.95,
            min_sample_size=300
        )

        total_count = len(df)
        linked_count = df['pixel_id'].notna().sum()
        linkage_rate = linked_count / total_count

        result_df, aggregation_triggered = processor.verify_linkage_and_trigger_aggregation(
            df, linkage_rate
        )

        assert aggregation_triggered is True  # N < 300 triggers aggregation
        assert all(result_df['needs_aggregation'] == False)  # But all are linked

    def test_zero_linkage(self, tmp_path):
        """Test when no households are linked."""
        data = {
            'household_id': [1, 2, 3],
            'pixel_id': [None, None, None],
            'ndvi_mean': [np.nan, np.nan, np.nan]
        }
        df = pd.DataFrame(data)

        processor = SpatialJoinProcessor(
            survey_data_path=tmp_path / "survey.csv",
            output_path=tmp_path / "output.csv",
            min_linkage_threshold=0.95,
            min_sample_size=300
        )

        result_df, aggregation_triggered = processor.verify_linkage_and_trigger_aggregation(
            df, 0.0
        )

        assert aggregation_triggered is True
        assert all(result_df['needs_aggregation'] == True)


class TestSpatialBuffer:
    """Tests for spatial buffering logic."""

    def test_buffer_application(self, tmp_path):
        """Test that buffering is applied correctly."""
        # Create a sample GeoDataFrame
        data = {
            'household_id': [1, 2],
            'latitude': [-12.3, -12.4],
            'longitude': [34.5, 34.6]
        }
        df = pd.DataFrame(data)
        geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

        processor = SpatialJoinProcessor(
            survey_data_path=tmp_path / "survey.csv",
            output_path=tmp_path / "output.csv",
            buffer_meters=1000  # 1km buffer
        )

        buffered_gdf = processor.apply_spatial_buffer(gdf)

        # Check that geometry changed from Point to Polygon
        assert all(buffered_gdf.geometry.geom_type == 'Polygon')

        # Check that the area is reasonable (approx pi * r^2)
        # 1000m buffer -> area ~ 3.14 km^2
        areas = buffered_gdf.geometry.to_crs("EPSG:6933").area  # Use equal area projection for measurement
        assert all(areas > 2000000)  # > 2 km^2 in m^2
        assert all(areas < 5000000)  # < 5 km^2 (allowing for projection distortions)


class TestSpatialJoinIntegration:
    """Integration tests for the full spatial join process."""

    def test_full_pipeline(self, tmp_path):
        """Test the full spatial join pipeline with mock data."""
        # Create mock survey data
        survey_data = {
            'household_id': [1, 2, 3],
            'latitude': [-12.3, -12.4, -12.5],
            'longitude': [34.5, 34.6, 34.7],
            'village_id': ['V1', 'V1', 'V2']
        }
        survey_df = pd.DataFrame(survey_data)
        survey_path = tmp_path / "survey.csv"
        survey_df.to_csv(survey_path, index=False)

        # Create mock remote sensing data
        rs_data = {
            'pixel_id': [10, 11, 12],
            'latitude': [-12.31, -12.41, -12.51],
            'longitude': [34.51, 34.61, 34.71],
            'ndvi_mean': [0.5, 0.6, 0.7],
            'cloud_cover': [0.1, 0.2, 0.3]
        }
        rs_df = pd.DataFrame(rs_data)
        rs_path = tmp_path / "rs.csv"
        rs_df.to_csv(rs_path, index=False)

        output_path = tmp_path / "output.csv"

        processor = SpatialJoinProcessor(
            survey_data_path=survey_path,
            remote_sensing_data_path=rs_path,
            output_path=output_path,
            buffer_meters=5000,  # 5km buffer to ensure overlap
            min_linkage_threshold=0.5,
            min_sample_size=1
        )

        result = processor.process()

        # Verify output
        assert result is not None
        assert len(result) == 3
        assert 'pixel_id' in result.columns
        assert 'ndvi_mean' in result.columns
        assert output_path.exists()

        # Verify linkage
        linked_count = result['pixel_id'].notna().sum()
        assert linked_count == 3  # All should be linked with 5km buffer
        assert result['needs_aggregation'].sum() == 0

    def test_pipeline_no_remote_sensing(self, tmp_path):
        """Test pipeline when remote sensing data is missing."""
        survey_data = {
            'household_id': [1, 2],
            'latitude': [-12.3, -12.4],
            'longitude': [34.5, 34.6]
        }
        survey_df = pd.DataFrame(survey_data)
        survey_path = tmp_path / "survey.csv"
        survey_df.to_csv(survey_path, index=False)

        output_path = tmp_path / "output.csv"

        processor = SpatialJoinProcessor(
            survey_data_path=survey_path,
            remote_sensing_data_path=tmp_path / "nonexistent.csv",
            output_path=output_path
        )

        result = processor.process()

        assert result is not None
        assert len(result) == 2
        assert all(result['pixel_id'].isna())
        assert all(result['needs_aggregation'] == True)
        assert output_path.exists()