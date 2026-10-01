"""
Integration test for T017: Feature Aggregation.
Verifies that aggregate_features produces a DataFrame with exactly 30 columns
in the correct order and no NaN values.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from main import aggregate_features

class TestFeatureAggregation:
    
    def test_aggregate_features_column_count_and_order(self, tmp_path):
        """
        Test that aggregate_features produces exactly 30 columns 
        in the specified order.
        """
        # Create mock participant data that matches T016 output specification
        mock_data = {
            "sub-001": {
                # 4 Mean Durations
                "mean_duration_A": 120.5,
                "mean_duration_B": 110.2,
                "mean_duration_C": 95.8,
                "mean_duration_D": 105.1,
                # 4 Occurrence Rates
                "occurrence_rate_A": 0.25,
                "occurrence_rate_B": 0.28,
                "occurrence_rate_C": 0.22,
                "occurrence_rate_D": 0.25,
                # 16 Transition Probabilities (4x4 flattened)
                "trans_prob_A_A": 0.1, "trans_prob_A_B": 0.2, "trans_prob_A_C": 0.3, "trans_prob_A_D": 0.4,
                "trans_prob_B_A": 0.2, "trans_prob_B_B": 0.1, "trans_prob_B_C": 0.4, "trans_prob_B_D": 0.3,
                "trans_prob_C_A": 0.3, "trans_prob_C_B": 0.4, "trans_prob_C_C": 0.1, "trans_prob_C_D": 0.2,
                "trans_prob_D_A": 0.4, "trans_prob_D_B": 0.3, "trans_prob_D_C": 0.2, "trans_prob_D_D": 0.1,
                # 6 Spectral Power Features
                "spectral_power_delta": 10.5,
                "spectral_power_theta": 8.2,
                "spectral_power_alpha": 12.1,
                "spectral_power_beta": 6.5,
                "spectral_power_low_gamma": 3.2,
                "spectral_power_high_gamma": 1.8
            },
            "sub-002": {
                "mean_duration_A": 125.0,
                "mean_duration_B": 108.0,
                "mean_duration_C": 98.0,
                "mean_duration_D": 102.0,
                "occurrence_rate_A": 0.26,
                "occurrence_rate_B": 0.27,
                "occurrence_rate_C": 0.21,
                "occurrence_rate_D": 0.26,
                "trans_prob_A_A": 0.15, "trans_prob_A_B": 0.15, "trans_prob_A_C": 0.35, "trans_prob_A_D": 0.35,
                "trans_prob_B_A": 0.25, "trans_prob_B_B": 0.15, "trans_prob_B_C": 0.35, "trans_prob_B_D": 0.25,
                "trans_prob_C_A": 0.35, "trans_prob_C_B": 0.35, "trans_prob_C_C": 0.15, "trans_prob_C_D": 0.15,
                "trans_prob_D_A": 0.40, "trans_prob_D_B": 0.25, "trans_prob_D_C": 0.20, "trans_prob_D_D": 0.15,
                "spectral_power_delta": 11.0,
                "spectral_power_theta": 7.5,
                "spectral_power_alpha": 13.0,
                "spectral_power_beta": 6.0,
                "spectral_power_low_gamma": 3.5,
                "spectral_power_high_gamma": 2.0
            }
        }

        output_file = tmp_path / "feature_matrix.csv"
        
        # Execute aggregation
        df = aggregate_features(mock_data, output_file)

        # Verify column count
        feature_cols = [c for c in df.columns if c != "participant_id"]
        assert len(feature_cols) == 30, f"Expected 30 columns, got {len(feature_cols)}"

        # Verify column order
        expected_order = (
            ["mean_duration_A", "mean_duration_B", "mean_duration_C", "mean_duration_D"] +
            ["occurrence_rate_A", "occurrence_rate_B", "occurrence_rate_C", "occurrence_rate_D"] +
            [f"trans_prob_{f}_{t}" for f in ["A", "B", "C", "D"] for t in ["A", "B", "C", "D"]] +
            ["spectral_power_delta", "spectral_power_theta", "spectral_power_alpha", 
             "spectral_power_beta", "spectral_power_low_gamma", "spectral_power_high_gamma"]
        )
        
        assert list(feature_cols) == expected_order, (
            f"Column order mismatch.\nExpected: {expected_order}\nGot: {feature_cols}"
        )

        # Verify no NaN values
        assert df.isna().sum().sum() == 0, "DataFrame contains NaN values"

        # Verify file was written
        assert output_file.exists(), "Output CSV file was not created"

        # Verify content can be reloaded
        reloaded_df = pd.read_csv(output_file)
        assert reloaded_df.shape == df.shape, "Reloaded CSV shape mismatch"

    def test_aggregate_features_raises_on_wrong_column_count(self, tmp_path):
        """
        Test that aggregate_features raises AssertionError if column count != 30.
        """
        # Create data with missing column
        incomplete_data = {
            "sub-001": {
                "mean_duration_A": 100.0,
                # Missing all other columns
            }
        }
        
        output_file = tmp_path / "fail_matrix.csv"
        
        with pytest.raises(AssertionError) as exc_info:
            aggregate_features(incomplete_data, output_file)
        
        assert "exactly 30 columns" in str(exc_info.value)

    def test_aggregate_features_raises_on_nan(self, tmp_path):
        """
        Test that aggregate_features raises ValueError if NaN values are present.
        """
        nan_data = {
            "sub-001": {
                "mean_duration_A": np.nan,
                "mean_duration_B": 100.0,
                "mean_duration_C": 100.0,
                "mean_duration_D": 100.0,
                "occurrence_rate_A": 0.25,
                "occurrence_rate_B": 0.25,
                "occurrence_rate_C": 0.25,
                "occurrence_rate_D": 0.25,
                "trans_prob_A_A": 0.25, "trans_prob_A_B": 0.25, "trans_prob_A_C": 0.25, "trans_prob_A_D": 0.25,
                "trans_prob_B_A": 0.25, "trans_prob_B_B": 0.25, "trans_prob_B_C": 0.25, "trans_prob_B_D": 0.25,
                "trans_prob_C_A": 0.25, "trans_prob_C_B": 0.25, "trans_prob_C_C": 0.25, "trans_prob_C_D": 0.25,
                "trans_prob_D_A": 0.25, "trans_prob_D_B": 0.25, "trans_prob_D_C": 0.25, "trans_prob_D_D": 0.25,
                "spectral_power_delta": 10.0,
                "spectral_power_theta": 10.0,
                "spectral_power_alpha": 10.0,
                "spectral_power_beta": 10.0,
                "spectral_power_low_gamma": 10.0,
                "spectral_power_high_gamma": 10.0
            }
        }

        output_file = tmp_path / "nan_matrix.csv"
        
        with pytest.raises(ValueError) as exc_info:
            aggregate_features(nan_data, output_file)
        
        assert "NaN" in str(exc_info.value)
