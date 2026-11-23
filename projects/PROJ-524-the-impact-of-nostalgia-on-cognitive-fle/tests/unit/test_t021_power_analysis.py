"""
Unit tests for T021 power analysis module.

Tests:
- load_cleaned_dataset: verifies file loading
- load_statistical_report: verifies JSON loading
- calculate_power_and_mdes: verifies power and MDES calculations
- run_power_analysis: verifies report update logic
"""

import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from task_t021_power_analysis import (
    calculate_power_and_mdes,
    run_power_analysis
)

class TestCalculatePowerAndMdes:
    """Tests for the calculate_power_and_mdes function."""
    
    def test_calculate_power_and_mdes_basic(self):
        """Test basic power and MDES calculation with known values."""
        group1_n = 50
        group2_n = 52
        effect_size = 0.91  # Large effect
        alpha = 0.05
        
        result = calculate_power_and_mdes(group1_n, group2_n, effect_size, alpha)
        
        assert 'statistical_power' in result
        assert 'minimum_detectable_effect_size' in result
        assert 'alpha' in result
        assert 'sample_size_nostalgia' in result
        assert 'sample_size_control' in result
        
        # Power should be high for large effect size with N=50+
        assert result['statistical_power'] > 0.8
        assert result['statistical_power'] <= 1.0
        
        # MDES should be reasonable for this sample size
        assert result['minimum_detectable_effect_size'] > 0
        assert result['minimum_detectable_effect_size'] < 1.0
        
        assert result['alpha'] == alpha
        assert result['sample_size_nostalgia'] == group1_n
        assert result['sample_size_control'] == group2_n
    
    def test_calculate_power_and_mdes_small_effect(self):
        """Test power calculation with small effect size."""
        group1_n = 50
        group2_n = 52
        effect_size = 0.2  # Small effect
        alpha = 0.05
        
        result = calculate_power_and_mdes(group1_n, group2_n, effect_size, alpha)
        
        # Power should be lower for small effect size
        assert result['statistical_power'] < 0.8
        assert result['statistical_power'] >= 0.0
    
    def test_calculate_power_and_mdes_unequal_groups(self):
        """Test power calculation with unequal group sizes."""
        group1_n = 30
        group2_n = 70
        effect_size = 0.5
        alpha = 0.05
        
        result = calculate_power_and_mdes(group1_n, group2_n, effect_size, alpha)
        
        assert result['statistical_power'] > 0.0
        assert result['statistical_power'] <= 1.0
        assert result['minimum_detectable_effect_size'] > 0
    
    def test_calculate_power_and_mdes_negative_effect_size(self):
        """Test that negative effect sizes are handled correctly (absolute value used)."""
        group1_n = 50
        group2_n = 52
        effect_size = -0.91  # Negative effect
        alpha = 0.05
        
        result = calculate_power_and_mdes(group1_n, group2_n, effect_size, alpha)
        
        # Power should be the same as for positive effect size of same magnitude
        result_positive = calculate_power_and_mdes(group1_n, group2_n, 0.91, alpha)
        assert abs(result['statistical_power'] - result_positive['statistical_power']) < 1e-6
    
    def test_calculate_power_and_mdes_zero_effect_size(self):
        """Test power calculation with zero effect size."""
        group1_n = 50
        group2_n = 52
        effect_size = 0.0
        alpha = 0.05
        
        result = calculate_power_and_mdes(group1_n, group2_n, effect_size, alpha)
        
        # Power should be very low (close to alpha) for zero effect
        assert result['statistical_power'] < 0.1
        assert result['minimum_detectable_effect_size'] > 0

