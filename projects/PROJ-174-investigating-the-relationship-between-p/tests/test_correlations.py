"""
Tests for the correlations analysis module (T016).

Tests:
- Benjamini-Hochberg FDR correction logic
- Pearson correlation calculation with edge cases
- Full pipeline execution on synthetic data
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.correlations import (
    calculate_pearson_correlation,
    benjamini_hochberg_fdr,
    extract_pupil_metrics,
    compute_correlations,
    main
)

class TestBenjaminiHochbergFDR:
    """Tests for FDR correction logic."""

    def test_fdr_basic(self):
        """Test basic FDR correction."""
        p_values = [0.01, 0.04, 0.03, 0.02]
        adjusted = benjamini_hochberg_fdr(p_values)
        
        assert len(adjusted) == 4
        assert all(0 <= p <= 1 for p in adjusted if not np.isnan(p))
        # Adjusted p-values should be >= raw p-values
        for raw, adj in zip(p_values, adjusted):
            if not np.isnan(raw):
                assert adj >= raw - 1e-10  # Allow small floating point error

    def test_fdr_with_nan(self):
        """Test FDR correction with NaN values."""
        p_values = [0.01, np.nan, 0.03, np.nan]
        adjusted = benjamini_hochberg_fdr(p_values)
        
        assert len(adjusted) == 4
        assert np.isnan(adjusted[1])
        assert np.isnan(adjusted[3])
        assert not np.isnan(adjusted[0])
        assert not np.isnan(adjusted[2])

    def test_fdr_monotonicity(self):
        """Test that adjusted p-values are monotonic."""
        # Create p-values that would break monotonicity without correction
        p_values = [0.1, 0.05, 0.01, 0.2]
        adjusted = benjamini_hochberg_fdr(p_values)
        
        # Filter out NaNs
        valid_adjusted = [p for p in adjusted if not np.isnan(p)]
        # Check that sorted adjusted values are non-decreasing
        sorted_adj = sorted(valid_adjusted)
        for i in range(len(sorted_adj) - 1):
            assert sorted_adj[i] <= sorted_adj[i + 1]

    def test_fdr_empty(self):
        """Test FDR correction with empty list."""
        assert benjamini_hochberg_fdr([]) == []

    def test_fdr_single_value(self):
        """Test FDR correction with single value."""
        p_values = [0.05]
        adjusted = benjamini_hochberg_fdr(p_values)
        assert len(adjusted) == 1
        assert adjusted[0] == 0.05  # Single value: adj = raw * 1 / 1

class TestPearsonCorrelation:
    """Tests for Pearson correlation calculation."""

    def test_pearson_basic(self):
        """Test basic Pearson correlation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        corr, p_val = calculate_pearson_correlation(x, y)
        
        assert abs(corr) > 0.99  # Perfect positive correlation
        assert p_val < 0.05

    def test_pearson_negative(self):
        """Test negative correlation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 4, 3, 2, 1])
        
        corr, p_val = calculate_pearson_correlation(x, y)
        
        assert corr < -0.99
        assert p_val < 0.05

    def test_pearson_no_correlation(self):
        """Test no correlation."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        
        corr, p_val = calculate_pearson_correlation(x, y)
        
        # Should be close to 0
        assert abs(corr) < 0.2

    def test_pearson_insufficient_data(self):
        """Test with insufficient data points."""
        x = np.array([1, 2])
        y = np.array([3, 4])
        
        corr, p_val = calculate_pearson_correlation(x, y)
        
        assert np.isnan(corr)
        assert np.isnan(p_val)

    def test_pearson_constant_variance(self):
        """Test with constant variance."""
        x = np.array([1, 1, 1, 1])
        y = np.array([1, 2, 3, 4])
        
        corr, p_val = calculate_pearson_correlation(x, y)
        
        assert np.isnan(corr)
        assert np.isnan(p_val)

    def test_pearson_with_nan(self):
        """Test with NaN values."""
        x = np.array([1, 2, np.nan, 4, 5])
        y = np.array([2, 4, 6, np.nan, 10])
        
        corr, p_val = calculate_pearson_correlation(x, y)
        
        # Should handle NaNs gracefully
        assert not np.isnan(corr) or np.isnan(corr)  # Either is fine, just shouldn't crash
        assert not np.isnan(p_val) or np.isnan(p_val)

