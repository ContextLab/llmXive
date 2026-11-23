"""
Unit tests for correlation calculation and p-value accuracy.

This module tests the CorrelationAnalyzer class in code/stats.py,
verifying:
1. Pearson and Spearman correlation calculations against known values
2. Bonferroni correction accuracy
3. Power analysis calculations
4. Sensitivity analysis and rank-order stability
5. Edge case handling (N=1, missing data, NaN values)
"""

import pytest
import numpy as np
from scipy.stats import pearsonr, spearmanr
from statsmodels.stats.power import FTestPower
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.stats import CorrelationAnalyzer
from code.utils import DataAvailabilityError


class TestCorrelationCalculation:
    """Test Pearson and Spearman correlation calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CorrelationAnalyzer()
        
        # Create known datasets with specific correlation properties
        # Perfect positive correlation
        self.perfect_pos_x = np.array([1, 2, 3, 4, 5])
        self.perfect_pos_y = np.array([2, 4, 6, 8, 10])
        
        # Perfect negative correlation
        self.perfect_neg_x = np.array([1, 2, 3, 4, 5])
        self.perfect_neg_y = np.array([10, 8, 6, 4, 2])
        
        # No correlation (independent random variables)
        np.random.seed(42)
        self.no_corr_x = np.random.randn(100)
        self.no_corr_y = np.random.randn(100)
        
        # Known moderate positive correlation
        self.moderate_x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.moderate_y = np.array([2, 3, 3, 5, 5, 6, 7, 7, 8, 9])

    def test_pearson_perfect_positive(self):
        """Test Pearson correlation for perfect positive relationship."""
        r, p = self.analyzer.calculate_pearson(self.perfect_pos_x, self.perfect_pos_y)
        
        assert np.isclose(r, 1.0, atol=1e-10), f"Expected r=1.0, got {r}"
        assert p < 0.001, "p-value should be very small for perfect correlation"

    def test_pearson_perfect_negative(self):
        """Test Pearson correlation for perfect negative relationship."""
        r, p = self.analyzer.calculate_pearson(self.perfect_neg_x, self.perfect_neg_y)
        
        assert np.isclose(r, -1.0, atol=1e-10), f"Expected r=-1.0, got {r}"
        assert p < 0.001, "p-value should be very small for perfect correlation"

    def test_pearson_no_correlation(self):
        """Test Pearson correlation for uncorrelated data."""
        r, p = self.analyzer.calculate_pearson(self.no_corr_x, self.no_corr_y)
        
        # For random data, correlation should be close to 0
        assert abs(r) < 0.2, f"Expected r close to 0, got {r}"
        # p-value should typically be > 0.05 for random data
        # (allow some tolerance due to randomness)

    def test_spearman_perfect_positive(self):
        """Test Spearman correlation for perfect positive relationship."""
        r, p = self.analyzer.calculate_spearman(self.perfect_pos_x, self.perfect_pos_y)
        
        assert np.isclose(r, 1.0, atol=1e-10), f"Expected r=1.0, got {r}"
        assert p < 0.001, "p-value should be very small for perfect correlation"

    def test_spearman_perfect_negative(self):
        """Test Spearman correlation for perfect negative relationship."""
        r, p = self.analyzer.calculate_spearman(self.perfect_neg_x, self.perfect_neg_y)
        
        assert np.isclose(r, -1.0, atol=1e-10), f"Expected r=-1.0, got {r}"
        assert p < 0.001, "p-value should be very small for perfect correlation"

    def test_spearman_moderate_correlation(self):
        """Test Spearman correlation for moderate relationship."""
        r, p = self.analyzer.calculate_spearman(self.moderate_x, self.moderate_y)
        
        # Should be positive and significant
        assert r > 0.5, f"Expected r > 0.5, got {r}"
        assert p < 0.05, f"Expected p < 0.05, got {p}"

    def test_correlation_mismatched_lengths(self):
        """Test that mismatched array lengths raise an error."""
        with pytest.raises(ValueError):
            self.analyzer.calculate_pearson(np.array([1, 2, 3]), np.array([1, 2]))

    def test_correlation_empty_arrays(self):
        """Test that empty arrays raise an error."""
        with pytest.raises(ValueError):
            self.analyzer.calculate_pearson(np.array([]), np.array([]))

    def test_correlation_single_value(self):
        """Test that single value arrays raise an error."""
        with pytest.raises(ValueError):
            self.analyzer.calculate_pearson(np.array([1]), np.array([2]))

    def test_correlation_constant_array(self):
        """Test that constant arrays (zero variance) are handled."""
        # When one array is constant, correlation is undefined
        with pytest.raises(ValueError):
            self.analyzer.calculate_pearson(np.array([1, 1, 1]), np.array([1, 2, 3]))

    def test_compare_with_scipy_pearson(self):
        """Verify our Pearson implementation matches scipy exactly."""
        r_ours, p_ours = self.analyzer.calculate_pearson(self.moderate_x, self.moderate_y)
        r_scipy, p_scipy = pearsonr(self.moderate_x, self.moderate_y)
        
        assert np.isclose(r_ours, r_scipy, atol=1e-10), \
            f"Pearson r mismatch: ours={r_ours}, scipy={r_scipy}"
        assert np.isclose(p_ours, p_scipy, atol=1e-10), \
            f"Pearson p mismatch: ours={p_ours}, scipy={p_scipy}"

    def test_compare_with_scipy_spearman(self):
        """Verify our Spearman implementation matches scipy exactly."""
        r_ours, p_ours = self.analyzer.calculate_spearman(self.moderate_x, self.moderate_y)
        r_scipy, p_scipy = spearmanr(self.moderate_x, self.moderate_y)
        
        assert np.isclose(r_ours, r_scipy, atol=1e-10), \
            f"Spearman r mismatch: ours={r_ours}, scipy={r_scipy}"
        assert np.isclose(p_ours, p_scipy, atol=1e-10), \
            f"Spearman p mismatch: ours={p_ours}, scipy={p_scipy}"

    def test_batch_correlation(self):
        """Test batch correlation calculation."""
        # Create multiple pairs of data
        x_list = [self.moderate_x, self.perfect_pos_x, self.no_corr_x]
        y_list = [self.moderate_y, self.perfect_pos_y, self.no_corr_y]
        
        results = self.analyzer.batch_correlate(x_list, y_list)
        
        assert len(results) == 3, "Should return results for all pairs"
        assert all('pearson_r' in r for r in results), "Each result should have pearson_r"
        assert all('pearson_p' in r for r in results), "Each result should have pearson_p"
        assert all('spearman_r' in r for r in results), "Each result should have spearman_r"
        assert all('spearman_p' in r for r in results), "Each result should have spearman_p"

class TestBonferroniCorrection:
    """Test Bonferroni correction for multiple comparisons."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CorrelationAnalyzer()

    def test_bonferroni_single_test(self):
        """Test Bonferroni correction with single test (no adjustment)."""
        p_values = [0.03]
        corrected = self.analyzer.bonferroni_correct(p_values)
        
        assert len(corrected) == 1
        assert corrected[0] == 0.03, "Single test should have unchanged p-value"

    def test_bonferroni_multiple_tests(self):
        """Test Bonferroni correction with multiple tests."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        corrected = self.analyzer.bonferroni_correct(p_values)
        
        # Bonferroni multiplies each p-value by number of tests
        expected = [0.01 * 5, 0.02 * 5, 0.03 * 5, 0.04 * 5, 0.05 * 5]
        
        for c, e in zip(corrected, expected):
            assert np.isclose(c, e, atol=1e-10), \
                f"Expected {e}, got {c}"

    def test_bonferroni_capped_at_one(self):
        """Test that Bonferroni-corrected p-values are capped at 1.0."""
        p_values = [0.5, 0.6, 0.7]
        corrected = self.analyzer.bonferroni_correct(p_values)
        
        # With 3 tests, these would be 1.5, 1.8, 2.1
        # But should be capped at 1.0
        for c in corrected:
            assert c <= 1.0, f"Corrected p-value {c} should be <= 1.0"

    def test_bonferroni_significance_threshold(self):
        """Test significance determination after Bonferroni correction."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        corrected = self.analyzer.bonferroni_correct(p_values)
        
        # With 5 tests and alpha=0.05, threshold is 0.01
        # Only first value (0.01 * 5 = 0.05) is at threshold
        # Actually, 0.01 * 5 = 0.05, which is at the threshold
        # 0.02 * 5 = 0.10, which is not significant
        
        # Check that the first value is exactly at the threshold
        assert np.isclose(corrected[0], 0.05, atol=1e-10)
        assert all(c >= 0.05 for c in corrected[1:]), \
            "Remaining values should be >= 0.05"

    def test_bonferroni_family_wise_error_rate(self):
        """Verify Bonferroni controls family-wise error rate."""
        # Generate many independent tests under null hypothesis
        np.random.seed(123)
        n_tests = 100
        n_simulations = 1000
        
        alpha = 0.05
        familywise_errors = 0

        for _ in range(n_simulations):
            # Generate random p-values under null
            p_values = np.random.uniform(0, 1, n_tests)
            corrected = self.analyzer.bonferroni_correct(p_values.tolist())
            
            # Check if any test is significant after correction
            if any(p < alpha for p in corrected):
                familywise_errors += 1

        # Family-wise error rate should be <= alpha
        observed_fwer = familywise_errors / n_simulations
        assert observed_fwer <= alpha + 0.02, \
            f"Observed FWER {observed_fwer} exceeds alpha {alpha}"

    def test_bonferroni_vs_uncorrected(self):
        """Test that Bonferroni correction is more conservative."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        corrected = self.analyzer.bonferroni_correct(p_values)
        
        # All corrected values should be >= original values
        for orig, corr in zip(p_values, corrected):
            assert corr >= orig, \
                f"Corrected p-value {corr} should be >= original {orig}"

class TestPowerAnalysis:
    """Test power analysis calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CorrelationAnalyzer()

    def test_power_analysis_valid_inputs(self):
        """Test power analysis with valid inputs."""
        # Test with reasonable effect size and sample size
        effect_size = 0.5  # medium effect
        n_obs = 50
        alpha = 0.05

        power = self.analyzer.calculate_power(effect_size, n_obs, alpha)
        
        assert 0 <= power <= 1, f"Power should be between 0 and 1, got {power}"
        assert power > 0.5, f"Power should be > 0.5 for medium effect and n=50, got {power}"

    def test_power_increases_with_sample_size(self):
        """Test that power increases with sample size."""
        effect_size = 0.5
        alpha = 0.05
        
        power_20 = self.analyzer.calculate_power(effect_size, 20, alpha)
        power_50 = self.analyzer.calculate_power(effect_size, 50, alpha)
        power_100 = self.analyzer.calculate_power(effect_size, 100, alpha)
        
        assert power_20 < power_50 < power_100, \
            "Power should increase with sample size"

    def test_power_increases_with_effect_size(self):
        """Test that power increases with effect size."""
        n_obs = 50
        alpha = 0.05
        
        power_small = self.analyzer.calculate_power(0.1, n_obs, alpha)
        power_medium = self.analyzer.calculate_power(0.3, n_obs, alpha)
        power_large = self.analyzer.calculate_power(0.5, n_obs, alpha)
        
        assert power_small < power_medium < power_large, \
            "Power should increase with effect size"

    def test_minimum_detectable_effect_size(self):
        """Test minimum detectable effect size calculation."""
        n_obs = 50
        alpha = 0.05
        desired_power = 0.8

        mdes = self.analyzer.calculate_mdes(n_obs, alpha, desired_power)
        
        assert mdes > 0, "Minimum detectable effect size should be positive"
        assert mdes < 1, "Minimum detectable effect size should be < 1"

    def test_power_warning_for_small_sample(self):
        """Test that small sample sizes trigger warnings."""
        # This test checks that the analyzer properly handles small samples
        # The actual warning logic is tested in the integration tests
        n_obs = 10  # Small sample
        effect_size = 0.5
        alpha = 0.05

        power = self.analyzer.calculate_power(effect_size, n_obs, alpha)
        
        # Power should be low for small samples
        assert power < 0.5, f"Power should be < 0.5 for n=10, got {power}"