class TestRunPowerAnalysis:
    """Tests for the run_power_analysis function."""
    
    def test_run_power_analysis_updates_report(self):
        """Test that run_power_analysis correctly updates the report with power results."""
        # Create mock report
        mock_report = {
            'comparisons': [
                {
                    'metric': 'perseverative_errors',
                    'group_nostalgia': {'n': 50, 'mean': 12.4, 'std': 3.2},
                    'group_control': {'n': 52, 'mean': 15.8, 'std': 4.1},
                    't_statistic': -4.52,
                    'p_value_raw': 0.000012,
                    'p_value_corrected': 0.000024,
                    'effect_size': {
                        'cohen_d': -0.91,
                        'ci_95_lower': -1.28,
                        'ci_95_upper': -0.54
                    }
                },
                {
                    'metric': 'categories_completed',
                    'group_nostalgia': {'n': 50, 'mean': 5.8, 'std': 1.4},
                    'group_control': {'n': 52, 'mean': 4.9, 'std': 1.6},
                    't_statistic': 3.12,
                    'p_value_raw': 0.0025,
                    'p_value_corrected': 0.005,
                    'effect_size': {
                        'cohen_d': 0.62,
                        'ci_95_lower': 0.24,
                        'ci_95_upper': 1.0
                    }
                }
            ]
        }
        
        # Create mock dataframe (not directly used in calculation)
        mock_df = pd.DataFrame({
            'participant_id': range(102),
            'stimulus_type': ['nostalgia'] * 50 + ['control'] * 52,
            'perseverative_errors': np.random.randn(102),
            'categories_completed': np.random.randn(102),
            'age': [70] * 102
        })
        
        # Run power analysis
        updated_report = run_power_analysis(mock_report, mock_df)
        
        # Verify report structure
        assert 'comparisons' in updated_report
        assert 'summary' in updated_report
        
        # Verify each comparison has power_analysis
        for comp in updated_report['comparisons']:
            assert 'power_analysis' in comp
            assert 'statistical_power' in comp['power_analysis']
            assert 'minimum_detectable_effect_size' in comp['power_analysis']
            assert 'alpha' in comp['power_analysis']
            assert 'sample_size_nostalgia' in comp['power_analysis']
            assert 'sample_size_control' in comp['power_analysis']
        
        # Verify summary statistics
        assert 'total_comparisons' in updated_report['summary']
        assert updated_report['summary']['total_comparisons'] == 2
        assert 'average_power' in updated_report['summary']
        assert 'average_mdes' in updated_report['summary']
        assert 'significant_at_alpha_05' in updated_report['summary']
        assert 'significant_at_alpha_01' in updated_report['summary']
    
    def test_run_power_analysis_counts_significant_results(self):
        """Test that significant results are counted correctly."""
        mock_report = {
            'comparisons': [
                {
                    'metric': 'metric1',
                    'group_nostalgia': {'n': 50},
                    'group_control': {'n': 52},
                    'p_value_corrected': 0.001,  # Significant at 0.05 and 0.01
                    'effect_size': {'cohen_d': 0.8}
                },
                {
                    'metric': 'metric2',
                    'group_nostalgia': {'n': 50},
                    'group_control': {'n': 52},
                    'p_value_corrected': 0.03,  # Significant at 0.05 only
                    'effect_size': {'cohen_d': 0.5}
                },
                {
                    'metric': 'metric3',
                    'group_nostalgia': {'n': 50},
                    'group_control': {'n': 52},
                    'p_value_corrected': 0.1,  # Not significant
                    'effect_size': {'cohen_d': 0.2}
                }
            ]
        }
        
        mock_df = pd.DataFrame({
            'participant_id': range(156),
            'stimulus_type': ['nostalgia'] * 52 + ['control'] * 52 + ['nostalgia'] * 52,
            'score': np.random.randn(156),
            'age': [70] * 156
        })
        
        updated_report = run_power_analysis(mock_report, mock_df)
        
        assert updated_report['summary']['significant_at_alpha_05'] == 2
        assert updated_report['summary']['significant_at_alpha_01'] == 1
    
    def test_run_power_analysis_empty_comparisons(self):
        """Test handling of empty comparisons list."""
        mock_report = {'comparisons': []}
        mock_df = pd.DataFrame()
        
        updated_report = run_power_analysis(mock_report, mock_df)
        
        assert updated_report['summary']['total_comparisons'] == 0
        assert updated_report['summary']['average_power'] == 0.0
        assert updated_report['summary']['average_mdes'] == 0.0
        assert updated_report['summary']['significant_at_alpha_05'] == 0
        assert updated_report['summary']['significant_at_alpha_01'] == 0