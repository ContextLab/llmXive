"""
Unit tests for scale scoring logic.
Verifies that scoring logic matches the definitions in config/scales.yaml.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.scales import load_scale_config, score_cesd, score_gad7, score_pcl5, apply_scale_scoring
from utils.logger import get_logger

logger = get_logger(__name__)

# Path to the scales configuration file
CONFIG_PATH = project_root / "code" / "config" / "scales.yaml"

class TestScaleConfig:
    """Tests for scale configuration loading."""

    def test_scale_config_exists(self):
        """Test that the scales.yaml configuration file exists."""
        assert CONFIG_PATH.exists(), f"Configuration file not found at {CONFIG_PATH}"

    def test_scale_config_valid_yaml(self):
        """Test that the scales.yaml file is valid YAML and contains expected keys."""
        config = load_scale_config(CONFIG_PATH)
        assert isinstance(config, dict), "Configuration must be a dictionary"
        assert "CES-D" in config, "Configuration must contain CES-D key"
        assert "GAD-7" in config, "Configuration must contain GAD-7 key"
        # PCL-5 is optional per spec (W-PCL5-MISSING)
        assert "variable" in config["CES-D"], "CES-D config must have 'variable' key"
        assert "type" in config["CES-D"], "CES-D config must have 'type' key"
        assert config["CES-D"]["variable"] == "depression", "CES-D variable must map to 'depression'"
        assert config["CES-D"]["type"] == "aggregate_score", "CES-D type must be 'aggregate_score'"

    def test_scale_config_variables_match_spec(self):
        """Test that scale variables match the spec's Data Dictionary."""
        config = load_scale_config(CONFIG_PATH)
        expected_mappings = {
            "CES-D": "depression",
            "GAD-7": "anxiety"
        }
        for scale_name, expected_var in expected_mappings.items():
            assert scale_name in config, f"Missing scale: {scale_name}"
            assert config[scale_name]["variable"] == expected_var, \
                f"Scale {scale_name} variable '{config[scale_name]['variable']}' does not match spec '{expected_var}'"

class TestScaleScoring:
    """Tests for individual scale scoring functions."""

    def test_score_cesd_aggregate(self):
        """Test CES-D scoring with aggregate score input."""
        config = load_scale_config(CONFIG_PATH)
        # Create mock data where 'depression' is already an aggregate score
        data = pd.DataFrame({
            "depression": [10.0, 20.0, 30.0],
            "id": [1, 2, 3]
        })
        result = score_cesd(data, config)
        assert "depression_score" in result.columns, "Result must contain 'depression_score' column"
        # Verify values are passed through (since it's already aggregate)
        pd.testing.assert_series_equal(result["depression_score"], data["depression"])

    def test_score_gad7_aggregate(self):
        """Test GAD-7 scoring with aggregate score input."""
        config = load_scale_config(CONFIG_PATH)
        data = pd.DataFrame({
            "anxiety": [5.0, 10.0, 15.0],
            "id": [1, 2, 3]
        })
        result = score_gad7(data, config)
        assert "anxiety_score" in result.columns, "Result must contain 'anxiety_score' column"
        pd.testing.assert_series_equal(result["anxiety_score"], data["anxiety"])

    def test_score_pcl5_missing_columns(self):
        """Test PCL-5 scoring when columns are missing (should handle gracefully)."""
        config = load_scale_config(CONFIG_PATH)
        data = pd.DataFrame({
            "id": [1, 2, 3]
            # No PCL-5 columns present
        })
        # Should not raise an error, just return data unchanged or with warning
        result = score_pcl5(data, config)
        assert "id" in result.columns, "Result must preserve original columns"

    def test_score_pcl5_aggregate(self):
        """Test PCL-5 scoring with aggregate score input."""
        config = load_scale_config(CONFIG_PATH)
        data = pd.DataFrame({
            "ptsd": [25.0, 50.0, 75.0],
            "id": [1, 2, 3]
        })
        result = score_pcl5(data, config)
        assert "ptsd_score" in result.columns, "Result must contain 'ptsd_score' column"
        pd.testing.assert_series_equal(result["ptsd_score"], data["ptsd"])

    def test_apply_scale_scoring_full_pipeline(self):
        """Test the full scale scoring pipeline with multiple scales."""
        config = load_scale_config(CONFIG_PATH)
        data = pd.DataFrame({
            "depression": [15.0, 25.0, 35.0],
            "anxiety": [8.0, 12.0, 18.0],
            "ptsd": [30.0, 45.0, 60.0],
            "id": [1, 2, 3]
        })
        result = apply_scale_scoring(data, config)
        
        # Verify all expected score columns exist
        expected_scores = ["depression_score", "anxiety_score", "ptsd_score"]
        for col in expected_scores:
            assert col in result.columns, f"Missing score column: {col}"

        # Verify values are correct (aggregate scores pass through)
        pd.testing.assert_series_equal(result["depression_score"], data["depression"])
        pd.testing.assert_series_equal(result["anxiety_score"], data["anxiety"])
        pd.testing.assert_series_equal(result["ptsd_score"], data["ptsd"])

    def test_apply_scale_scoring_partial_data(self):
        """Test scale scoring when some scales are missing from data."""
        config = load_scale_config(CONFIG_PATH)
        # Data without PTSD column
        data = pd.DataFrame({
            "depression": [15.0, 25.0],
            "anxiety": [8.0, 12.0],
            "id": [1, 2]
        })
        result = apply_scale_scoring(data, config)
        
        # Should have depression and anxiety scores, but not PTSD
        assert "depression_score" in result.columns
        assert "anxiety_score" in result.columns
        # PCL-5 handling depends on implementation; if it's missing from data,
        # the function should handle it gracefully (either skip or warn)
        if "ptsd_score" in result.columns:
            assert result["ptsd_score"].isna().all(), "Missing PCL-5 data should result in NaN scores"

    def test_scale_scoring_with_nulls(self):
        """Test that scale scoring handles null values correctly."""
        config = load_scale_config(CONFIG_PATH)
        data = pd.DataFrame({
            "depression": [15.0, np.nan, 35.0],
            "anxiety": [8.0, 12.0, np.nan],
            "id": [1, 2, 3]
        })
        result = apply_scale_scoring(data, config)
        
        # Nulls should be preserved as NaN in the output
        assert pd.isna(result.loc[1, "depression_score"])
        assert pd.isna(result.loc[2, "anxiety_score"])

    def test_scale_scoring_invalid_input_type(self):
        """Test that scale scoring raises error for invalid input type."""
        config = load_scale_config(CONFIG_PATH)
        with pytest.raises((TypeError, AttributeError)):
            apply_scale_scoring("not a dataframe", config)

    def test_scale_scoring_missing_required_columns(self):
        """Test that scale scoring handles missing required columns gracefully."""
        config = load_scale_config(CONFIG_PATH)
        data = pd.DataFrame({
            "id": [1, 2, 3]
            # Missing all required score columns
        })
        # Should not crash, but return empty scores or handle gracefully
        result = apply_scale_scoring(data, config)
        assert "id" in result.columns