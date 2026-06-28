"""
Unit tests for sensitivity analysis across clone detection thresholds.

This module tests the sensitivity analysis functionality implemented in
correlation_analysis.py, specifically testing that the analysis correctly
handles multiple thresholds (0.7, 0.8, 0.9) and produces valid results
for each threshold.

This test is distinct from T030 which tests only Spearman coefficient
computation. T038 specifically tests the sensitivity analysis workflow
across multiple thresholds.

Tests validate:
- Sensitivity analysis runs successfully for all specified thresholds
- Results differ appropriately across thresholds
- Thresholds are properly documented and reproducible
- Correlation metrics are computed correctly for each threshold
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'code'))

from correlation_analysis import (
    compute_sensitivity_analysis,
    load_correlation_data,
    validate_thresholds,
    get_threshold_results,
    compute_threshold_correlation
)


class TestSensitivityAnalysisThresholds:
    """Test sensitivity analysis across clone detection thresholds."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for sensitivity analysis testing."""
        np.random.seed(42)
        n_samples = 100
        
        # Generate synthetic clone density and perplexity data
        clone_density = np.random.uniform(0.0, 1.0, n_samples)
        perplexity = 10 + np.random.normal(0, 2, n_samples)
        bug_detection_acc = np.random.uniform(0.5, 1.0, n_samples)
        
        df = pd.DataFrame({
            'clone_density': clone_density,
            'perplexity': perplexity,
            'bug_detection_accuracy': bug_detection_acc,
            'threshold': 0.8  # Default threshold
        })
        return df

    @pytest.fixture
    def thresholds(self):
        """Return the standard sensitivity analysis thresholds."""
        return [0.7, 0.8, 0.9]

    def test_thresholds_are_valid(self, thresholds):
        """Test that the specified thresholds are valid (between 0 and 1)."""
        for threshold in thresholds:
            assert 0.0 <= threshold <= 1.0, f"Threshold {threshold} must be between 0 and 1"
            assert isinstance(threshold, (int, float)), f"Threshold {threshold} must be numeric"

    def test_validate_thresholds_function(self, thresholds):
        """Test the validate_thresholds function accepts valid thresholds."""
        result = validate_thresholds(thresholds)
        assert result is True
        assert len(result) == 0 if isinstance(result, list) else True

    def test_validate_thresholds_rejects_invalid(self):
        """Test that validate_thresholds rejects invalid thresholds."""
        invalid_thresholds = [0.5, 1.5, -0.1]
        result = validate_thresholds(invalid_thresholds)
        assert result is False

    def test_sensitivity_analysis_runs_for_all_thresholds(self, sample_data, thresholds):
        """Test that sensitivity analysis executes successfully for all thresholds."""
        with patch('correlation_analysis.spearmanr') as mock_spearman:
            # Mock the correlation function to return deterministic values
            mock_spearman.return_value = (0.5, 0.01)
            
            results = compute_sensitivity_analysis(sample_data, thresholds)
            
            # Verify results exist for all thresholds
            assert len(results) == len(thresholds), \
                f"Expected {len(thresholds)} results, got {len(results)}"
            
            # Verify each threshold has a result
            for threshold in thresholds:
                assert threshold in results, f"Missing results for threshold {threshold}"

    def test_results_differ_across_thresholds(self, sample_data, thresholds):
        """Test that different thresholds produce different correlation results."""
        with patch('correlation_analysis.spearmanr') as mock_spearman:
            # Make the mock return different values based on threshold
            def mock_return(*args, **kwargs):
                threshold = kwargs.get('threshold', 0.8)
                # Different thresholds should yield different correlations
                correlation = 0.3 + (threshold * 0.2)
                return (correlation, 0.01)
            
            mock_spearman.side_effect = mock_return
            
            results = compute_sensitivity_analysis(sample_data, thresholds)
            
            # Verify results are different across thresholds
        correlations = [results[t]['correlation'] for t in thresholds]
        assert len(set(correlations)) > 1, \
            "Different thresholds should produce different correlation values"

    def test_threshold_07_computation(self, sample_data):
        """Test correlation computation specifically for threshold 0.7."""
        with patch('correlation_analysis.spearmanr') as mock_spearman:
            mock_spearman.return_value = (0.45, 0.02)
            
            result = compute_threshold_correlation(sample_data, threshold=0.7)
            
            assert result['threshold'] == 0.7
            assert result['correlation'] == 0.45
            assert result['p_value'] == 0.02

    def test_threshold_08_computation(self, sample_data):
        """Test correlation computation specifically for threshold 0.8."""
        with patch('correlation_analysis.spearmanr') as mock_spearman:
            mock_spearman.return_value = (0.52, 0.015)
            
            result = compute_threshold_correlation(sample_data, threshold=0.8)
            
            assert result['threshold'] == 0.8
            assert result['correlation'] == 0.52
            assert result['p_value'] == 0.015

    def test_threshold_09_computation(self, sample_data):
        """Test correlation computation specifically for threshold 0.9."""
        with patch('correlation_analysis.spearmanr') as mock_spearman:
            mock_spearman.return_value = (0.61, 0.008)
            
            result = compute_threshold_correlation(sample_data, threshold=0.9)
            
            assert result['threshold'] == 0.9
            assert result['correlation'] == 0.61
            assert result['p_value'] == 0.008

    def test_get_threshold_results_returns_all(self, sample_data, thresholds):
        """Test that get_threshold_results returns results for all thresholds."""
        with patch('correlation_analysis.compute_threshold_correlation') as mock_compute:
            mock_compute.return_value = {
                'threshold': 0.8,
                'correlation': 0.5,
                'p_value': 0.01
            }
            
            results = get_threshold_results(sample_data, thresholds)
            
            assert len(results) == len(thresholds)
            for threshold in thresholds:
                assert threshold in results

    def test_reproducibility_with_fixed_seed(self, sample_data, thresholds):
        """Test that sensitivity analysis is reproducible with fixed seed."""
        with patch('correlation_analysis.spearmanr') as mock_spearman:
            mock_spearman.return_value = (0.5, 0.01)
            
            # Run twice with same data
            results1 = compute_sensitivity_analysis(sample_data, thresholds)
            results2 = compute_sensitivity_analysis(sample_data, thresholds)
            
            # Results should be identical
        for threshold in thresholds:
            assert results1[threshold]['correlation'] == results2[threshold]['correlation']
            assert results1[threshold]['p_value'] == results2[threshold]['p_value']

    def test_empty_data_handling(self, thresholds):
        """Test that sensitivity analysis handles empty data gracefully."""
        empty_df = pd.DataFrame(columns=['clone_density', 'perplexity', 'threshold'])
        
        with patch('correlation_analysis.spearmanr') as mock_spearman:
            mock_spearman.return_value = (np.nan, np.nan)
            
            results = compute_sensitivity_analysis(empty_df, thresholds)
            
            # Should still produce results structure, even if values are NaN
            assert len(results) == len(thresholds)

    def test_single_sample_data(self, thresholds):
        """Test sensitivity analysis with minimal data (single sample)."""
        single_df = pd.DataFrame({
            'clone_density': [0.5],
            'perplexity': [10.0],
            'threshold': [0.8]
        })
        
        with patch('correlation_analysis.spearmanr') as mock_spearman:
            # Spearman with single sample may return NaN
            mock_spearman.return_value = (np.nan, np.nan)
            
            results = compute_sensitivity_analysis(single_df, thresholds)
            
            assert len(results) == len(thresholds)

    def test_results_contain_required_fields(self, sample_data, thresholds):
        """Test that sensitivity analysis results contain all required fields."""
        with patch('correlation_analysis.spearmanr') as mock_spearman:
            mock_spearman.return_value = (0.5, 0.01)
            
            results = compute_sensitivity_analysis(sample_data, thresholds)
            
            required_fields = ['threshold', 'correlation', 'p_value', 'n_samples']
            for threshold in thresholds:
                result = results[threshold]
                for field in required_fields:
                    assert field in result, f"Missing field '{field}' in result for threshold {threshold}"

    def test_correlation_significance_tracking(self, sample_data, thresholds):
        """Test that significance is properly tracked across thresholds."""
        with patch('correlation_analysis.spearmanr') as mock_spearman:
            # Return varying p-values
            def mock_return(*args, **kwargs):
                threshold = kwargs.get('threshold', 0.8)
                p_value = 0.05 - (threshold * 0.03)  # Different p-values
                return (0.5, p_value)
            
            mock_spearman.side_effect = mock_return
            
            results = compute_sensitivity_analysis(sample_data, thresholds)
            
            # Verify p-values are different and tracked
            p_values = [results[t]['p_value'] for t in thresholds]
            assert len(set(p_values)) > 1, "Different thresholds should have different p-values"


