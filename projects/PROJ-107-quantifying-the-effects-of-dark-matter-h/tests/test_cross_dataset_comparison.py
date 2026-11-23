"""
Unit tests for cross-dataset comparison logic (T033).

Tests verify:
  - Loading of statistical results from different datasets
  - Comparison of statistical metrics between datasets
  - Significance rate comparisons
  - Report generation
  - Handling of missing datasets
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.cross_dataset_comparison import (
    load_statistical_results,
    compare_statistical_metrics,
    compare_significance_rates,
    generate_cross_dataset_report,
    run_cross_dataset_comparison
)
from utils.config import get_project_root


class TestCrossDatasetComparison:
    """Test suite for cross-dataset comparison functions."""

    @pytest.fixture
    def sample_tng_results(self):
        """Create sample TNG-100 statistical results."""
        data = {
            'p_value': [0.01, 0.03, 0.05, 0.10, 0.20],
            'effect_size': [0.5, 0.3, 0.2, 0.1, 0.05],
            'correlation': [0.7, 0.5, 0.3, 0.1, 0.0],
            'test_type': ['kw', 'mwu', 'ks', 'regression', 'regression'],
            'property': ['sfr', 'sfr', 'radius', 'sfr', 'radius']
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_millennium_results(self):
        """Create sample Millennium-II statistical results."""
        data = {
            'p_value': [0.02, 0.04, 0.06, 0.15, 0.25],
            'effect_size': [0.45, 0.28, 0.18, 0.08, 0.04],
            'correlation': [0.65, 0.48, 0.28, 0.08, 0.0],
            'test_type': ['kw', 'mwu', 'ks', 'regression', 'regression'],
            'property': ['sfr', 'sfr', 'radius', 'sfr', 'radius']
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_wdm_results(self):
        """Create sample WDM statistical results."""
        data = {
            'p_value': [0.015, 0.035, 0.055, 0.12, 0.22],
            'effect_size': [0.48, 0.29, 0.19, 0.09, 0.045],
            'correlation': [0.68, 0.49, 0.29, 0.09, 0.0],
            'test_type': ['kw', 'mwu', 'ks', 'regression', 'regression'],
            'property': ['sfr', 'sfr', 'radius', 'sfr', 'radius']
        }
        return pd.DataFrame(data)

    def test_compare_statistical_metrics(self, sample_tng_results, sample_millennium_results):
        """Test comparison of statistical metrics between datasets."""
        result = compare_statistical_metrics(
            sample_tng_results,
            sample_millennium_results,
            metric_columns=['p_value', 'effect_size', 'correlation']
        )

        assert 'datasets' in result
        assert result['datasets'] == ['tng', 'other']
        assert 'differences' in result

        # Check that all requested metrics are in the result
        for metric in ['p_value', 'effect_size', 'correlation']:
            assert metric in result['differences']
            assert 'mean_tng' in result['differences'][metric]
            assert 'mean_other' in result['differences'][metric]
            assert 'mean_difference' in result['differences'][metric]

    def test_compare_significance_rates(self, sample_tng_results, sample_millennium_results):
        """Test comparison of significance rates between datasets."""
        result = compare_significance_rates(
            sample_tng_results,
            sample_millennium_results,
            significance_threshold=0.05
        )

        assert 'significance_threshold' in result
        assert result['significance_threshold'] == 0.05
        assert 'tng' in result
        assert 'other' in result
        assert 'rate_difference' in result

        # TNG should have 2 significant tests (p < 0.05)
        assert result['tng']['significant_count'] == 2
        # Millennium should have 2 significant tests (p < 0.05)
        assert result['other']['significant_count'] == 2

    def test_generate_cross_dataset_report(self, sample_tng_results, sample_millennium_results):
        """Test generation of cross-dataset comparison report."""
        comp_result = compare_statistical_metrics(
            sample_tng_results,
            sample_millennium_results,
            metric_columns=['p_value']
        )

        sig_comp = compare_significance_rates(
            sample_tng_results,
            sample_millennium_results,
            significance_threshold=0.05
        )

        report_df = generate_cross_dataset_report(
            [comp_result],
            [sig_comp],
            missing_datasets=['wdm']
        )

        assert isinstance(report_df, pd.DataFrame)
        assert len(report_df) > 0
        assert 'dataset' in report_df.columns
        assert 'metric' in report_df.columns
        assert 'status' in report_df.columns
        assert 'associational_only' in report_df.columns

        # Check that associational_only flag is set
        assert all(report_df['associational_only'] == True)

    def test_compare_with_nan_values(self):
        """Test comparison handling of NaN values."""
        tng_data = {
            'p_value': [0.01, np.nan, 0.05, 0.10],
            'effect_size': [0.5, 0.3, np.nan, 0.1]
        }
        other_data = {
            'p_value': [0.02, 0.04, np.nan, 0.15],
            'effect_size': [np.nan, 0.28, 0.18, 0.08]
        }

        tng_df = pd.DataFrame(tng_data)
        other_df = pd.DataFrame(other_data)

        result = compare_statistical_metrics(
            tng_df,
            other_df,
            metric_columns=['p_value', 'effect_size']
        )

        # Should handle NaN gracefully and still produce results
        assert 'differences' in result
        assert 'p_value' in result['differences']
        assert 'effect_size' in result['differences']

    def test_compare_with_missing_columns(self, sample_tng_results):
        """Test comparison when columns are missing."""
        # Create a DataFrame with different columns
        other_data = {
            'p_value': [0.02, 0.04, 0.06],
            'different_metric': [0.1, 0.2, 0.3]
        }
        other_df = pd.DataFrame(other_data)

        result = compare_statistical_metrics(
            sample_tng_results,
            other_df,
            metric_columns=['p_value', 'effect_size', 'nonexistent']
        )

        # Should only include columns present in both
        assert 'p_value' in result['differences']
        assert 'effect_size' not in result['differences']
        assert 'nonexistent' not in result['differences']

    def test_significance_rate_with_threshold(self, sample_tng_results):
        """Test significance rate calculation with different thresholds."""
        result_01 = compare_significance_rates(
            sample_tng_results,
            sample_tng_results,
            significance_threshold=0.01
        )

        result_05 = compare_significance_rates(
            sample_tng_results,
            sample_tng_results,
            significance_threshold=0.05
        )

        # With threshold 0.01, only 1 test should be significant
        assert result_01['tng']['significant_count'] == 1
        # With threshold 0.05, 2 tests should be significant
        assert result_05['tng']['significant_count'] == 2

    def test_empty_dataframe_comparison(self):
        """Test comparison with empty DataFrames."""
        empty_df = pd.DataFrame()
        sample_df = pd.DataFrame({'p_value': [0.01, 0.05]})

        result = compare_statistical_metrics(
            empty_df,
            sample_df,
            metric_columns=['p_value']
        )

        # Should handle empty DataFrames gracefully
        assert 'differences' in result
        assert 'p_value' in result['differences']
        assert result['differences']['p_value']['tng_count'] == 0

    def test_report_with_multiple_missing_datasets(self):
        """Test report generation with multiple missing datasets."""
        sample_comp = {
            'datasets': ['tng', 'millennium'],
            'differences': {}
        }
        sample_sig = {
            'datasets': ['tng', 'millennium'],
            'significance_threshold': 0.05,
            'tng': {'rate': 0.5, 'significant_count': 1, 'total_count': 2},
            'other': {'rate': 0.4, 'significant_count': 2, 'total_count': 5},
            'rate_difference': -0.1
        }

        report_df = generate_cross_dataset_report(
            [sample_comp],
            [sample_sig],
            missing_datasets=['millennium', 'wdm']
        )

        # Check that missing datasets are reported
        missing_rows = report_df[report_df['status'] == 'missing']
        assert len(missing_rows) == 2

        # Check that available comparisons are still in the report
        available_rows = report_df[report_df['status'] == 'available']
        assert len(available_rows) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])