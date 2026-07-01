import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.generate_synthetic_data import generate_synthetic_data


class TestSyntheticGenerator:
    """Unit tests for the synthetic data generator (T010)."""

    def test_ground_truth_correlation_injection(self):
        """
        Verify that the synthetic data has the expected ground-truth correlations:
        - Positive correlation between smoothness and agency_score
        - Negative correlation between latency and agency_score
        - Positive correlation between lead_time and agency_score
        """
        df = generate_synthetic_data(n_samples=500, seed=123)

        # Check smoothness-agency correlation (should be positive)
        smoothness_corr = df['smoothness'].corr(df['agency_score'])
        assert smoothness_corr > 0, f"Expected positive correlation between smoothness and agency, got {smoothness_corr}"

        # Check latency-agency correlation (should be negative)
        latency_corr = df['latency'].corr(df['agency_score'])
        assert latency_corr < 0, f"Expected negative correlation between latency and agency, got {latency_corr}"

        # Check lead_time-agency correlation (should be positive)
        lead_time_corr = df['lead_time'].corr(df['agency_score'])
        assert lead_time_corr > 0, f"Expected positive correlation between lead_time and agency, got {lead_time_corr}"

    def test_user_response_trigger_distinctness(self):
        """
        Verify that user_response_trigger is distinct from agency_score (FR-012).
        They should have low correlation (near zero).
        """
        df = generate_synthetic_data(n_samples=500, seed=456)

        # The user_response_trigger should be largely independent of agency_score
        trigger_corr = df['user_response_trigger'].corr(df['agency_score'])

        # Allow some small correlation due to noise, but it should be weak
        assert abs(trigger_corr) < 0.3, \
            f"User response trigger should be distinct from agency score, correlation: {trigger_corr}"

    def test_instrument_validation_logic(self):
        """
        Verify that the generated data meets basic instrument validation criteria:
        - All required columns are present
        - Values are within expected ranges
        - No NaN values in required columns
        """
        df = generate_synthetic_data(n_samples=100, seed=789)

        # Check required columns
        required_cols = ['participant_id', 'latency', 'smoothness', 'lead_time', 'agency_score']
        for col in required_cols:
            assert col in df.columns, f"Missing required column: {col}"

        # Check value ranges
        assert df['latency'].between(0, 500).all(), "Latency should be between 0 and 500"
        assert df['smoothness'].between(0, 1).all(), "Smoothness should be between 0 and 1"
        assert df['lead_time'].between(-100, 200).all(), "Lead time should be between -100 and 200"
        assert df['agency_score'].between(0, 100).all(), "Agency score should be between 0 and 100"

        # Check for NaN in required columns
        for col in required_cols:
            assert not df[col].isna().any(), f"NaN values found in required column: {col}"

    def test_sample_size_generation(self):
        """Verify that the generator produces the requested number of samples."""
        n_requested = 120
        df = generate_synthetic_data(n_samples=n_requested, seed=999)
        assert len(df) == n_requested, f"Expected {n_requested} samples, got {len(df)}"

    def test_deterministic_seed(self):
        """Verify that the same seed produces the same data."""
        df1 = generate_synthetic_data(n_samples=50, seed=42)
        df2 = generate_synthetic_data(n_samples=50, seed=42)

        pd.testing.assert_frame_equal(df1, df2)