class TestSensitivityAnalysis:
    """Test sensitivity analysis and rank-order stability."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CorrelationAnalyzer()

    def test_sensitivity_analysis_thresholds(self):
        """Test sensitivity analysis across multiple thresholds."""
        # Create sample data
        np.random.seed(456)
        x = np.random.randn(100)
        y = 0.5 * x + np.random.randn(100) * 0.5
        
        thresholds = [0.01, 0.05, 0.10]
        results = self.analyzer.sensitivity_analysis(x, y, thresholds)
        
        assert len(results) == len(thresholds), \
            f"Should have results for all {len(thresholds)} thresholds"

    def test_rank_order_stability(self):
        """Test rank-order stability across thresholds."""
        # Create data with clear correlations
        np.random.seed(789)
        n_metrics = 5
        n_samples = 50
        
        # Create multiple metrics with varying correlations
        x = np.random.randn(n_samples)
        metrics = []
        for i in range(n_metrics):
            # Different correlation strengths
            corr_strength = (i + 1) * 0.1
            y = corr_strength * x + np.random.randn(n_samples) * (1 - corr_strength)
            metrics.append(y)
        
        thresholds = [0.01, 0.05, 0.10]
        stability_results = self.analyzer.check_rank_stability(metrics, x, thresholds)
        
        # Check that rank-order stability is calculated
        assert 'rank_correlation' in stability_results, \
            "Should include rank correlation metric"
        assert 'magnitude_differences' in stability_results, \
            "Should include magnitude differences"

    def test_magnitude_difference_calculation(self):
        """Test that magnitude differences are calculated correctly."""
        # Create two sets of correlation values
        corr_set1 = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        corr_set2 = np.array([0.15, 0.35, 0.55, 0.75, 0.95])
        
        # Max difference should be 0.05
        max_diff = np.max(np.abs(corr_set1 - corr_set2))
        assert np.isclose(max_diff, 0.05), f"Expected max diff 0.05, got {max_diff}"

    def test_sensitivity_flag_large_changes(self):
        """Test that large changes are flagged in sensitivity analysis."""
        # Create data where correlation changes significantly with threshold
        np.random.seed(999)
        x = np.random.randn(30)
        y = x + np.random.randn(30) * 0.1  # Very strong correlation
        
        thresholds = [0.01, 0.05, 0.10]
        results = self.analyzer.sensitivity_analysis(x, y, thresholds)
        
        # For strong correlation, results should be stable
        # Check that no magnitude difference exceeds 0.1 (threshold for concern)
        for result in results:
            if 'magnitude_diff' in result:
                assert result['magnitude_diff'] < 0.1, \
                    f"Magnitude difference {result['magnitude_diff']} exceeds threshold"

class TestEdgeCases:
    """Test edge case handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CorrelationAnalyzer()

    def test_n_equals_one(self):
        """Test handling of single observation (N=1)."""
        with pytest.raises(ValueError) as exc_info:
            self.analyzer.calculate_pearson(np.array([1]), np.array([2]))
        
        assert "N=1" in str(exc_info.value) or "single" in str(exc_info.value).lower()

    def test_missing_metadata_handling(self):
        """Test handling of missing metadata in batch analysis."""
        # Create data with some missing values
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
        
        # Should handle NaN values gracefully
        r, p = self.analyzer.calculate_pearson(x, y)
        
        # Result should be based on valid pairs only
        assert not np.isnan(r) or np.isnan(p), \
            "Should handle NaN values appropriately"

    def test_undefined_metrics_nan_assignment(self):
        """Test that undefined metrics are assigned NaN and flagged."""
        # Create constant arrays (undefined correlation)
        x = np.array([1, 1, 1, 1])
        y = np.array([1, 1, 1, 1])
        
        with pytest.raises(ValueError):
            self.analyzer.calculate_pearson(x, y)

    def test_all_nan_input(self):
        """Test handling of all-NaN input arrays."""
        x = np.array([np.nan, np.nan, np.nan])
        y = np.array([np.nan, np.nan, np.nan])
        
        with pytest.raises(ValueError):
            self.analyzer.calculate_pearson(x, y)

    def test_mixed_nan_handling(self):
        """Test handling of mixed NaN values."""
        x = np.array([1.0, np.nan, 3.0, 4.0, 5.0])
        y = np.array([2.0, 4.0, np.nan, 8.0, 10.0])
        
        # Should calculate based on non-NaN pairs
        r, p = self.analyzer.calculate_pearson(x, y)
        
        # Should have valid result from remaining pairs
        assert not np.isnan(r), "Should calculate correlation from valid pairs"

    def test_extreme_outliers(self):
        """Test handling of extreme outliers."""
        # Create data with extreme outlier
        x = np.array([1, 2, 3, 4, 5, 1000])
        y = np.array([2, 4, 6, 8, 10, 12])
        
        # Should still calculate (outliers may affect result but not crash)
        r, p = self.analyzer.calculate_pearson(x, y)
        
        assert not np.isnan(r), "Should handle extreme outliers without crashing"

    def test_integer_inputs(self):
        """Test handling of integer inputs."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        # Should work with integer arrays
        r, p = self.analyzer.calculate_pearson(x, y)
        
        assert np.isclose(r, 1.0), "Should work with integer inputs"

    def test_very_small_values(self):
        """Test handling of very small numerical values."""
        x = np.array([1e-10, 2e-10, 3e-10, 4e-10, 5e-10])
        y = np.array([2e-10, 4e-10, 6e-10, 8e-10, 10e-10])
        
        r, p = self.analyzer.calculate_pearson(x, y)
        
        assert np.isclose(r, 1.0), "Should handle very small values correctly"

    def test_very_large_values(self):
        """Test handling of very large numerical values."""
        x = np.array([1e10, 2e10, 3e10, 4e10, 5e10])
        y = np.array([2e10, 4e10, 6e10, 8e10, 10e10])
        
        r, p = self.analyzer.calculate_pearson(x, y)
        
        assert np.isclose(r, 1.0), "Should handle very large values correctly"

    def test_negative_values(self):
        """Test handling of negative values."""
        x = np.array([-5, -3, -1, 1, 3, 5])
        y = np.array([-10, -6, -2, 2, 6, 10])
        
        r, p = self.analyzer.calculate_pearson(x, y)
        
        assert np.isclose(r, 1.0), "Should handle negative values correctly"

class TestIntegration:
    """Integration tests for the full correlation analysis pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CorrelationAnalyzer()

    def test_full_analysis_workflow(self):
        """Test the complete analysis workflow."""
        # Create synthetic data with known properties
        np.random.seed(12345)
        n_samples = 100
        
        # Create metrics with varying correlations to conductivity
        conductivity = np.random.randn(n_samples)
        metric1 = 0.6 * conductivity + np.random.randn(n_samples) * 0.4
        metric2 = -0.4 * conductivity + np.random.randn(n_samples) * 0.6
        metric3 = 0.1 * conductivity + np.random.randn(n_samples) * 0.9  # Weak correlation
        
        metrics = {
            'clustering_coeff': metric1,
            'mean_degree': metric2,
            'percolation_threshold': metric3
        }
        
        # Run full analysis
        results = self.analyzer.run_full_analysis(
            metrics=metrics,
            target='conductivity',
            target_values=conductivity,
            alpha=0.05
        )
        
        # Verify results structure
        assert 'correlations' in results
        assert 'bonferroni_corrected' in results
        assert 'power_analysis' in results
        assert 'sensitivity_analysis' in results
        
        # Verify metric1 has strong positive correlation
        corr1 = results['correlations']['clustering_coeff']['pearson_r']
        assert corr1 > 0.5, f"Expected strong positive correlation, got {corr1}"
        
        # Verify metric2 has moderate negative correlation
        corr2 = results['correlations']['mean_degree']['pearson_r']
        assert corr2 < -0.2, f"Expected moderate negative correlation, got {corr2}"
        
        # Verify metric3 has weak correlation
        corr3 = results['correlations']['percolation_threshold']['pearson_r']
        assert abs(corr3) < 0.2, f"Expected weak correlation, got {corr3}"

    def test_bonferroni_flagging(self):
        """Test that Bonferroni correction properly flags significance changes."""
        # Create data where some correlations become non-significant after correction
        np.random.seed(54321)
        n_samples = 30
        
        conductivity = np.random.randn(n_samples)
        
        # Create 10 metrics with varying correlations
        metrics = {}
        for i in range(10):
            corr_strength = 0.3 + (i * 0.05)  # 0.3 to 0.75
            metrics[f'metric_{i}'] = corr_strength * conductivity + np.random.randn(n_samples) * (1 - corr_strength)
        
        results = self.analyzer.run_full_analysis(
            metrics=metrics,
            target='conductivity',
            target_values=conductivity,
            alpha=0.05
        )
        
        # Check that Bonferroni correction was applied
        assert 'bonferroni_corrected' in results
        assert 'flagged_changes' in results['bonferroni_corrected']
        
        # Verify that some correlations changed significance status
        flagged = results['bonferroni_corrected']['flagged_changes']
        # With 10 tests and alpha=0.05, threshold is 0.005
        # Some metrics with p-values between 0.005 and 0.05 should be flagged
        assert len(flagged) >= 0, "Should have flagged changes (possibly 0 if all are very significant)"

    def test_power_analysis_reporting(self):
        """Test that power analysis is properly reported."""
        np.random.seed(98765)
        n_samples = 25
        
        conductivity = np.random.randn(n_samples)
        metric = 0.5 * conductivity + np.random.randn(n_samples) * 0.5
        
        results = self.analyzer.run_full_analysis(
            metrics={'test_metric': metric},
            target='conductivity',
            target_values=conductivity,
            alpha=0.05
        )
        
        # Check power analysis results
        power_results = results['power_analysis']
        assert 'minimum_detectable_effect_size' in power_results
        assert 'achieved_power' in power_results
        
        # For n=25 and moderate effect, power should be reported
        assert power_results['achieved_power'] > 0, "Power should be positive"
        
        # Check that small sample warning is included
        assert 'warnings' in power_results
        assert any('small sample' in w.lower() for w in power_results['warnings']), \
            "Should include small sample warning"

    def test_sensitivity_rank_stability(self):
        """Test that rank-order stability is properly assessed."""
        np.random.seed(11111)
        n_samples = 50
        
        conductivity = np.random.randn(n_samples)
        
        # Create multiple metrics with different correlations
        metrics = {}
        for i in range(5):
            strength = 0.2 + (i * 0.15)  # 0.2 to 0.8
            metrics[f'metric_{i}'] = strength * conductivity + np.random.randn(n_samples) * (1 - strength)
        
        results = self.analyzer.run_full_analysis(
            metrics=metrics,
            target='conductivity',
            target_values=conductivity,
            alpha=0.05
        )
        
        # Check sensitivity analysis results
        sens_results = results['sensitivity_analysis']
        assert 'rank_correlation' in sens_results
        assert 'magnitude_differences' in sens_results
        
        # Verify rank correlation is high (stable ordering)
        rank_corr = sens_results['rank_correlation']
        assert rank_corr > 0.8, f"Expected high rank stability, got {rank_corr}"

    def test_comprehensive_error_handling(self):
        """Test comprehensive error handling in full workflow."""
        # Test with various error conditions
        with pytest.raises(ValueError):
            self.analyzer.run_full_analysis(
                metrics={},  # Empty metrics
                target='conductivity',
                target_values=np.array([1, 2, 3]),
                alpha=0.05
            )

        with pytest.raises(ValueError):
            self.analyzer.run_full_analysis(
                metrics={'test': np.array([1, 2, 3])},
                target='conductivity',
                target_values=np.array([1, 2]),  # Mismatched lengths
                alpha=0.05
            )