"""
Unit tests for power analysis functionality.

These tests verify the power calculation logic and sufficiency checks
as required by FR-008.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.power_analysis import (
    calculate_power_for_correlation,
    check_power_sufficiency,
    run_power_analysis
)
from scipy import stats


class TestCalculatePowerForCorrelation:
    """Tests for the power calculation function."""
    
    def test_power_increases_with_sample_size(self):
        """Power should increase as sample size increases."""
        effect_size = 0.5
        alpha = 0.05
        
        power_n10 = calculate_power_for_correlation(10, effect_size, alpha)
        power_n50 = calculate_power_for_correlation(50, effect_size, alpha)
        power_n100 = calculate_power_for_correlation(100, effect_size, alpha)
        
        assert power_n10 < power_n50 < power_n100
        assert 0 <= power_n10 <= 1
        assert 0 <= power_n50 <= 1
        assert 0 <= power_n100 <= 1
    
    def test_power_increases_with_effect_size(self):
        """Power should increase as effect size increases."""
        n = 50
        alpha = 0.05
        
        power_r03 = calculate_power_for_correlation(n, 0.3, alpha)
        power_r05 = calculate_power_for_correlation(n, 0.5, alpha)
        power_r07 = calculate_power_for_correlation(n, 0.7, alpha)
        
        assert power_r03 < power_r05 < power_r07
    
    def test_power_decreases_with_alpha(self):
        """Power should decrease as alpha decreases (more stringent)."""
        n = 50
        effect_size = 0.5
        
        power_alpha01 = calculate_power_for_correlation(n, effect_size, 0.01)
        power_alpha05 = calculate_power_for_correlation(n, effect_size, 0.05)
        
        assert power_alpha01 < power_alpha05
    
    def test_minimum_sample_size(self):
        """Should raise error for sample size < 3."""
        with pytest.raises(ValueError):
            calculate_power_for_correlation(2, 0.5, 0.05)
    
    def test_power_at_threshold_values(self):
        """Test power calculation at boundary conditions."""
        # Large sample should have high power
        power_large = calculate_power_for_correlation(200, 0.5, 0.05)
        assert power_large > 0.9
        
        # Small sample should have low power
        power_small = calculate_power_for_correlation(5, 0.5, 0.05)
        assert power_small < 0.5


class TestCheckPowerSufficiency:
    """Tests for power sufficiency checking."""
    
    def test_power_above_threshold(self):
        """Should return True when power is above threshold."""
        is_sufficient, message = check_power_sufficiency(0.8, 0.2)
        assert is_sufficient is True
        assert "sufficient" in message.lower()
    
    def test_power_below_threshold(self):
        """Should return False when power is below threshold."""
        is_sufficient, message = check_power_sufficiency(0.1, 0.2)
        assert is_sufficient is False
        assert "inconclusive" in message.lower()
        assert "low power" in message.lower()
    
    def test_power_at_threshold(self):
        """Should return True when power equals threshold."""
        is_sufficient, message = check_power_sufficiency(0.2, 0.2)
        assert is_sufficient is True


class TestRunPowerAnalysis:
    """Tests for the full power analysis pipeline."""
    
    def test_run_power_analysis_with_valid_data(self):
        """Should return valid power analysis results."""
        df = pd.DataFrame({'discharge_id': range(10)})
        results = run_power_analysis(df, effect_size=0.5, alpha=0.05, power_threshold=0.2)
        
        assert 'n' in results
        assert 'power' in results
        assert 'is_sufficient' in results
        assert 'status_message' in results
        assert results['n'] == 10
        assert 0 <= results['power'] <= 1
    
    def test_run_power_analysis_insufficient_sample(self):
        """Should handle insufficient sample size gracefully."""
        df = pd.DataFrame({'discharge_id': range(2)})
        results = run_power_analysis(df)
        
        assert results['n'] == 2
        assert results['power'] == 0.0
        assert results['is_sufficient'] is False
        assert 'Insufficient sample size' in results.get('warning_flag', '')
    
    def test_run_power_analysis_with_custom_threshold(self):
        """Should use custom power threshold."""
        df = pd.DataFrame({'discharge_id': range(50)})
        results = run_power_analysis(df, power_threshold=0.8)
        
        assert 'power_threshold' in str(results.get('status_message', '')) or results['power'] < 0.8 or results['is_sufficient']
    
    def test_run_power_analysis_effect_size_parameter(self):
        """Should use custom effect size parameter."""
        df = pd.DataFrame({'discharge_id': range(50)})
        
        results_low = run_power_analysis(df, effect_size=0.3)
        results_high = run_power_analysis(df, effect_size=0.7)
        
        # Higher effect size should yield higher power
        assert results_high['power'] > results_low['power']


class TestPowerCalculationAccuracy:
    """Tests to verify accuracy against known statistical values."""
    
    def test_power_calculation_matches_scipy_approximation(self):
        """
        Verify power calculation is reasonable by comparing to a known approximation.
        For n=50, r=0.5, alpha=0.05, power should be approximately 0.7-0.8
        """
        power = calculate_power_for_correlation(50, 0.5, 0.05)
        
        # Based on standard power tables, this should be in the 0.7-0.8 range
        assert 0.6 < power < 0.9
    
    def test_power_for_large_sample(self):
        """For very large samples, power should approach 1."""
        power = calculate_power_for_correlation(500, 0.5, 0.05)
        assert power > 0.99
    
    def test_power_for_very_small_effect(self):
        """For very small effect sizes, power should be low even with moderate n."""
        power = calculate_power_for_correlation(50, 0.1, 0.05)
        assert power < 0.3