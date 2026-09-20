"""
Unit tests for analysis module - AIC model selection logic.
"""
import numpy as np
import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import (
    select_model_aic,
    ModelSelectionResult,
    filter_unresolved_realizations,
    bootstrap_resample,
    compute_bootstrap_statistics,
    compute_scaling_exponent,
    generate_toy_model_data,
    verify_scaling_ansatz
)


class TestAICModelSelection:
    """Tests for AIC-based model selection logic."""

    def test_area_law_selection(self):
        """Test that constant data is correctly identified as Area Law."""
        # Generate constant entropy data (Area Law)
        l_values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        entropy_values = np.ones_like(l_values, dtype=float) * 2.0 + np.random.normal(0, 0.01, len(l_values))

        result = select_model_aic(l_values, entropy_values)

        assert result.best_model == 'area_law', f"Expected 'area_law', got '{result.best_model}'"
        assert 'area_law' in result.aic_scores
        assert result.aic_scores['area_law'] < result.aic_scores['logarithmic']
        assert result.aic_scores['area_law'] < result.aic_scores['volume_law']

    def test_logarithmic_selection(self):
        """Test that logarithmic data is correctly identified."""
        # Generate logarithmic scaling data (Refael-Moore random singlet phase)
        l_values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        # S(l) = (ln 2)/3 * log(l) + c
        true_slope = np.log(2) / 3
        entropy_values = true_slope * np.log(l_values) + 1.0 + np.random.normal(0, 0.02, len(l_values))

        result = select_model_aic(l_values, entropy_values)

        assert result.best_model == 'logarithmic', f"Expected 'logarithmic', got '{result.best_model}'"
        assert 'logarithmic' in result.aic_scores
        assert result.aic_scores['logarithmic'] < result.aic_scores['area_law']
        assert result.aic_scores['logarithmic'] < result.aic_scores['volume_law']

        # Check that the fitted slope is close to the true slope
        fitted_slope, _ = result.coefficients['logarithmic']
        assert abs(fitted_slope - true_slope) < 0.1, f"Fitted slope {fitted_slope} not close to {true_slope}"

    def test_volume_law_selection(self):
        """Test that linear data is correctly identified as Volume Law."""
        # Generate linear scaling data (Volume Law)
        l_values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        # S(l) = 0.5 * l + c
        true_slope = 0.5
        entropy_values = true_slope * l_values + 1.0 + np.random.normal(0, 0.02, len(l_values))

        result = select_model_aic(l_values, entropy_values)

        assert result.best_model == 'volume_law', f"Expected 'volume_law', got '{result.best_model}'"
        assert 'volume_law' in result.aic_scores
        assert result.aic_scores['volume_law'] < result.aic_scores['area_law']
        assert result.aic_scores['volume_law'] < result.aic_scores['logarithmic']

        # Check that the fitted slope is close to the true slope
        fitted_slope, _ = result.coefficients['volume_law']
        assert abs(fitted_slope - true_slope) < 0.1, f"Fitted slope {fitted_slope} not close to {true_slope}"

    def test_aic_scores_exist(self):
        """Test that AIC scores are computed for all models."""
        l_values = np.array([1, 2, 3, 4, 5])
        entropy_values = np.array([1.0, 1.5, 2.0, 2.5, 3.0])

        result = select_model_aic(l_values, entropy_values)

        assert 'area_law' in result.aic_scores
        assert 'logarithmic' in result.aic_scores
        assert 'volume_law' in result.aic_scores
        assert all(isinstance(score, (int, float)) for score in result.aic_scores.values())

    def test_coefficients_structure(self):
        """Test that coefficients have the correct structure."""
        l_values = np.array([1, 2, 3, 4, 5])
        entropy_values = np.array([1.0, 1.5, 2.0, 2.5, 3.0])

        result = select_model_aic(l_values, entropy_values)

        for model in ['area_law', 'logarithmic', 'volume_law']:
            assert model in result.coefficients
            slope, intercept = result.coefficients[model]
            assert isinstance(slope, float)
            assert isinstance(intercept, float)

    def test_r_squared_computed(self):
        """Test that R² values are computed for all models."""
        l_values = np.array([1, 2, 3, 4, 5])
        entropy_values = np.array([1.0, 1.5, 2.0, 2.5, 3.0])

        result = select_model_aic(l_values, entropy_values)

        for model in ['area_law', 'logarithmic', 'volume_law']:
            assert model in result.r_squared
            r2 = result.r_squared[model]
            assert 0 <= r2 <= 1.1, f"R² {r2} out of expected range [0, 1]"

    def test_insufficient_data_points(self):
        """Test that insufficient data points raise an error."""
        l_values = np.array([1, 2])
        entropy_values = np.array([1.0, 2.0])

        with pytest.raises(ValueError, match="At least 3 data points"):
            select_model_aic(l_values, entropy_values)


class TestFilterUnresolvedRealizations:
    """Tests for filtering unresolved realizations."""

    def test_filter_resolved(self):
        """Test that resolved realizations are kept."""
        data = [
            {'id': 1, 'resolved': True},
            {'id': 2, 'resolved': True},
            {'id': 3, 'resolved': False}
        ]

        filtered = filter_unresolved_realizations(data)

        assert len(filtered) == 2
        assert all(r['resolved'] for r in filtered)

    def test_filter_all_resolved(self):
        """Test filtering when all are resolved."""
        data = [
            {'id': 1, 'resolved': True},
            {'id': 2, 'resolved': True}
        ]

        filtered = filter_unresolved_realizations(data)

        assert len(filtered) == 2

    def test_filter_all_unresolved(self):
        """Test filtering when all are unresolved."""
        data = [
            {'id': 1, 'resolved': False},
            {'id': 2, 'resolved': False}
        ]

        filtered = filter_unresolved_realizations(data)

        assert len(filtered) == 0

    def test_filter_missing_key(self):
        """Test filtering when 'resolved' key is missing (defaults to True)."""
        data = [
            {'id': 1},
            {'id': 2, 'resolved': True}
        ]

        filtered = filter_unresolved_realizations(data)

        assert len(filtered) == 2


