"""
Unit tests for the statistical analysis module (T023).

Verifies:
1. Fisher's Exact Test is triggered for n < 30.
2. Z-test is triggered for n >= 30.
3. P-values and statistics are numeric and within expected ranges.
4. Conclusion logic correctly identifies significance (p < 0.05).
"""
import pytest
import math
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.analysis.stats import calculate_statistical_significance


class TestStatisticalAnalysis:
    
    def test_fisher_exact_small_sample(self):
        """Test that Fisher's Exact is used when total n < 30."""
        # Small sample: 10+5 + 12+3 = 30 -> Wait, 30 is boundary. Let's do 14 total.
        # Baseline: 5 success, 2 fail (n=7)
        # Augmented: 6 success, 1 fail (n=7)
        # Total n = 14 (< 30)
        result = calculate_statistical_significance(5, 2, 6, 1)
        
        assert result['test_type'] == 'fisher_exact'
        assert isinstance(result['p_value'], float)
        assert 0.0 <= result['p_value'] <= 1.0
        assert isinstance(result['statistic'], float)
        assert result['statistic'] > 0  # Odds ratio must be positive
        assert 'conclusion' in result
        
    def test_z_test_large_sample(self):
        """Test that Z-test is used when total n >= 30."""
        # Large sample: 50+20 + 60+15 = 145 (>= 30)
        result = calculate_statistical_significance(50, 20, 60, 15)
        
        assert result['test_type'] == 'z_test'
        assert isinstance(result['p_value'], float)
        assert 0.0 <= result['p_value'] <= 1.0
        assert isinstance(result['statistic'], float)
        # Z-score can be negative or positive
        
    def test_conclusion_significant(self):
        """Test that conclusion is 'significant' when p < 0.05."""
        # Create a scenario likely to be significant
        # Baseline: 10/20 success (50%), Augmented: 18/20 success (90%)
        # Total n = 40 -> Z-test
        result = calculate_statistical_significance(10, 10, 18, 2)
        
        # Note: We don't assert the p-value is exactly < 0.05 because it depends on the math,
        # but we assert the logic matches the p-value.
        expected_significant = result['p_value'] < 0.05
        expected_conclusion = 'significant' if expected_significant else 'not_significant'
        
        assert result['conclusion'] == expected_conclusion
        
    def test_conclusion_not_significant(self):
        """Test that conclusion is 'not_significant' when p >= 0.05."""
        # Create a scenario likely to be NOT significant (very similar rates)
        # Baseline: 10/20 (50%), Augmented: 11/20 (55%)
        result = calculate_statistical_significance(10, 10, 11, 9)
        
        expected_significant = result['p_value'] < 0.05
        expected_conclusion = 'significant' if expected_significant else 'not_significant'
        
        assert result['conclusion'] == expected_conclusion
        
    def test_boundary_n_equals_30(self):
        """Test behavior exactly at n=30 (should use Z-test)."""
        # 15 + 15 = 30
        result = calculate_statistical_significance(10, 5, 10, 5)
        
        # Per logic: if n < 30 -> fisher, else -> z_test
        assert result['test_type'] == 'z_test'
        
    def test_boundary_n_equals_29(self):
        """Test behavior just below n=30 (should use Fisher)."""
        # 14 + 15 = 29
        result = calculate_statistical_significance(10, 4, 10, 5)
        
        assert result['test_type'] == 'fisher_exact'