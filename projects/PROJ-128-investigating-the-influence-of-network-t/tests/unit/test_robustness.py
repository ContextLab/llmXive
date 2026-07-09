import os
import sys
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import get_config_dict
from analysis.robustness import calculate_sensitivity_metrics

class TestSensitivityAnalysisLogic:
    """Unit tests for sensitivity analysis logic in robustness.py"""

    def setup_method(self):
        """Setup test fixtures"""
        self.config = get_config_dict()
        
        # Create mock correlation results with baseline (30 TR) and sensitivity (20 TR) data
        self.mock_correlation_data = pd.DataFrame({
            'metric_pair': ['efficiency-clustering', 'modularity-dwell_time', 'clustering-states'],
            'r_baseline': [0.65, 0.42, 0.78],
            'p_baseline': [0.001, 0.012, 0.0005],
            'r_sensitivity': [0.61, 0.45, 0.72],
            'p_sensitivity': [0.002, 0.009, 0.001],
            'fdr_corrected': [True, False, True]
        })

    def test_calculate_sensitivity_metrics_computes_absolute_difference(self):
        """Test that absolute difference between 30 TR and 20 TR correlation coefficients is calculated"""
        result = calculate_sensitivity_metrics(self.mock_correlation_data)
        
        assert 'absolute_difference' in result.columns
        assert len(result) == len(self.mock_correlation_data)
        
        # Verify the absolute difference calculation
        expected_diff_0 = abs(0.65 - 0.61)
        expected_diff_1 = abs(0.42 - 0.45)
        expected_diff_2 = abs(0.78 - 0.72)
        
        assert abs(result.iloc[0]['absolute_difference'] - expected_diff_0) < 1e-6
        assert abs(result.iloc[1]['absolute_difference'] - expected_diff_1) < 1e-6
        assert abs(result.iloc[2]['absolute_difference'] - expected_diff_2) < 1e-6

    def test_calculate_sensitivity_metrics_identifies_significant_changes(self):
        """Test that significant changes are identified based on threshold"""
        result = calculate_sensitivity_metrics(self.mock_correlation_data)
        
        assert 'significant_change' in result.columns
        
        # All differences should be flagged as True or False based on threshold
        assert all(result['significant_change'].isin([True, False]))

    def test_calculate_sensitivity_metrics_handles_empty_dataframe(self):
        """Test behavior with empty input dataframe"""
        empty_df = pd.DataFrame(columns=['metric_pair', 'r_baseline', 'r_sensitivity'])
        result = calculate_sensitivity_metrics(empty_df)
        
        assert len(result) == 0
        assert 'absolute_difference' in result.columns

    def test_calculate_sensitivity_metrics_preserves_original_columns(self):
        """Test that original columns are preserved in output"""
        result = calculate_sensitivity_metrics(self.mock_correlation_data)
        
        original_columns = ['metric_pair', 'r_baseline', 'p_baseline', 'r_sensitivity', 
                          'p_sensitivity', 'fdr_corrected']
        
        for col in original_columns:
            assert col in result.columns

    def test_calculate_sensitivity_metrics_adds_expected_columns(self):
        """Test that expected new columns are added"""
        result = calculate_sensitivity_metrics(self.mock_correlation_data)
        
        expected_new_columns = ['absolute_difference', 'significant_change']
        
        for col in expected_new_columns:
            assert col in result.columns

    def test_sensitivity_analysis_with_identical_values(self):
        """Test when baseline and sensitivity values are identical"""
        mock_data_identical = self.mock_correlation_data.copy()
        mock_data_identical['r_sensitivity'] = mock_data_identical['r_baseline']
        
        result = calculate_sensitivity_metrics(mock_data_identical)
        
        # Absolute difference should be zero for all
        assert all(result['absolute_difference'] == 0.0)

    def test_sensitivity_analysis_with_large_differences(self):
        """Test with large differences between baseline and sensitivity"""
        mock_data_large_diff = self.mock_correlation_data.copy()
        mock_data_large_diff['r_sensitivity'] = mock_data_large_diff['r_baseline'] + 0.3
        
        result = calculate_sensitivity_metrics(mock_data_large_diff)
        
        # All should show significant changes
        assert all(result['significant_change'] == True)

    def test_integration_with_config_threshold(self):
        """Test that the sensitivity threshold from config is used"""
        # This test verifies that the function respects the config threshold
        # In a real scenario, we would mock the config to return a specific threshold
        with patch('analysis.robustness.get_config_dict') as mock_config:
            mock_config.return_value = {
                'sensitivity_threshold': 0.1,
                'baseline_window': 30,
                'sensitivity_window': 20
            }
            
            result = calculate_sensitivity_metrics(self.mock_correlation_data)
            
            # Verify that the threshold is applied correctly
            # With threshold 0.1, differences >= 0.1 should be True
            expected_significance = result['absolute_difference'] >= 0.1
            pd.testing.assert_series_equal(result['significant_change'], expected_significance)

    def test_output_dataframe_structure(self):
        """Test that output dataframe has correct structure"""
        result = calculate_sensitivity_metrics(self.mock_correlation_data)
        
        # Check data types
        assert result['absolute_difference'].dtype in [np.float64, np.float32]
        assert result['significant_change'].dtype == bool
        assert result['metric_pair'].dtype == object

    def test_no_nan_values_in_output(self):
        """Test that output doesn't contain NaN values for valid inputs"""
        result = calculate_sensitivity_metrics(self.mock_correlation_data)
        
        assert not result.isnull().any().any()

    def test_edge_case_single_row(self):
        """Test with single row dataframe"""
        single_row_df = self.mock_correlation_data.iloc[[0]].copy()
        result = calculate_sensitivity_metrics(single_row_df)
        
        assert len(result) == 1
        assert 'absolute_difference' in result.columns
        assert abs(result.iloc[0]['absolute_difference'] - 0.04) < 1e-6

    def test_negative_correlation_values(self):
        """Test with negative correlation values"""
        mock_negative = self.mock_correlation_data.copy()
        mock_negative['r_baseline'] = [-0.5, -0.3, -0.8]
        mock_negative['r_sensitivity'] = [-0.45, -0.35, -0.75]
        
        result = calculate_sensitivity_metrics(mock_negative)
        
        # Verify absolute differences are calculated correctly for negative values
        expected_diff_0 = abs(-0.5 - (-0.45))
        assert abs(result.iloc[0]['absolute_difference'] - expected_diff_0) < 1e-6