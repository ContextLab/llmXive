import pytest
import numpy as np
from code.stats import CorrelationAnalyzer, run_post_hoc_power_analysis
from code.utils import DataAvailabilityError

class TestPostHocPowerAnalysis:
    """Tests for T030: Post-hoc Power Analysis implementation."""

    def test_power_analysis_initialization(self):
        """Test that CorrelationAnalyzer initializes correctly."""
        analyzer = CorrelationAnalyzer(alpha=0.01)
        assert analyzer.alpha == 0.01

    def test_insufficient_samples_flag(self):
        """Test that N < 20 triggers a power flag and warning."""
        # Create synthetic data with N < 20
        n_samples = 10
        x = np.random.randn(n_samples, 2)
        y = np.random.randn(n_samples)
        metric_names = ['metric1', 'metric2']

        analyzer = CorrelationAnalyzer()
        results = analyzer.calculate_correlations(x, y, metric_names)

        assert results['n_samples'] == n_samples
        assert results['power_analysis']['power_flag'] is True
        assert any("below the recommended threshold of 20" in w for w in results['power_analysis']['warnings'])

    def test_power_analysis_with_sufficient_samples(self):
        """Test power analysis with N >= 20."""
        n_samples = 50
        # Create data with a known correlation
        x = np.random.randn(n_samples, 2)
        y = x[:, 0] * 0.5 + np.random.randn(n_samples) * 0.5
        metric_names = ['metric1', 'metric2']

        analyzer = CorrelationAnalyzer()
        results = analyzer.calculate_correlations(x, y, metric_names)

        assert results['n_samples'] == n_samples
        # Check that MDES and observed power are calculated (not NaN)
        assert len(results['power_analysis']['minimum_detectable_effect_size']) == 2
        assert len(results['power_analysis']['observed_power']) == 2

    def test_mdes_calculation(self):
        """Test that minimum detectable effect size is a valid float between 0 and 1."""
        n_samples = 100
        x = np.random.randn(n_samples, 1)
        y = x[:, 0] * 0.3 + np.random.randn(n_samples)
        metric_names = ['metric1']

        analyzer = CorrelationAnalyzer()
        results = analyzer.calculate_correlations(x, y, metric_names)

        mdes = results['power_analysis']['minimum_detectable_effect_size'][0]
        assert not np.isnan(mdes)
        assert 0.0 <= mdes <= 1.0

    def test_observed_power_calculation(self):
        """Test that observed power is calculated correctly."""
        n_samples = 100
        x = np.random.randn(n_samples, 1)
        y = x[:, 0] * 0.3 + np.random.randn(n_samples)
        metric_names = ['metric1']

        analyzer = CorrelationAnalyzer()
        results = analyzer.calculate_correlations(x, y, metric_names)

        power = results['power_analysis']['observed_power'][0]
        assert not np.isnan(power)
        assert 0.0 <= power <= 1.0

    def test_bonferroni_correction_integration(self):
        """Test that power analysis uses Bonferroni-corrected alpha."""
        n_samples = 50
        x = np.random.randn(n_samples, 5)  # 5 metrics
        y = np.random.randn(n_samples)
        metric_names = [f'metric{i}' for i in range(5)]

        analyzer = CorrelationAnalyzer(alpha=0.05)
        results = analyzer.calculate_correlations(x, y, metric_names)

        # Corrected alpha should be 0.05 / 5 = 0.01
        assert results['corrected_alpha'] == 0.01

    def test_convenience_function(self):
        """Test the standalone run_post_hoc_power_analysis function."""
        result = run_post_hoc_power_analysis(n_samples=30, observed_r=0.4, alpha=0.05, n_tests=1)

        assert 'minimum_detectable_effect_size' in result
        assert 'observed_power' in result
        assert not np.isnan(result['minimum_detectable_effect_size'])
        assert not np.isnan(result['observed_power'])

    def test_convenience_function_small_n(self):
        """Test convenience function with N < 20."""
        result = run_post_hoc_power_analysis(n_samples=10, observed_r=0.4, alpha=0.05, n_tests=1)

        assert result['warning'] is not None
        assert "N=10 < 20" in result['warning']

    def test_nan_handling(self):
        """Test that NaN correlations are handled gracefully."""
        n_samples = 50
        x = np.random.randn(n_samples, 2)
        x[0, 0] = np.nan  # Introduce NaN
        y = np.random.randn(n_samples)
        metric_names = ['metric1', 'metric2']

        analyzer = CorrelationAnalyzer()
        results = analyzer.calculate_correlations(x, y, metric_names)

        # The first metric should have NaN results
        assert np.isnan(results['pearson_r'][0]) or results['power_analysis']['minimum_detectable_effect_size'][0] == np.nan

    def test_edge_case_n_equals_1(self):
        """Test behavior when N=1 (should return empty/NaN results)."""
        x = np.array([[1.0]])
        y = np.array([2.0])
        metric_names = ['metric1']

        analyzer = CorrelationAnalyzer()
        results = analyzer.calculate_correlations(x, y, metric_names)

        assert results['n_samples'] == 1
        # Should return empty results or NaN for correlations
        assert results['pearson_r'] == [] or all(np.isnan(r) for r in results['pearson_r'])