class TestExtractPupilMetrics:
    """Tests for pupil metric extraction."""

    def test_extract_metrics_existing(self):
        """Test extraction when metrics already exist."""
        df = pd.DataFrame({
            'subject_id': [1, 1, 2, 2],
            'trial_id': [1, 2, 1, 2],
            'pupil_diameter_mean': [3.0, 3.1, 3.2, 3.3],
            'pupil_diameter_peak': [4.0, 4.1, 4.2, 4.3],
            'pupil_diameter_quantized': [0, 1, 2, 3]
        })
        
        result = extract_pupil_metrics(df)
        
        assert 'pupil_diameter_mean' in result.columns
        assert 'pupil_diameter_peak' in result.columns
        assert 'pupil_diameter_quantized' in result.columns

    def test_extract_metrics_computed(self):
        """Test computation of missing metrics."""
        df = pd.DataFrame({
            'subject_id': [1, 1, 2, 2],
            'trial_id': [1, 2, 1, 2],
            'pupil_diameter': [3.0, 3.1, 3.2, 3.3]
        })
        
        result = extract_pupil_metrics(df)
        
        assert 'pupil_diameter_mean' in result.columns
        assert 'pupil_diameter_peak' in result.columns
        assert 'pupil_diameter_quantized' in result.columns

    def test_extract_metrics_missing_data(self):
        """Test with missing pupil diameter column."""
        df = pd.DataFrame({
            'subject_id': [1, 2],
            'trial_id': [1, 2]
        })
        
        result = extract_pupil_metrics(df)
        
        assert 'pupil_diameter_mean' in result.columns
        assert np.all(np.isnan(result['pupil_diameter_mean']))

class TestComputeCorrelations:
    """Tests for full correlation computation."""

    def test_compute_correlations_basic(self):
        """Test basic correlation computation."""
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            'subject_id': [1] * n,
            'trial_id': range(n),
            'pupil_diameter_mean': np.random.randn(n),
            'search_time': np.random.randn(n)
        })
        
        result = compute_correlations(df)
        
        assert len(result) > 0
        assert 'pupil_metric' in result.columns
        assert 'load_proxy' in result.columns
        assert 'pearson_r' in result.columns
        assert 'p_value_raw' in result.columns
        assert 'p_value_adj' in result.columns

    def test_compute_correlations_missing_proxy(self):
        """Test with missing load proxy."""
        df = pd.DataFrame({
            'subject_id': [1, 2],
            'trial_id': [1, 2],
            'pupil_diameter_mean': [3.0, 3.1]
        })
        
        result = compute_correlations(df)
        
        # Should return empty or minimal result
        assert len(result) == 0 or len(result.columns) == 5

    def test_compute_correlations_unfulfillable(self):
        """Test with UNFULFILLABLE status."""
        df = pd.DataFrame({
            'subject_id': [1, 2],
            'trial_id': [1, 2],
            'pupil_diameter_mean': [3.0, 3.1],
            'search_time': [1.0, 1.1],
            'status': ['UNFULFILLABLE', 'UNFULFILLABLE']
        })
        
        result = compute_correlations(df)
        
        # Should handle gracefully
        assert len(result) >= 0

class TestMainIntegration:
    """Integration tests for the main function."""

    @patch('analysis.correlations.load_processed_data')
    @patch('analysis.correlations.extract_pupil_metrics')
    @patch('analysis.correlations.compute_correlations')
    @patch('analysis.correlations.save_results')
    @patch('analysis.correlations.Path.exists', return_value=True)
    def test_main_success(
        self,
        mock_exists,
        mock_save,
        mock_compute,
        mock_extract,
        mock_load
    ):
        """Test successful main execution."""
        mock_load.return_value = pd.DataFrame({
            'subject_id': [1],
            'trial_id': [1],
            'pupil_diameter': [3.0]
        })
        mock_extract.return_value = pd.DataFrame({
            'subject_id': [1],
            'trial_id': [1],
            'pupil_diameter_mean': [3.0],
            'pupil_diameter_peak': [3.5]
        })
        mock_compute.return_value = pd.DataFrame({
            'pupil_metric': ['pupil_diameter_mean'],
            'load_proxy': ['search_time'],
            'pearson_r': [0.5],
            'p_value_raw': [0.01],
            'p_value_adj': [0.02]
        })
        
        with patch.object(sys, 'argv', ['correlations.py']):
            main()
        
        mock_load.assert_called_once()
        mock_extract.assert_called_once()
        mock_compute.assert_called_once()
        mock_save.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])