"""
Unit tests for the spatial_join module.
"""
import pytest
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
import tempfile
import os

from src.data.processing.spatial_join import (
    load_survey_data,
    verify_linkage_and_trigger_aggregation,
    DEFAULT_BUFFER_METERS
)
from src.utils.io_helpers import FatalError

class TestLoadSurveyData:
    def test_load_valid_survey(self, tmp_path):
        """Test loading a valid survey CSV."""
        survey_file = tmp_path / "survey.csv"
        data = {
            'household_id': [1, 2, 3],
            'latitude': [10.0, 11.0, 12.0],
            'longitude': [20.0, 21.0, 22.0],
            'village_id': ['A', 'B', 'C']
        }
        pd.DataFrame(data).to_csv(survey_file, index=False)
        
        gdf = load_survey_data(survey_file)
        
        assert len(gdf) == 3
        assert 'geometry' in gdf.columns
        assert gdf.crs == "EPSG:4326"
        assert list(gdf['household_id']) == [1, 2, 3]

    def test_load_survey_missing_columns(self, tmp_path):
        """Test that missing columns raise an error."""
        survey_file = tmp_path / "survey.csv"
        data = {
            'household_id': [1, 2],
            'latitude': [10.0, 11.0]
            # Missing 'longitude'
        }
        pd.DataFrame(data).to_csv(survey_file, index=False)
        
        with pytest.raises(FatalError):
            load_survey_data(survey_file)

    def test_load_survey_invalid_coords(self, tmp_path):
        """Test handling of rows with missing coordinates."""
        survey_file = tmp_path / "survey.csv"
        data = {
            'household_id': [1, 2, 3],
            'latitude': [10.0, np.nan, 12.0],
            'longitude': [20.0, 21.0, np.nan]
        }
        pd.DataFrame(data).to_csv(survey_file, index=False)
        
        gdf = load_survey_data(survey_file)
        
        # Should drop rows with NaN coordinates
        assert len(gdf) == 1
        assert gdf.iloc[0]['household_id'] == 1

class TestVerifyLinkageAndTriggerAggregation:
    def test_linkage_passes(self):
        """Test when linkage rate and sample size are sufficient."""
        df_matched = pd.DataFrame({'household_id': range(350)})
        total = 400
        
        should_agg, reason = verify_linkage_and_trigger_aggregation(
            df_matched, total, min_linkage_rate=0.95, min_sample_size=300
        )
        
        assert should_agg is False
        assert reason is None

    def test_linkage_fails_low_rate(self):
        """Test when linkage rate is below threshold."""
        df_matched = pd.DataFrame({'household_id': range(300)}) # 300/400 = 75%
        total = 400
        
        should_agg, reason = verify_linkage_and_trigger_aggregation(
            df_matched, total, min_linkage_rate=0.95, min_sample_size=300
        )
        
        assert should_agg is True
        assert "Linkage rate" in str(reason)

    def test_linkage_fails_low_sample(self):
        """Test when sample size is below threshold despite high rate."""
        df_matched = pd.DataFrame({'household_id': range(200)}) # 200/250 = 80% (fails both)
        total = 250
        
        should_agg, reason = verify_linkage_and_trigger_aggregation(
            df_matched, total, min_linkage_rate=0.95, min_sample_size=300
        )
        
        assert should_agg is True
        assert reason is not None

    def test_edge_case_exact_threshold(self):
        """Test when linkage is exactly at threshold."""
        # 95% of 1000 is 950
        df_matched = pd.DataFrame({'household_id': range(950)})
        total = 1000
        
        should_agg, reason = verify_linkage_and_trigger_aggregation(
            df_matched, total, min_linkage_rate=0.95, min_sample_size=300
        )
        
        assert should_agg is False

    def test_edge_case_exact_sample_size(self):
        """Test when sample size is exactly at threshold."""
        df_matched = pd.DataFrame({'household_id': range(300)})
        total = 300 # 100% rate
        
        should_agg, reason = verify_linkage_and_trigger_aggregation(
            df_matched, total, min_linkage_rate=0.95, min_sample_size=300
        )
        
        assert should_agg is False