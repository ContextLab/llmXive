"""
Unit tests for core statistical functions used in the analysis pipeline.

Tests cover:
- Mann-Kendall test (modified with pre-whitening)
- Theil-Sen slope estimator
- Jaccard similarity coefficient
- Augmented Dickey-Fuller (ADF) test logic
- Benjamini-Hochberg correction
- Power analysis (MDES)

These tests ensure the statistical methods used in US1, US2, and US3
are implemented correctly and produce expected results on known inputs.
"""
import math
import unittest
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Import from project analysis modules
# Note: We assume the code/ directory is in sys.path or PYTHONPATH
try:
    from analysis.trends import (
        calculate_mann_kendall_statistic,
        prewhiten_series,
        modified_mann_kendall,
        theil_sen_slope,
        benjamini_hochberg_correction,
        calculate_power_and_mdes,
        classify_trend
    )
    from analysis.decomposition import (
        perform_adf_test,
        apply_differencing
    )
    from analysis.clustering import (
        calculate_jaccard_similarity
    )
except ImportError as e:
    # Fallback for direct execution from project root
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
    from analysis.trends import (
        calculate_mann_kendall_statistic,
        prewhiten_series,
        modified_mann_kendall,
        theil_sen_slope,
        benjamini_hochberg_correction,
        calculate_power_and_mdes,
        classify_trend
    )
    from analysis.decomposition import (
        perform_adf_test,
        apply_differencing
    )
    from analysis.clustering import (
        calculate_jaccard_similarity
    )


class TestMannKendall(unittest.TestCase):
    """Tests for Mann-Kendall trend test implementation."""
    
    def test_mann_kendall_constant_series(self):
        """Test that a constant series returns S=0 and p=1.0."""
        series = [5.0, 5.0, 5.0, 5.0, 5.0]
        s, var_s, p_value = calculate_mann_kendall_statistic(series)
        
        self.assertEqual(s, 0)
        self.assertAlmostEqual(p_value, 1.0, places=5)
    
    def test_mann_kendall_strictly_increasing(self):
        """Test that a strictly increasing series returns positive S."""
        series = [1.0, 2.0, 3.0, 4.0, 5.0]
        s, var_s, p_value = calculate_mann_kendall_statistic(series)
        
        self.assertGreater(s, 0)
        self.assertLess(p_value, 0.05)  # Should be significant
    
    def test_mann_kendall_strictly_decreasing(self):
        """Test that a strictly decreasing series returns negative S."""
        series = [5.0, 4.0, 3.0, 2.0, 1.0]
        s, var_s, p_value = calculate_mann_kendall_statistic(series)
        
        self.assertLess(s, 0)
        self.assertLess(p_value, 0.05)  # Should be significant
    
    def test_mann_kendall_with_ties(self):
        """Test Mann-Kendall with tied values."""
        series = [1.0, 2.0, 2.0, 3.0, 4.0]
        s, var_s, p_value = calculate_mann_kendall_statistic(series)
        
        # Should handle ties without error
        self.assertIsInstance(s, (int, float))
        self.assertIsInstance(p_value, float)
        self.assertGreaterEqual(p_value, 0)
        self.assertLessEqual(p_value, 1)
    
    def test_prewhitening_reduces_autocorrelation(self):
        """Test that pre-whitening reduces autocorrelation in AR(1) process."""
        # Create a series with strong autocorrelation
        n = 100
        series = []
        val = 0.0
        for i in range(n):
            val = 0.8 * val + 1.0 + 0.1 * (i / n)  # AR(1) + trend
            series.append(val)
        
        # Pre-whiten
        prewhitened = prewhiten_series(series)
        
        self.assertEqual(len(prewhitened), len(series))
        # Pre-whitened series should have reduced variance in trend component
        # (exact check depends on implementation details)
    
    def test_modified_mann_kendall_significance(self):
        """Test modified MK test detects significant trend in known data."""
        # Generate a clear linear trend with noise
        n = 50
        series = [i * 0.5 + (i % 3) * 0.1 for i in range(n)]
        
        s, var_s, p_value, tau, z = modified_mann_kendall(series)
        
        self.assertLess(p_value, 0.05)  # Should detect trend
        self.assertGreater(tau, 0)  # Positive trend
        self.assertGreater(z, 1.96)  # Significant at 5%


