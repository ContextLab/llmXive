import pytest
import json
import os
import sys
from pathlib import Path
import numpy as np
from scipy import stats

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from diagnostics import run_sensitivity_analysis, calculate_power

class TestSensitivityAnalysis:
    """Unit tests for sensitivity analysis functionality."""

    def test_sensitivity_analysis_empty_results(self):
        """Test sensitivity analysis with empty correlation results."""
        results = run_sensitivity_analysis({})
        assert results['status'] == 'ERROR'
        assert 'stability_status' in results

    def test_sensitivity_analysis_no_correlations(self):
        """Test sensitivity analysis with empty correlation list."""
        results = run_sensitivity_analysis({'correlations': []})
        assert results['status'] == 'PASS'
        assert results['stability_status'] == 'STABLE'

    def test_sensitivity_analysis_all_significant(self):
        """Test sensitivity analysis where all correlations are significant at all thresholds."""
        correlations = [
            {'p_value': 0.001, 'correlation': 0.5},
            {'p_value': 0.002, 'correlation': 0.6},
            {'p_value': 0.003, 'correlation': 0.4}
        ]
        
        results = run_sensitivity_analysis({'correlations': correlations})
        
        assert results['status'] == 'PASS'
        assert results['stability_status'] == 'STABLE'  # All thresholds have 100% significance
        assert 'thresholds' in results
        assert '0.01' in results['thresholds']
        assert results['thresholds']['0.01']['percentage_significant'] == 100.0

    def test_sensitivity_analysis_mixed_significance(self):
        """Test sensitivity analysis with mixed significance levels."""
        correlations = [
            {'p_value': 0.005, 'correlation': 0.7},  # Significant at all thresholds
            {'p_value': 0.02, 'correlation': 0.5},   # Significant at 0.05, 0.10
            {'p_value': 0.08, 'correlation': 0.3},   # Significant at 0.10 only
            {'p_value': 0.20, 'correlation': 0.1}    # Not significant
        ]
        
        results = run_sensitivity_analysis({'correlations': correlations})
        
        assert results['status'] == 'PASS'
        assert 'thresholds' in results
        assert 'percentage_changes' in results
        assert 'stability_status' in results

    def test_sensitivity_analysis_stability_threshold(self):
        """Test that stability status correctly identifies stable vs unstable results."""
        # Create data with minimal change (should be STABLE)
        correlations_stable = [
            {'p_value': 0.001 * i, 'correlation': 0.5} for i in range(1, 11)
        ]
        
        results_stable = run_sensitivity_analysis({'correlations': correlations_stable})
        assert results_stable['stability_status'] == 'STABLE'

    def test_sensitivity_analysis_output_structure(self):
        """Test that output contains all required fields."""
        correlations = [
            {'p_value': 0.03, 'correlation': 0.4},
            {'p_value': 0.07, 'correlation': 0.3}
        ]
        
        results = run_sensitivity_analysis({'correlations': correlations})
        
        required_fields = ['status', 'thresholds', 'stability_status', 'stability_threshold']
        for field in required_fields:
            assert field in results, f"Missing required field: {field}"

class TestPowerAnalysis:
    """Unit tests for power analysis functionality."""

    def test_power_analysis_basic(self):
        """Test basic power analysis calculation."""
        results = calculate_power({'correlations': []})
        
        assert results['status'] == 'PASS'
        assert 'minimum_sample_size' in results
        assert results['minimum_sample_size'] > 0
        assert results['effect_size'] == 0.3
        assert results['alpha'] == 0.05
        assert results['target_power'] == 0.80

    def test_power_analysis_with_data_source(self):
        """Test power analysis includes data source type."""
        results = calculate_power({'correlations': [], 'data_source_type': 'synthetic'})
        
        assert results['data_source_type'] == 'synthetic'

    def test_power_analysis_calculation_reasonableness(self):
        """Test that calculated sample size is reasonable for typical effect sizes."""
        results = calculate_power({}, effect_size=0.3)
        
        # For r=0.3, alpha=0.05, power=0.80, n should be around 85-90
        assert 70 <= results['minimum_sample_size'] <= 110, f"Sample size {results['minimum_sample_size']} seems unreasonable"

    def test_power_analysis_smaller_effect_requires_larger_n(self):
        """Test that smaller effect sizes require larger sample sizes."""
        results_large = calculate_power({}, effect_size=0.5)
        results_small = calculate_power({}, effect_size=0.2)
        
        assert results_small['minimum_sample_size'] > results_large['minimum_sample_size']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
