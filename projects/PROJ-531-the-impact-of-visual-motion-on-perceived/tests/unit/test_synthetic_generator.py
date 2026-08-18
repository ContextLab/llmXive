"""
Unit tests for the synthetic data generator.

Verifies:
- Ground-truth correlation injection (FR-011).
- Instrument validation logic (distinctness of user_response_trigger and agency_score).
- Data shape and type constraints.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_synthetic_data import generate_synthetic_data

class TestSyntheticGenerator:
    """Tests for generate_synthetic_data function."""

    def test_sample_size(self):
        """Test that the generator produces the requested number of samples."""
        n = 150
        df = generate_synthetic_data(n_samples=n, seed=42)
        assert len(df) == n, f"Expected {n} rows, got {len(df)}"

    def test_required_columns_exist(self):
        """Test that all required columns are present."""
        df = generate_synthetic_data(n_samples=10, seed=42)
        required_cols = ['participant_id', 'latency', 'smoothness', 'lead_time', 
                         'user_response_trigger', 'agency_score']
        for col in required_cols:
            assert col in df.columns, f"Missing required column: {col}"

    def test_ground_truth_correlation_injection(self):
        """
        Test FR-011: Verify that the injected ground-truth correlations exist.
        - Latency should be negatively correlated with Agency.
        - Smoothness (Jerk) should be negatively correlated with Agency.
        - Lead Time should be positively correlated with Agency.
        """
        # Use a large sample to ensure statistical significance of correlation
        df = generate_synthetic_data(n_samples=1000, seed=123)
        
        corr_latency = df['latency'].corr(df['agency_score'])
        corr_smoothness = df['smoothness'].corr(df['agency_score'])
        corr_lead_time = df['lead_time'].corr(df['agency_score'])
        
        # Assert negative correlations for latency and smoothness
        assert corr_latency < 0, f"Latency should be negatively correlated with Agency, got {corr_latency}"
        assert corr_smoothness < 0, f"Smoothness should be negatively correlated with Agency, got {corr_smoothness}"
        
        # Assert positive correlation for lead time
        assert corr_lead_time > 0, f"Lead Time should be positively correlated with Agency, got {corr_lead_time}"
        
        # Optional: Assert magnitude is non-trivial (e.g., > 0.1) to ensure injection worked
        assert abs(corr_latency) > 0.1, "Latency correlation magnitude too low"
        assert abs(corr_smoothness) > 0.1, "Smoothness correlation magnitude too low"
        assert abs(corr_lead_time) > 0.1, "Lead Time correlation magnitude too low"

    def test_fr_012_distinctness(self):
        """
        Test FR-012: Ensure `user_response_trigger` is distinct from `agency_score`.
        They should not be perfectly correlated or identical.
        """
        df = generate_synthetic_data(n_samples=500, seed=42)
        
        corr_trigger_agency = df['user_response_trigger'].corr(df['agency_score'])
        
        # They should not be perfectly correlated (r != 1.0)
        # In a realistic synthetic model, they might be weakly correlated or uncorrelated,
        # but definitely not identical.
        assert abs(corr_trigger_agency) < 0.95, \
            f"user_response_trigger is too correlated with agency_score ({corr_trigger_agency}), " \
            f"violating FR-012 distinctness requirement."
        
        # Verify they are not the same column (sanity check)
        assert not df['user_response_trigger'].equals(df['agency_score'])

    def test_data_types_and_ranges(self):
        """Test that data types and ranges are valid."""
        df = generate_synthetic_data(n_samples=100, seed=42)
        
        # Agency score should be between 0 and 1
        assert df['agency_score'].min() >= 0.0
        assert df['agency_score'].max() <= 1.0
        
        # Latency, smoothness, lead_time should be numeric and positive (mostly)
        assert df['latency'].dtype in [np.float64, np.int64]
        assert df['smoothness'].dtype in [np.float64, np.int64]
        assert df['lead_time'].dtype in [np.float64, np.int64]
        
        # Check for NaNs
        assert not df.isnull().any().any(), "Dataset contains NaN values"

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        df1 = generate_synthetic_data(n_samples=50, seed=99)
        df2 = generate_synthetic_data(n_samples=50, seed=99)
        
        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seed_produces_different_data(self):
        """Test that different seeds produce different results."""
        df1 = generate_synthetic_data(n_samples=50, seed=1)
        df2 = generate_synthetic_data(n_samples=50, seed=2)
        
        # Just check that they are not identical
        assert not df1.equals(df2), "Different seeds should produce different data"