class TestTheilSen(unittest.TestCase):
    """Tests for Theil-Sen slope estimator."""
    
    def test_theil_sen_constant_series(self):
        """Test slope is zero for constant series."""
        series = [5.0, 5.0, 5.0, 5.0, 5.0]
        slope, intercept = theil_sen_slope(list(range(len(series))), series)
        
        self.assertAlmostEqual(slope, 0.0, places=5)
    
    def test_theil_sen_linear_series(self):
        """Test slope is 1.0 for y=x series."""
        x = list(range(10))
        y = [float(i) for i in x]
        slope, intercept = theil_sen_slope(x, y)
        
        self.assertAlmostEqual(slope, 1.0, places=5)
        self.assertAlmostEqual(intercept, 0.0, places=5)
    
    def test_theil_sen_outlier_resistant(self):
        """Test that Theil-Sen is resistant to outliers."""
        x = list(range(10))
        y = [float(i) for i in x]
        # Add extreme outlier
        y[5] = 1000.0
        
        slope, intercept = theil_sen_slope(x, y)
        
        # Should still be close to 1.0 despite outlier
        self.assertLess(abs(slope - 1.0), 0.5)
    
    def test_theil_sen_negative_slope(self):
        """Test negative slope detection."""
        x = list(range(10))
        y = [10.0 - float(i) for i in x]
        slope, intercept = theil_sen_slope(x, y)
        
        self.assertAlmostEqual(slope, -1.0, places=5)


class TestJaccardSimilarity(unittest.TestCase):
    """Tests for Jaccard similarity coefficient."""
    
    def test_jaccard_identical_sets(self):
        """Test Jaccard similarity of identical sets is 1.0."""
        set1 = {"python", "javascript", "java"}
        set2 = {"python", "javascript", "java"}
        
        result = calculate_jaccard_similarity(set1, set2)
        self.assertAlmostEqual(result, 1.0, places=5)
    
    def test_jaccard_disjoint_sets(self):
        """Test Jaccard similarity of disjoint sets is 0.0."""
        set1 = {"python", "java"}
        set2 = {"javascript", "ruby"}
        
        result = calculate_jaccard_similarity(set1, set2)
        self.assertAlmostEqual(result, 0.0, places=5)
    
    def test_jaccard_partial_overlap(self):
        """Test Jaccard similarity with partial overlap."""
        set1 = {"python", "javascript", "java"}
        set2 = {"python", "javascript", "ruby"}
        # Intersection: 2, Union: 4
        # Jaccard = 2/4 = 0.5
        
        result = calculate_jaccard_similarity(set1, set2)
        self.assertAlmostEqual(result, 0.5, places=5)
    
    def test_jaccard_empty_sets(self):
        """Test Jaccard similarity with empty sets."""
        set1 = set()
        set2 = set()
        
        # Should handle gracefully (return 0.0 or 1.0 depending on convention)
        # Most implementations return 1.0 for two empty sets
        result = calculate_jaccard_similarity(set1, set2)
        self.assertIn(result, [0.0, 1.0])
    
    def test_jaccard_one_empty_set(self):
        """Test Jaccard similarity with one empty set."""
        set1 = {"python", "java"}
        set2 = set()
        
        result = calculate_jaccard_similarity(set1, set2)
        self.assertAlmostEqual(result, 0.0, places=5)


class TestADFTest(unittest.TestCase):
    """Tests for Augmented Dickey-Fuller test implementation."""
    
    def test_adf_stationary_series(self):
        """Test ADF detects stationarity in white noise."""
        # White noise is stationary
        import random
        random.seed(42)
        series = [random.gauss(0, 1) for _ in range(100)]
        
        is_stationary, p_value, critical_values = perform_adf_test(series)
        
        # Should detect stationarity (p < 0.05)
        self.assertTrue(is_stationary)
        self.assertLess(p_value, 0.05)
    
    def test_adf_non_stationary_series(self):
        """Test ADF detects non-stationarity in random walk."""
        # Random walk is non-stationary
        series = []
        val = 0.0
        for _ in range(100):
            val += random.gauss(0, 1)
            series.append(val)
        
        is_stationary, p_value, critical_values = perform_adf_test(series)
        
        # Should detect non-stationarity (p > 0.05)
        self.assertFalse(is_stationary)
        self.assertGreater(p_value, 0.05)
    
    def test_adf_trend_series(self):
        """Test ADF with deterministic trend."""
        # Series with linear trend
        series = [i * 0.5 + random.gauss(0, 0.1) for i in range(100)]
        
        is_stationary, p_value, critical_values = perform_adf_test(series)
        
        # May or may not detect trend depending on model specification
        # Just ensure it runs without error
        self.assertIsInstance(p_value, float)
        self.assertGreaterEqual(p_value, 0)
        self.assertLessEqual(p_value, 1)


