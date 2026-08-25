import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.zero_replace import (
    estimate_zero_replacement_params,
    bayesian_multiplicative_replace,
    process_batch
)
from code.utils.logging import PreprocessingError

class TestZeroReplacement:
    """Test suite for Bayesian-multiplicative zero replacement."""

    @pytest.fixture
    def sample_counts_with_zeros(self):
        """Create a sample dataframe with known zeros for testing."""
        data = {
            'taxon_A': [10, 0, 50, 0, 100],
            'taxon_B': [0, 20, 0, 40, 0],
            'taxon_C': [30, 30, 30, 30, 30],  # No zeros
            'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5']
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_counts_all_nonzero(self):
        """Create a sample dataframe with no zeros."""
        data = {
            'taxon_A': [10, 20, 30, 40, 50],
            'taxon_B': [15, 25, 35, 45, 55],
            'taxon_C': [5, 15, 25, 35, 45]
        }
        return pd.DataFrame(data)

    def test_estimate_params_calculates_geometric_means(self, sample_counts_with_zeros):
        """Test that geometric means are calculated correctly for non-zero values."""
        params = estimate_zero_replacement_params(sample_counts_with_zeros)

        # Check delta is set
        assert 'delta' in params
        assert params['delta'] == 0.65

        # Check geometric means are calculated
        assert 'geometric_means' in params
        geo_means = params['geometric_means']

        # Taxon A: non-zero values are [10, 50, 100]
        # Geometric mean = (10 * 50 * 100)^(1/3) = 50000^(1/3) ≈ 36.84
        expected_A = np.exp(np.mean(np.log([10, 50, 100])))
        assert abs(geo_means['taxon_A'] - expected_A) < 1e-6

        # Taxon B: non-zero values are [20, 40]
        # Geometric mean = (20 * 40)^(1/2) = 800^(1/2) ≈ 28.28
        expected_B = np.exp(np.mean(np.log([20, 40])))
        assert abs(geo_means['taxon_B'] - expected_B) < 1e-6

        # Taxon C: all values are 30
        assert abs(geo_means['taxon_C'] - 30.0) < 1e-6

    def test_bayesian_replacement_replaces_zeros(self, sample_counts_with_zeros):
        """Test that zeros are replaced with small positive values."""
        params = estimate_zero_replacement_params(sample_counts_with_zeros)
        result = bayesian_multiplicative_replace(sample_counts_with_zeros, params)

        # Check no zeros remain
        numeric_cols = result.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            assert (result[col] == 0).sum() == 0, f"Zeros still present in {col}"

        # Check non-zero values are preserved
        assert result.loc[0, 'taxon_A'] == 10
        assert result.loc[2, 'taxon_A'] == 50

        # Check that replaced values are positive and small
        # Taxon A, row 1 was 0, should be delta * geo_mean
        expected_replacement_A = 0.65 * params['geometric_means']['taxon_A']
        assert result.loc[1, 'taxon_A'] == expected_replacement_A

    def test_bayesian_replacement_preserves_non_zeros(self, sample_counts_all_nonzero):
        """Test that non-zero values are not modified."""
        params = estimate_zero_replacement_params(sample_counts_all_nonzero)
        result = bayesian_multiplicative_replace(sample_counts_all_nonzero, params)

        # All values should be identical
        pd.testing.assert_frame_equal(result, sample_counts_all_nonzero)

    def test_replacement_values_are_positive(self, sample_counts_with_zeros):
        """Test that all replacement values are positive."""
        params = estimate_zero_replacement_params(sample_counts_with_zeros)
        result = bayesian_multiplicative_replace(sample_counts_with_zeros, params)

        numeric_cols = result.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            assert (result[col] > 0).all(), f"Non-positive values found in {col}"

    def test_process_batch_function(self, sample_counts_with_zeros):
        """Test the process_batch helper function."""
        params = estimate_zero_replacement_params(sample_counts_with_zeros)
        result = process_batch(sample_counts_with_zeros, params)

        # Should be same as bayesian_multiplicative_replace
        expected = bayesian_multiplicative_replace(sample_counts_with_zeros, params)
        pd.testing.assert_frame_equal(result, expected)

    def test_empty_dataframe_handling(self):
        """Test handling of empty dataframes."""
        empty_df = pd.DataFrame()
        params = {'delta': 0.65, 'geometric_means': {}}

        result = bayesian_multiplicative_replace(empty_df, params)
        assert result.empty

    def test_all_zero_column_handling(self):
        """Test handling of a column with all zeros."""
        data = {
            'taxon_A': [0, 0, 0, 0, 0],
            'taxon_B': [10, 20, 30, 40, 50]
        }
        df = pd.DataFrame(data)

        params = estimate_zero_replacement_params(df)
        result = bayesian_multiplicative_replace(df, params)

        # Check no zeros remain
        assert (result['taxon_A'] == 0).sum() == 0
        assert (result['taxon_B'] == 0).sum() == 0

        # Check values are positive
        assert (result['taxon_A'] > 0).all()

    def test_log_ready_output(self, sample_counts_with_zeros):
        """Test that output is ready for log transformation (no zeros)."""
        params = estimate_zero_replacement_params(sample_counts_with_zeros)
        result = bayesian_multiplicative_replace(sample_counts_with_zeros, params)

        # After replacement, log should not produce -inf
        numeric_cols = result.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            log_vals = np.log(result[col])
            assert not np.isinf(log_vals).any(), f"Log produced inf in {col}"
            assert not np.isnan(log_vals).any(), f"Log produced nan in {col}"
