"""
Unit tests for validation utilities in code/analysis/validation.py.

Tests cover:
- Uncertainty scaling to 90% CI
- Bias checking against catalog uncertainties
- Injected data scenario validation
"""

import pytest
import numpy as np
from code.analysis.validation import (
    scale_uncertainty_to_90_ci,
    scale_catalog_uncertainties,
    check_bias_against_catalog_ci,
    validate_injected_data_scenario
)


class TestUncertaintyScaling:
    """Tests for uncertainty scaling functions."""

    def test_scale_1sigma_to_90ci_basic(self):
        """Test basic 1-sigma to 90% CI scaling."""
        sigma = 1.0
        expected = 1.0 * 1.645
        result = scale_uncertainty_to_90_ci(sigma)
        assert np.isclose(result, expected)

    def test_scale_1sigma_to_90ci_small_value(self):
        """Test scaling with small uncertainty values."""
        sigma = 0.001
        result = scale_uncertainty_to_90_ci(sigma)
        expected = 0.001 * 1.645
        assert np.isclose(result, expected)

    def test_scale_1sigma_invalid_values(self):
        """Test that invalid uncertainty values raise errors."""
        with pytest.raises(ValueError):
            scale_uncertainty_to_90_ci(0.0)

        with pytest.raises(ValueError):
            scale_uncertainty_to_90_ci(-1.0)

        with pytest.raises(ValueError):
            scale_uncertainty_to_90_ci(np.nan)

    def test_scale_catalog_uncertainties(self):
        """Test scaling of catalog parameter uncertainties."""
        catalog = {
            'mass_1': 30.0,
            'mass_1_err': 1.0,
            'chi_eff': 0.0,
            'chi_eff_err': 0.1
        }
        scaled = scale_catalog_uncertainties(catalog)

        assert scaled['mass_1'] == 30.0
        assert np.isclose(scaled['mass_1_err'], 1.645)
        assert scaled['chi_eff'] == 0.0
        assert np.isclose(scaled['chi_eff_err'], 0.1645)


class TestBiasChecking:
    """Tests for bias checking against catalog uncertainties."""

    def test_bias_within_threshold(self):
        """Test bias that is within the catalog uncertainty threshold."""
        biases = {'mass_1': 0.5, 'chi_eff': 0.05}
        uncertainties = {'mass_1_err': 1.645, 'chi_eff_err': 0.1645}

        result = check_bias_against_catalog_ci(biases, uncertainties)

        assert result['mass_1'] is False
        assert result['chi_eff'] is False

    def test_bias_exceeds_threshold(self):
        """Test bias that exceeds the catalog uncertainty threshold."""
        biases = {'mass_1': 2.0, 'chi_eff': 0.2}
        uncertainties = {'mass_1_err': 1.645, 'chi_eff_err': 0.1645}

        result = check_bias_against_catalog_ci(biases, uncertainties)

        assert result['mass_1'] is True
        assert result['chi_eff'] is True

    def test_missing_uncertainty_key(self):
        """Test handling of missing uncertainty keys."""
        biases = {'mass_1': 0.5, 'missing_param': 0.1}
        uncertainties = {'mass_1_err': 1.645}

        result = check_bias_against_catalog_ci(biases, uncertainties)

        assert result['mass_1'] is False
        assert result['missing_param'] is False  # Should default to False


class TestInjectedDataValidation:
    """Tests for injected data scenario validation."""

    def test_perfect_recovery(self):
        """Test case where posterior perfectly recovers injection."""
        injected = {'mass_1': 30.0, 'chi_eff': 0.0}
        posterior = {
            'mass_1': np.array([30.0] * 1000),
            'chi_eff': np.array([0.0] * 1000)
        }

        is_valid, biases = validate_injected_data_scenario(posterior, injected, tolerance=1e-6)

        assert is_valid is True
        assert biases['mass_1'] == 0.0
        assert biases['chi_eff'] == 0.0

    def test_small_bias_within_tolerance(self):
        """Test case with small bias within tolerance."""
        injected = {'mass_1': 30.0}
        posterior = {'mass_1': np.array([30.0 + 1e-7] * 1000)}

        is_valid, biases = validate_injected_data_scenario(posterior, injected, tolerance=1e-6)

        assert is_valid is True
        assert np.isclose(biases['mass_1'], 1e-7)

    def test_large_bias_exceeds_tolerance(self):
        """Test case where bias exceeds tolerance."""
        injected = {'mass_1': 30.0}
        posterior = {'mass_1': np.array([30.0 + 1e-5] * 1000)}

        is_valid, biases = validate_injected_data_scenario(posterior, injected, tolerance=1e-6)

        assert is_valid is False
        assert np.isclose(biases['mass_1'], 1e-5)

    def test_no_common_parameters(self):
        """Test error when no common parameters exist."""
        injected = {'mass_1': 30.0}
        posterior = {'chi_eff': np.array([0.0] * 1000)}

        with pytest.raises(ValueError):
            validate_injected_data_scenario(posterior, injected)

    def test_empty_inputs(self):
        """Test error when inputs are empty."""
        with pytest.raises(ValueError):
            validate_injected_data_scenario({}, {'mass_1': 30.0})

        with pytest.raises(ValueError):
            validate_injected_data_scenario(
                {'mass_1': np.array([30.0])},
                {}
            )

    def test_realistic_posterior_recovery(self):
        """Test with realistic posterior samples around injected value."""
        injected = {
            'mass_1': 30.0,
            'mass_2': 25.0,
            'chi_eff': 0.0
        }

        # Simulate posterior with very small standard deviation (high precision)
        posterior = {
            'mass_1': np.random.normal(30.0, 1e-7, 10000),
            'mass_2': np.random.normal(25.0, 1e-7, 10000),
            'chi_eff': np.random.normal(0.0, 1e-7, 10000)
        }

        is_valid, biases = validate_injected_data_scenario(posterior, injected, tolerance=1e-6)

        assert is_valid is True
        for param, bias in biases.items():
            assert bias < 1e-6, f"Bias for {param} ({bias}) exceeds tolerance"