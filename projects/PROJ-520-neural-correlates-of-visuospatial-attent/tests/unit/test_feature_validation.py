"""
Unit tests for feature validation logic (T022).
"""

import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np

from code.feature_validation import (
    load_features,
    check_nan_inf_ratio,
    check_physiological_bounds,
    validate_features,
    PHYSIOLOGICAL_BOUNDS
)

class TestLoadFeatures:
    def test_load_valid_csv(self, tmp_path):
        csv_path = tmp_path / "test_features.csv"
        df = pd.DataFrame({"alpha_Pz": [10.0, 11.0], "beta_F3": [5.0, 6.0]})
        df.to_csv(csv_path, index=False)
        
        loaded = load_features(str(csv_path))
        assert loaded.shape == df.shape
        assert list(loaded.columns) == list(df.columns)

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_features(str(tmp_path / "nonexistent.csv"))

    def test_load_empty_csv(self, tmp_path):
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("col1,col2\n")
        
        with pytest.raises(ValueError, match="Features file is empty"):
            load_features(str(csv_path))

class TestCheckNaNInfRatio:
    def test_clean_data(self):
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
        valid, details = check_nan_inf_ratio(df, threshold=0.1)
        assert valid is True
        assert details["invalid_count"] == 0

    def test_high_nan_ratio(self):
        df = pd.DataFrame({"a": [1.0, np.nan, np.nan], "b": [4.0, 5.0, 6.0]})
        # 2 NaN out of 6 cells = 0.33 ratio
        valid, details = check_nan_inf_ratio(df, threshold=0.1)
        assert valid is False
        assert details["invalid_ratio"] > 0.1

    def test_inf_values(self):
        df = pd.DataFrame({"a": [1.0, np.inf, 3.0], "b": [4.0, 5.0, 6.0]})
        valid, details = check_nan_inf_ratio(df, threshold=0.1)
        assert valid is False
        assert details["inf_count"] > 0

class TestCheckPhysiologicalBounds:
    def test_values_within_bounds(self):
        # Create columns with 'alpha' and 'beta' in name
        df = pd.DataFrame({
            "alpha_power_Pz": [10.0, 15.0],
            "beta_power_F3": [5.0, 8.0]
        })
        valid, details = check_physiological_bounds(df, PHYSIOLOGICAL_BOUNDS)
        assert valid is True
        assert len(details["issues"]) == 0

    def test_values_out_of_bounds(self):
        # Value 100 is > max of 50 for alpha
        df = pd.DataFrame({
            "alpha_power_Pz": [10.0, 100.0], 
            "beta_power_F3": [5.0, 8.0]
        })
        valid, details = check_physiological_bounds(df, PHYSIOLOGICAL_BOUNDS)
        assert valid is False
        assert len(details["issues"]) == 1
        assert details["issues"][0]["column"] == "alpha_power_Pz"

    def test_mixed_band_columns(self):
        df = pd.DataFrame({
            "alpha_P3": [10.0, 12.0],
            "beta_F4": [5.0, 6.0],
            "other_col": [1.0, 2.0]  # Should be ignored by band logic
        })
        valid, details = check_physiological_bounds(df, PHYSIOLOGICAL_BOUNDS)
        # Should pass if alpha/beta are fine
        assert valid is True

class TestValidateFeatures:
    def test_full_validation_pass(self, tmp_path):
        csv_path = tmp_path / "valid_features.csv"
        log_path = tmp_path / "report.json"
        
        df = pd.DataFrame({
            "alpha_Pz": [10.0, 12.0, 11.0],
            "beta_F3": [5.0, 6.0, 5.5]
        })
        df.to_csv(csv_path, index=False)

        results = validate_features(str(csv_path), output_log_path=str(log_path))
        
        assert results["overall_valid"] is True
        assert os.path.exists(log_path)
        assert "checks" in results

    def test_full_validation_fail_nan(self, tmp_path):
        csv_path = tmp_path / "bad_features.csv"
        log_path = tmp_path / "report.json"
        
        # High NaN ratio
        df = pd.DataFrame({
            "alpha_Pz": [10.0, np.nan, np.nan],
            "beta_F3": [5.0, np.nan, np.nan]
        })
        df.to_csv(csv_path, index=False)

        results = validate_features(str(csv_path), output_log_path=str(log_path))
        
        assert results["overall_valid"] is False
        assert "nan_inf_ratio" in results["checks"]
        assert results["checks"]["nan_inf_ratio"]["valid"] is False

    def test_full_validation_fail_bounds(self, tmp_path):
        csv_path = tmp_path / "bad_bounds.csv"
        log_path = tmp_path / "report.json"
        
        df = pd.DataFrame({
            "alpha_Pz": [10.0, 200.0], # 200 is out of bounds
            "beta_F3": [5.0, 6.0]
        })
        df.to_csv(csv_path, index=False)

        results = validate_features(str(csv_path), output_log_path=str(log_path))
        
        assert results["overall_valid"] is False
        assert "physiological_bounds" in results["checks"]
        assert results["checks"]["physiological_bounds"]["valid"] is False
        assert "failure_reasons" in results