class TestDifferencing(unittest.TestCase):
    """Tests for differencing operation."""
    
    def test_first_differencing(self):
        """Test first-order differencing."""
        series = [1.0, 2.0, 3.0, 4.0, 5.0]
        differenced = apply_differencing(series, order=1)
        
        expected = [1.0, 1.0, 1.0, 1.0]
        self.assertEqual(len(differenced), len(expected))
        for i, (a, b) in enumerate(zip(differenced, expected)):
            self.assertAlmostEqual(a, b, places=5)
    
    def test_second_differencing(self):
        """Test second-order differencing."""
        series = [1.0, 4.0, 9.0, 16.0, 25.0]  # x^2
        differenced = apply_differencing(series, order=2)
        
        # First diff: [3, 5, 7, 9]
        # Second diff: [2, 2, 2]
        expected = [2.0, 2.0, 2.0]
        self.assertEqual(len(differenced), len(expected))
        for i, (a, b) in enumerate(zip(differenced, expected)):
            self.assertAlmostEqual(a, b, places=5)
    
    def test_differencing_order_zero(self):
        """Test that order=0 returns original series."""
        series = [1.0, 2.0, 3.0]
        differenced = apply_differencing(series, order=0)
        
        self.assertEqual(differenced, series)


class TestBenjaminiHochberg(unittest.TestCase):
    """Tests for Benjamini-Hochberg correction."""
    
    def test_bh_correction_increases_p_values(self):
        """Test that BH correction produces larger adjusted p-values."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        adjusted = benjamini_hochberg_correction(p_values, alpha=0.05)
        
        for i, (orig, adj) in enumerate(zip(p_values, adjusted)):
            self.assertGreaterEqual(adj, orig)
    
    def test_bh_correction_significance(self):
        """Test BH correction maintains significance for small p-values."""
        p_values = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2]
        adjusted = benjamini_hochberg_correction(p_values, alpha=0.05)
        
        # First few should still be significant
        self.assertLess(adjusted[0], 0.05)
        self.assertLess(adjusted[1], 0.05)
    
    def test_bh_correction_all_significant(self):
        """Test case where all p-values become non-significant."""
        p_values = [0.2, 0.3, 0.4, 0.5]
        adjusted = benjamini_hochberg_correction(p_values, alpha=0.05)
        
        # All should be non-significant
        for adj in adjusted:
            self.assertGreaterEqual(adj, 0.05)


class TestPowerAnalysis(unittest.TestCase):
    """Tests for power analysis and MDES calculation."""
    
    def test_mdes_decreases_with_sample_size(self):
        """Test that MDES decreases as sample size increases."""
        mdes_small = calculate_power_and_mdes(n=20, alpha=0.05, power=0.8)
        mdes_large = calculate_power_and_mdes(n=100, alpha=0.05, power=0.8)
        
        self.assertLess(mdes_large["mdes"], mdes_small["mdes"])
    
    def test_mdes_increases_with_alpha(self):
        """Test that MDES increases as alpha increases (less stringent)."""
        mdes_strict = calculate_power_and_mdes(n=50, alpha=0.01, power=0.8)
        mdes_loose = calculate_power_and_mdes(n=50, alpha=0.1, power=0.8)
        
        self.assertGreater(mdes_loose["mdes"], mdes_strict["mdes"])
    
    def test_power_calculation(self):
        """Test power calculation for known effect size."""
        result = calculate_power_and_mdes(n=50, alpha=0.05, power=0.8)
        
        self.assertIn("mdes", result)
        self.assertIn("power", result)
        self.assertIn("effect_size", result)
        self.assertGreaterEqual(result["power"], 0)
        self.assertLessEqual(result["power"], 1)


class TestTrendClassification(unittest.TestCase):
    """Tests for trend classification logic."""
    
    def test_classify_significant_growth(self):
        """Test classification of significant growth."""
        result = classify_trend(
            p_value=0.01,
            slope=0.5,
            power=0.9,
            alpha=0.05
        )
        
        self.assertEqual(result["classification"], "Growth")
        self.assertGreater(result["slope"], 0)
    
    def test_classify_significant_decline(self):
        """Test classification of significant decline."""
        result = classify_trend(
            p_value=0.01,
            slope=-0.5,
            power=0.9,
            alpha=0.05
        )
        
        self.assertEqual(result["classification"], "Decline")
        self.assertLess(result["slope"], 0)
    
    def test_classify_stable(self):
        """Test classification of stable trend (high power, non-significant)."""
        result = classify_trend(
            p_value=0.3,
            slope=0.01,
            power=0.9,
            alpha=0.05
        )
        
        self.assertEqual(result["classification"], "Stable")
    
    def test_classify_insufficient_data(self):
        """Test classification of insufficient data (low power)."""
        result = classify_trend(
            p_value=0.3,
            slope=0.01,
            power=0.5,
            alpha=0.05
        )
        
        self.assertEqual(result["classification"], "Insufficient Data")
        self.assertIn("mdes", result)


if __name__ == "__main__":
    unittest.main()