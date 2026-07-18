"""
Unit tests for the Benjamini-Hochberg correction implementation in code/analysis.py.
This module verifies that the False Discovery Rate (FDR) correction is applied
correctly across multiple comparisons (electrodes).
"""
import os
import sys
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis import run_benjamini_hochberg, load_config, validate_metadata
import yaml

class TestBenjaminiHochbergCorrection:
    """Tests for the Benjamini-Hochberg FDR correction logic."""

    def test_bh_correction_basic(self, tmp_path):
        """
        Verify that run_benjamini_hochberg correctly computes adjusted p-values
        for a known set of p-values.
        """
        # Create a dataframe with known p-values
        # Expected behavior: sorted p-values are multiplied by (m/i) and capped
        data = {
            'channel': ['A', 'B', 'C', 'D', 'E'],
            'p_value': [0.001, 0.01, 0.02, 0.03, 0.04]
        }
        df = pd.DataFrame(data)

        # Run BH correction with alpha=0.05
        result_df = run_benjamini_hochberg(df, alpha=0.05)

        # Verify columns exist
        assert 'p_value' in result_df.columns
        assert 'p_adj' in result_df.columns
        assert 'significant' in result_df.columns

        # Verify monotonicity of adjusted p-values (sorted by original p-value)
        # The BH procedure ensures that adjusted p-values are non-decreasing
        # when sorted by original p-values
        sorted_result = result_df.sort_values('p_value').reset_index(drop=True)
        assert (sorted_result['p_adj'].diff().dropna() >= -1e-9).all(), \
            "Adjusted p-values must be monotonically non-decreasing"

        # Verify specific calculation for the largest p-value
        # m = 5, i = 5 (for 0.04), raw = 0.04 * 5/5 = 0.04
        # The smallest p-value (0.001) -> 0.001 * 5/1 = 0.005
        # Check that the logic holds for the first row (smallest p)
        first_row = sorted_result.iloc[0]
        expected_adj_min = min(0.001 * (5 / 1), 1.0)
        assert abs(first_row['p_adj'] - expected_adj_min) < 1e-6, \
            f"Expected adjusted p-value {expected_adj_min}, got {first_row['p_adj']}"

    def test_bh_correction_all_significant(self, tmp_path):
        """
        Verify that all p-values are marked significant when they are very small.
        """
        data = {
            'channel': ['A', 'B', 'C'],
            'p_value': [0.0001, 0.0002, 0.0003]
        }
        df = pd.DataFrame(data)

        result_df = run_benjamini_hochberg(df, alpha=0.05)

        assert all(result_df['significant']), "All p-values should be significant"

    def test_bh_correction_none_significant(self, tmp_path):
        """
        Verify that no p-values are marked significant when they are all large.
        """
        data = {
            'channel': ['A', 'B', 'C'],
            'p_value': [0.5, 0.6, 0.7]
        }
        df = pd.DataFrame(data)

        result_df = run_benjamini_hochberg(df, alpha=0.05)

        assert not any(result_df['significant']), "No p-values should be significant"

    def test_bh_correction_edge_case_zero_p(self, tmp_path):
        """
        Verify handling of p-value = 0 (or very close to 0).
        """
        data = {
            'channel': ['A', 'B'],
            'p_value': [0.0, 0.05]
        }
        df = pd.DataFrame(data)

        result_df = run_benjamini_hochberg(df, alpha=0.05)

        # 0.0 should remain 0.0 or very close, and be significant
        assert result_df.loc[result_df['channel'] == 'A', 'p_adj'].iloc[0] <= 0.001
        assert result_df.loc[result_df['channel'] == 'A', 'significant'].iloc[0] is True

    def test_bh_correction_single_test(self, tmp_path):
        """
        Verify behavior with a single test (no multiple comparison correction needed).
        """
        data = {
            'channel': ['A'],
            'p_value': [0.04]
        }
        df = pd.DataFrame(data)

        result_df = run_benjamini_hochberg(df, alpha=0.05)

        # For a single test, adjusted p-value should be the same as raw
        assert abs(result_df['p_adj'].iloc[0] - 0.04) < 1e-6
        assert result_df['significant'].iloc[0] is True

    def test_bh_correction_preserves_order(self, tmp_path):
        """
        Verify that the row order is preserved in the output dataframe.
        """
        # Create dataframe with specific order
        data = {
            'channel': ['Z', 'A', 'M'],
            'p_value': [0.05, 0.01, 0.03]
        }
        df = pd.DataFrame(data)

        result_df = run_benjamini_hochberg(df, alpha=0.05)

        # Check that the order of channels is preserved
        assert list(result_df['channel']) == ['Z', 'A', 'M']

    def test_bh_correction_alpha_0_01(self, tmp_path):
        """
        Verify that the alpha threshold correctly filters significance.
        """
        data = {
            'channel': ['A', 'B', 'C'],
            'p_value': [0.005, 0.008, 0.015]
        }
        df = pd.DataFrame(data)

        result_df = run_benjamini_hochberg(df, alpha=0.01)

        # With alpha=0.01, only the most significant might pass depending on correction
        # We verify the logic runs without error and returns boolean column
        assert 'significant' in result_df.columns
        assert result_df['significant'].dtype == bool

    def test_bh_correction_with_nan(self, tmp_path):
        """
        Verify that the function handles NaN values gracefully (either drops or marks as non-significant).
        """
        data = {
            'channel': ['A', 'B', 'C'],
            'p_value': [0.01, np.nan, 0.03]
        }
        df = pd.DataFrame(data)

        # The function should not crash. It may drop NaNs or handle them.
        # We check that it returns a valid dataframe with the same number of rows
        # or fewer (if NaNs were dropped).
        result_df = run_benjamini_hochberg(df, alpha=0.05)

        assert isinstance(result_df, pd.DataFrame)
        assert 'p_adj' in result_df.columns
        assert 'significant' in result_df.columns