class TestBootstrapResample:
    """Tests for bootstrap resampling."""

    def test_bootstrap_resample_count(self):
        """Test that the correct number of resamples is generated."""
        l_values = np.array([1, 2, 3, 4, 5])
        entropy_values = np.array([1.0, 1.5, 2.0, 2.5, 3.0])

        resamples = bootstrap_resample(l_values, entropy_values, n_resamples=100, random_seed=42)

        assert len(resamples) == 100
        assert all(len(r) == 5 for r in resamples)

    def test_bootstrap_resample_values(self):
        """Test that resampled values are from the original set."""
        l_values = np.array([1, 2, 3, 4, 5])
        entropy_values = np.array([1.0, 1.5, 2.0, 2.5, 3.0])

        resamples = bootstrap_resample(l_values, entropy_values, n_resamples=10, random_seed=42)

        for resample in resamples:
            assert all(val in entropy_values for val in resample)

    def test_bootstrap_reproducibility(self):
        """Test that bootstrap is reproducible with the same seed."""
        l_values = np.array([1, 2, 3, 4, 5])
        entropy_values = np.array([1.0, 1.5, 2.0, 2.5, 3.0])

        resamples1 = bootstrap_resample(l_values, entropy_values, n_resamples=10, random_seed=42)
        resamples2 = bootstrap_resample(l_values, entropy_values, n_resamples=10, random_seed=42)

        assert all(np.array_equal(r1, r2) for r1, r2 in zip(resamples1, resamples2))


class TestBootstrapStatistics:
    """Tests for bootstrap statistics computation."""

    def test_statistics_keys(self):
        """Test that all expected keys are present in statistics."""
        l_values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        entropy_values = np.log(l_values) + np.random.normal(0, 0.1, len(l_values))

        stats_dict = compute_bootstrap_statistics(l_values, entropy_values, n_resamples=50, random_seed=42)

        expected_keys = ['mean', 'std', 'ci_lower', 'ci_upper', 'p_value', 'n_resamples']
        assert all(key in stats_dict for key in expected_keys)

    def test_statistics_values(self):
        """Test that statistics values are reasonable."""
        l_values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        entropy_values = np.log(l_values) + np.random.normal(0, 0.1, len(l_values))

        stats_dict = compute_bootstrap_statistics(l_values, entropy_values, n_resamples=50, random_seed=42)

        assert isinstance(stats_dict['mean'], float)
        assert isinstance(stats_dict['std'], float)
        assert stats_dict['std'] >= 0
        assert stats_dict['ci_lower'] <= stats_dict['mean'] <= stats_dict['ci_upper']
        assert 0 <= stats_dict['p_value'] <= 1
        assert stats_dict['n_resamples'] == 50


class TestScalingExponent:
    """Tests for scaling exponent computation."""

    def test_compute_scaling_exponent(self):
        """Test that scaling exponent is computed correctly."""
        l_values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        entropy_values = np.log(l_values) + np.random.normal(0, 0.1, len(l_values))

        alpha, intercept = compute_scaling_exponent(l_values, entropy_values)

        assert isinstance(alpha, float)
        assert isinstance(intercept, float)

    def test_scaling_exponent_logarithmic(self):
        """Test scaling exponent for logarithmic data."""
        l_values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        true_slope = np.log(2) / 3
        entropy_values = true_slope * np.log(l_values) + 1.0 + np.random.normal(0, 0.02, len(l_values))

        alpha, _ = compute_scaling_exponent(l_values, entropy_values)

        assert abs(alpha - true_slope) < 0.1


class TestToyModelData:
    """Tests for toy model data generation."""

    def test_toy_model_data_shape(self):
        """Test that toy model data has correct shape."""
        l_values, entropy_values = generate_toy_model_data(L=10, n_points=5)

        assert len(l_values) == 5
        assert len(entropy_values) == 5
        assert all(l_values >= 1)
        assert all(l_values < 10)

    def test_toy_model_data_values(self):
        """Test that toy model data follows logarithmic scaling."""
        l_values, entropy_values = generate_toy_model_data(L=10, n_points=5)

        # Check that entropy increases with l (logarithmic scaling)
        assert np.all(np.diff(entropy_values) > 0)


class TestVerifyScalingAnsatz:
    """Tests for scaling ansatz verification."""

    def test_verify_scaling_ansatz_keys(self):
        """Test that all expected keys are present in verification result."""
        l_values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        entropy_values = np.log(l_values) + np.random.normal(0, 0.1, len(l_values))

        result = verify_scaling_ansatz(l_values, entropy_values)

        expected_keys = ['best_model', 'aic_scores', 'delta_aic', 'coefficients', 'r_squared']
        assert all(key in result for key in expected_keys)

    def test_verify_scaling_ansatz_delta_aic(self):
        """Test that delta AIC is computed correctly."""
        l_values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        entropy_values = np.log(l_values) + np.random.normal(0, 0.1, len(l_values))

        result = verify_scaling_ansatz(l_values, entropy_values)

        # The best model should have delta_aic = 0
        best_model = result['best_model']
        assert abs(result['delta_aic'][best_model]) < 1e-10

        # Other models should have positive delta_aic
        for model, delta in result['delta_aic'].items():
            if model != best_model:
                assert delta > 0
