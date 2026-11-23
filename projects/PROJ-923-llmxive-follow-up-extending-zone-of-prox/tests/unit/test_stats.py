import pytest
import numpy as np
from pathlib import Path
import sys

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.stats import paired_ttest_aucc, calculate_statistical_significance

class TestPairedTTest:
    """Unit tests for paired t-test implementation in stats.py"""

    def test_identical_arrays(self):
        """Test that identical arrays result in p-value of 1.0"""
        baseline = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        cap = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        
        t_stat, p_value, std_baseline, std_cap = paired_ttest_aucc(baseline, cap)
        
        assert p_value == 1.0, f"Expected p_value=1.0 for identical arrays, got {p_value}"
        assert t_stat == 0.0, f"Expected t_stat=0.0 for identical arrays, got {t_stat}"

    def test_significant_difference(self):
        """Test detection of significant difference between arrays"""
        # Baseline: low performance
        baseline = np.array([0.3, 0.35, 0.32, 0.33, 0.31])
        # CAP: high performance
        cap = np.array([0.8, 0.85, 0.82, 0.83, 0.81])
        
        t_stat, p_value, std_baseline, std_cap = paired_ttest_aucc(baseline, cap)
        
        assert p_value < 0.05, f"Expected p_value < 0.05 for significant difference, got {p_value}"
        assert t_stat > 0, f"Expected positive t_stat when CAP > baseline, got {t_stat}"

    def test_no_significant_difference(self):
        """Test that small random differences are not significant"""
        np.random.seed(42)
        baseline = np.random.normal(0.5, 0.05, 100)
        cap = np.random.normal(0.5, 0.05, 100)
        
        t_stat, p_value, std_baseline, std_cap = paired_ttest_aucc(baseline, cap)
        
        assert p_value > 0.05, f"Expected p_value > 0.05 for random noise, got {p_value}"

    def test_single_element_arrays(self):
        """Test behavior with single element arrays (edge case)"""
        baseline = np.array([0.5])
        cap = np.array([0.6])
        
        t_stat, p_value, std_baseline, std_cap = paired_ttest_aucc(baseline, cap)
        
        # With n=1, std is 0, which causes division by zero in t-test
        # The implementation should handle this gracefully
        assert p_value is not None or t_stat is None, "Should handle single element arrays"

    def test_mismatched_lengths(self):
        """Test that mismatched array lengths raise an error"""
        baseline = np.array([0.5, 0.6, 0.7])
        cap = np.array([0.8, 0.9])
        
        with pytest.raises(ValueError):
            paired_ttest_aucc(baseline, cap)

    def test_empty_arrays(self):
        """Test that empty arrays raise an error"""
        baseline = np.array([])
        cap = np.array([])
        
        with pytest.raises(ValueError):
            paired_ttest_aucc(baseline, cap)

    def test_std_calculation(self):
        """Test that standard deviations are calculated correctly"""
        baseline = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        cap = np.array([0.6, 0.7, 0.8, 0.9, 1.0])
        
        t_stat, p_value, std_baseline, std_cap = paired_ttest_aucc(baseline, cap)
        
        expected_std_baseline = np.std(baseline, ddof=1)
        expected_std_cap = np.std(cap, ddof=1)
        
        assert np.isclose(std_baseline, expected_std_baseline), \
            f"Expected std_baseline={expected_std_baseline}, got {std_baseline}"
        assert np.isclose(std_cap, expected_std_cap), \
            f"Expected std_cap={expected_std_cap}, got {std_cap}"

class TestStatisticalSignificance:
    """Unit tests for statistical significance classification"""

    def test_significant_positive(self):
        """Test classification of significant positive difference"""
        t_stat, p_value = 3.5, 0.001
        result = calculate_statistical_significance(t_stat, p_value)
        
        assert result["is_significant"] is True
        assert result["direction"] == "positive"
        assert result["p_value"] == 0.001

    def test_significant_negative(self):
        """Test classification of significant negative difference"""
        t_stat, p_value = -3.5, 0.001
        result = calculate_statistical_significance(t_stat, p_value)
        
        assert result["is_significant"] is True
        assert result["direction"] == "negative"
        assert result["p_value"] == 0.001

    def test_not_significant(self):
        """Test classification of non-significant difference"""
        t_stat, p_value = 0.5, 0.6
        result = calculate_statistical_significance(t_stat, p_value)
        
        assert result["is_significant"] is False
        assert result["direction"] == "none"
        assert result["p_value"] == 0.6

    def test_alpha_threshold(self):
        """Test that p-value exactly at alpha threshold is not significant"""
        t_stat, p_value = 1.96, 0.05
        result = calculate_statistical_significance(t_stat, p_value)
        
        assert result["is_significant"] is False  # p > alpha (strict inequality)
        assert result["direction"] == "none"

class TestIntegration:
    """Integration tests combining multiple functions"""

    def test_full_workflow(self):
        """Test complete workflow from data to significance report"""
        np.random.seed(123)
        
        # Simulate 10 runs with different seeds
        baseline_aucc = np.random.normal(0.55, 0.03, 10)
        cap_aucc = np.random.normal(0.62, 0.03, 10)
        
        t_stat, p_value, std_baseline, std_cap = paired_ttest_aucc(baseline_aucc, cap_aucc)
        significance = calculate_statistical_significance(t_stat, p_value)
        
        assert significance["is_significant"] is True
        assert significance["direction"] == "positive"
        assert p_value < 0.05
        assert np.isclose(std_baseline, np.std(baseline_aucc, ddof=1))
        assert np.isclose(std_cap, np.std(cap_aucc, ddof=1))

    def test_edge_case_all_zeros(self):
        """Test with all zero values"""
        baseline = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        cap = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        
        t_stat, p_value, std_baseline, std_cap = paired_ttest_aucc(baseline, cap)
        
        assert p_value == 1.0
        assert t_stat == 0.0
        assert std_baseline == 0.0
        assert std_cap == 0.0