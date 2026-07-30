import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingest import normalize_time_to_minutes, load_data, filter_missing_target, validate_physical_bounds, impute_missing_composition, clip_outliers

class TestNormalizeTimeToMinutes:
    def test_normalize_hours_to_minutes(self):
        """Test that hours are correctly converted to minutes."""
        data = {
            "time_to_peak": [1.0, 2.0, 3.0],
            "unit": ["hour", "hour", "hour"]
        }
        df = pd.DataFrame(data)
        
        result_df, logs = normalize_time_to_minutes(df)
        
        assert result_df["time_to_peak"].iloc[0] == 60.0
        assert result_df["time_to_peak"].iloc[1] == 120.0
        assert result_df["time_to_peak"].iloc[2] == 180.0
        assert "unit" not in result_df.columns
        assert len(logs) > 0
        assert logs[0]["type"] == "unit_conversion"

    def test_normalize_minutes_no_change(self):
        """Test that minutes remain unchanged."""
        data = {
            "time_to_peak": [10.0, 20.0, 30.0],
            "unit": ["minute", "minute", "minute"]
        }
        df = pd.DataFrame(data)
        
        result_df, logs = normalize_time_to_minutes(df)
        
        assert result_df["time_to_peak"].iloc[0] == 10.0
        assert result_df["time_to_peak"].iloc[1] == 20.0
        assert result_df["time_to_peak"].iloc[2] == 30.0
        assert "unit" not in result_df.columns

    def test_normalize_no_unit_column(self):
        """Test behavior when no unit column exists (assume minutes)."""
        data = {
            "time_to_peak": [10.0, 20.0, 30.0]
        }
        df = pd.DataFrame(data)
        
        result_df, logs = normalize_time_to_minutes(df)
        
        assert result_df["time_to_peak"].iloc[0] == 10.0
        assert logs[0]["type"] == "unit_assumed"

    def test_normalize_handles_mixed_units(self):
        """Test mixed hours and minutes."""
        data = {
            "time_to_peak": [1.0, 60.0, 2.0],
            "unit": ["hour", "minute", "hour"]
        }
        df = pd.DataFrame(data)
        
        result_df, logs = normalize_time_to_minutes(df)
        
        assert result_df["time_to_peak"].iloc[0] == 60.0
        assert result_df["time_to_peak"].iloc[1] == 60.0
        assert result_df["time_to_peak"].iloc[2] == 120.0
        assert "unit" not in result_df.columns

class TestFilterMissingTarget:
    def test_filter_missing(self):
        data = {
            "time_to_peak": [10.0, np.nan, 30.0, np.nan],
            "cold_work": [10, 20, 30, 40]
        }
        df = pd.DataFrame(data)
        result = filter_missing_target(df)
        assert len(result) == 2
        assert result["time_to_peak"].isna().sum() == 0

class TestValidatePhysicalBounds:
    def test_invalid_cold_work(self):
        data = {
            "time_to_peak": [10.0, 20.0, 30.0],
            "cold_work": [-5, 50, 105]
        }
        df = pd.DataFrame(data)
        result, logs = validate_physical_bounds(df)
        assert len(result) == 1
        assert result["cold_work"].iloc[0] == 50
        assert len(logs) > 0

    def test_invalid_time(self):
        data = {
            "time_to_peak": [-10, 20, 0],
            "cold_work": [10, 20, 30]
        }
        df = pd.DataFrame(data)
        result, logs = validate_physical_bounds(df)
        assert len(result) == 1
        assert result["time_to_peak"].iloc[0] == 20

class TestImputeMissingComposition:
    def test_impute_by_global_mean(self):
        data = {
            "Mn_content": [1.0, np.nan, 3.0],
            "Mg_content": [0.5, 0.6, 0.7]
        }
        df = pd.DataFrame(data)
        result, logs = impute_missing_composition(df)
        assert not result["Mn_content"].isna().any()
        assert result["Mn_content"].iloc[1] == 2.0 # Mean of 1 and 3

class TestClipOutliers:
    def test_clip_outliers(self):
        # Create data with an extreme outlier
        data = {
            "time_to_peak": [10, 12, 11, 13, 1000] # 1000 is outlier
        }
        df = pd.DataFrame(data)
        result, logs = clip_outliers(df, column="time_to_peak", percentile=90)
        # 90th percentile of [10,11,12,13,1000] is 13 (approx)
        # The outlier 1000 should be clipped to ~13
        assert result["time_to_peak"].max() < 1000
        assert len(logs) > 0
        assert logs[0]["type"] == "outlier_clipped"