class TestThresholdValidation:
    """Test threshold validation utilities."""

    def test_standard_thresholds_valid(self):
        """Test that the standard sensitivity analysis thresholds are valid."""
        standard_thresholds = [0.7, 0.8, 0.9]
        assert all(0.0 <= t <= 1.0 for t in standard_thresholds)

    def test_threshold_range_coverage(self):
        """Test that thresholds cover a meaningful range."""
        thresholds = [0.7, 0.8, 0.9]
        range_span = max(thresholds) - min(thresholds)
        assert range_span >= 0.2, "Threshold range should span at least 0.2"

    def test_threshold_step_size(self):
        """Test that threshold steps are consistent."""
        thresholds = [0.7, 0.8, 0.9]
        steps = [thresholds[i+1] - thresholds[i] for i in range(len(thresholds)-1)]
        assert all(step == 0.1 for step in steps), "Threshold steps should be consistent (0.1)"


class TestCorrelationDataLoading:
    """Test correlation data loading for sensitivity analysis."""

    def test_load_correlation_data_with_file(self, tmp_path):
        """Test loading correlation data from a CSV file."""
        # Create sample data file
        csv_path = tmp_path / 'correlation_data.csv'
        df = pd.DataFrame({
            'clone_density': [0.3, 0.5, 0.7],
            'perplexity': [10.0, 12.0, 15.0],
            'threshold': [0.7, 0.8, 0.9]
        })
        df.to_csv(csv_path, index=False)
        
        loaded_df = load_correlation_data(str(csv_path))
        assert loaded_df is not None
        assert len(loaded_df) == 3
        assert 'clone_density' in loaded_df.columns

    def test_load_correlation_data_missing_file(self):
        """Test that missing file is handled gracefully."""
        with pytest.raises(FileNotFoundError):
            load_correlation_data('/nonexistent/path/data.csv')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])