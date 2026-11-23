"""
Unit tests for sensitivity analysis module.

FR-009: Verify p-value sweep output includes results for {0.01, 0.05, 0.1}.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
import tempfile
from typing import Dict, Any

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.utils.sensitivity import (
    run_sensitivity_analysis,
    save_sensitivity_report,
    setup_logger_module
)


class TestSensitivityAnalysis:
    """Test suite for sensitivity analysis functions."""

    @pytest.fixture
    def sample_correlation_data(self) -> pd.DataFrame:
        """Create sample correlation data for testing."""
        np.random.seed(42)
        n_samples = 100

        # Create sample data with known correlations
        data = {
            'feature_A': np.random.randn(n_samples),
            'feature_B': np.random.randn(n_samples),
            'feature_C': np.random.randn(n_samples),
            'thermal_conductivity': np.random.randn(n_samples)
        }

        df = pd.DataFrame(data)

        # Calculate correlations and p-values
        results = []
        for feature in ['feature_A', 'feature_B', 'feature_C']:
            corr = df[feature].corr(df['thermal_conductivity'])
            # Calculate p-value using t-distribution
            n = len(df)
            t_stat = corr * np.sqrt((n - 2) / (1 - corr**2))
            p_value = 2 * (1 - abs(t_stat) / (abs(t_stat) + np.sqrt((n - 2))))

            results.append({
                'feature': feature,
                'correlation': corr,
                'p_value': max(p_value, 0.001)  # Ensure non-zero
            })

        return pd.DataFrame(results)

    @pytest.fixture
    def sample_dict_data(self) -> Dict[str, Any]:
        """Create sample correlation data as dict."""
        return {
            'feature_A': [0.5, 0.02],
            'feature_B': [0.3, 0.15],
            'feature_C': [0.7, 0.005]
        }

    def test_run_sensitivity_analysis_dataframe(self, sample_correlation_data):
        """Test sensitivity analysis with DataFrame input."""
        thresholds = [0.01, 0.05, 0.1]

        results = run_sensitivity_analysis(
            correlation_results=sample_correlation_data,
            p_value_columns=['p_value'],
            thresholds=thresholds
        )

        # Verify structure
        assert 'thresholds' in results
        assert 'results' in results
        assert 'summary' in results

        # Verify thresholds match
        assert results['thresholds'] == thresholds

        # Verify results for each threshold
        for threshold in thresholds:
            key = str(threshold)
            assert key in results['results']
            assert 'significant_count' in results['results'][key]
            assert 'significant_pairs' in results['results'][key]
            assert 'correlation_values' in results['results'][key]

    def test_run_sensitivity_analysis_dict(self, sample_dict_data):
        """Test sensitivity analysis with dict input."""
        thresholds = [0.01, 0.05, 0.1]

        # Convert dict to DataFrame format expected by function
        df = pd.DataFrame({
            'feature': list(sample_dict_data.keys()),
            'correlation': [v[0] for v in sample_dict_data.values()],
            'p_value': [v[1] for v in sample_dict_data.values()]
        })

        results = run_sensitivity_analysis(
            correlation_results=df,
            p_value_columns=['p_value'],
            thresholds=thresholds
        )

        # Verify FR-009: thresholds 0.01, 0.05, 0.1 are present
        assert '0.01' in results['results']
        assert '0.05' in results['results']
        assert '0.1' in results['results']

    def test_sensitivity_across_thresholds(self, sample_correlation_data):
        """Test that significant count varies across thresholds."""
        thresholds = [0.01, 0.05, 0.1]

        results = run_sensitivity_analysis(
            correlation_results=sample_correlation_data,
            p_value_columns=['p_value'],
            thresholds=thresholds
        )

        # Counts should be non-decreasing as threshold increases
        counts = [results['results'][str(t)]['significant_count'] for t in thresholds]

        # Verify monotonicity (looser check due to floating point)
        assert all(counts[i] <= counts[i+1] for i in range(len(counts)-1))

    def test_empty_dataframe_raises_error(self):
        """Test that empty DataFrame raises ValueError."""
        empty_df = pd.DataFrame(columns=['feature', 'correlation', 'p_value'])

        with pytest.raises(ValueError, match="correlation_results is empty"):
            run_sensitivity_analysis(
                correlation_results=empty_df,
                p_value_columns=['p_value'],
                thresholds=[0.05]
            )

    def test_missing_p_value_columns_raises_error(self, sample_correlation_data):
        """Test that missing p-value columns raise ValueError."""
        with pytest.raises(ValueError, match="P-value columns not found"):
            run_sensitivity_analysis(
                correlation_results=sample_correlation_data,
                p_value_columns=['nonexistent_column'],
                thresholds=[0.05]
            )

    def test_invalid_input_type_raises_error(self):
        """Test that invalid input type raises TypeError."""
        with pytest.raises(TypeError, match="correlation_results must be a DataFrame or dict"):
            run_sensitivity_analysis(
                correlation_results="invalid",
                p_value_columns=['p_value'],
                thresholds=[0.05]
            )

    def test_save_sensitivity_report(self, sample_correlation_data):
        """Test saving sensitivity report to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sensitivity_report.json"

            results = run_sensitivity_analysis(
                correlation_results=sample_correlation_data,
                p_value_columns=['p_value'],
                thresholds=[0.05]
            )

            save_sensitivity_report(results, output_path)

            # Verify file exists
            assert output_path.exists()

            # Verify JSON is valid
            with open(output_path, 'r') as f:
                loaded = json.load(f)

            assert 'thresholds' in loaded
            assert 'results' in loaded

    def test_multiple_p_value_columns(self, sample_correlation_data):
        """Test analysis with multiple p-value columns."""
        # Add another p-value column
        df = sample_correlation_data.copy()
        df['p_value_adjusted'] = df['p_value'] * 1.5

        results = run_sensitivity_analysis(
            correlation_results=df,
            p_value_columns=['p_value', 'p_value_adjusted'],
            thresholds=[0.05, 0.1]
        )

        # Verify both columns are considered
        assert '0.05' in results['results']
        assert '0.1' in results['results']

    def test_summary_statistics(self, sample_correlation_data):
        """Test that summary statistics are correctly computed."""
        thresholds = [0.01, 0.05, 0.1]

        results = run_sensitivity_analysis(
            correlation_results=sample_correlation_data,
            p_value_columns=['p_value'],
            thresholds=thresholds
        )

        summary = results['summary']

        assert summary['total_thresholds'] == len(thresholds)
        assert 'min_significant' in summary
        assert 'max_significant' in summary
        assert summary['thresholds_evaluated'] == thresholds

    def test_correlation_values_extracted(self, sample_correlation_data):
        """Test that correlation values are extracted for significant pairs."""
        results = run_sensitivity_analysis(
            correlation_results=sample_correlation_data,
            p_value_columns=['p_value'],
            thresholds=[0.05]
        )

        threshold_key = '0.05'
        corr_values = results['results'][threshold_key]['correlation_values']

        # Verify correlation values are present for significant pairs
        if results['results'][threshold_key]['significant_count'] > 0:
            assert len(corr_values) > 0
            for key, value in corr_values.items():
                # Values should be numeric (or None if not available)
                assert isinstance(value, (float, int, type(None)))

    def test_seeds_determinism(self, sample_correlation_data):
        """Test that results are deterministic (no randomness involved)."""
        results1 = run_sensitivity_analysis(
            correlation_results=sample_correlation_data,
            p_value_columns=['p_value'],
            thresholds=[0.05]
        )

        results2 = run_sensitivity_analysis(
            correlation_results=sample_correlation_data,
            p_value_columns=['p_value'],
            thresholds=[0.05]
        )

        # Results should be identical
        assert results1 == results2

    def test_fr009_requirement(self, sample_correlation_data):
        """
        Verify FR-009: p-value sweep output includes results for {0.01, 0.05, 0.1}.

        This test explicitly checks that the required thresholds are present
        in the output as specified in the functional requirement.
        """
        # Use the exact thresholds from FR-009
        required_thresholds = [0.01, 0.05, 0.1]

        results = run_sensitivity_analysis(
            correlation_results=sample_correlation_data,
            p_value_columns=['p_value'],
            thresholds=required_thresholds
        )

        # Verify each required threshold is present
        for threshold in required_thresholds:
            key = str(threshold)
            assert key in results['results'], f"Threshold {threshold} missing from results"

            # Verify structure for each threshold
            threshold_result = results['results'][key]
            assert 'significant_count' in threshold_result
            assert 'significant_pairs' in threshold_result
            assert 'correlation_values' in threshold_result

    def test_large_threshold_range(self, sample_correlation_data):
        """Test with a wide range of thresholds."""
        thresholds = [0.001, 0.01, 0.05, 0.1, 0.2, 0.5]

        results = run_sensitivity_analysis(
            correlation_results=sample_correlation_data,
            p_value_columns=['p_value'],
            thresholds=thresholds
        )

        assert len(results['results']) == len(thresholds)
        for threshold in thresholds:
            assert str(threshold) in results['results']