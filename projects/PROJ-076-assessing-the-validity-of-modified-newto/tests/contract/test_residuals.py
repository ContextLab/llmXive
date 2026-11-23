"""
Tests for residual analysis module.
"""

import pytest
import numpy as np
from residuals import (
    calculate_residuals,
    calculate_residuals_for_galaxy,
    block_bootstrap_permutation_test,
    holm_bonferroni_correction,
    generate_residual_stats
)

def test_calculate_residuals():
    """Test basic residual calculation."""
    observed = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    predicted = np.array([1.1, 2.1, 2.9, 4.2, 4.8])

    residuals = calculate_residuals(observed, predicted)

    expected = observed - predicted
    np.testing.assert_array_almost_equal(residuals, expected)

def test_calculate_residuals_with_uncertainty():
    """Test residual calculation with uncertainty (should be ignored)."""
    observed = np.array([1.0, 2.0, 3.0])
    predicted = np.array([1.1, 2.1, 2.9])
    uncertainty = np.array([0.1, 0.1, 0.1])

    residuals = calculate_residuals(observed, predicted, uncertainty)
    expected = observed - predicted

    np.testing.assert_array_almost_equal(residuals, expected)

def test_calculate_residuals_for_galaxy():
    """Test residual calculation for a single galaxy."""
    galaxy_data = {
        'galaxy_id': 'NGC123',
        'r': np.array([1.0, 2.0, 3.0]),
        'v_obs': np.array([10.0, 20.0, 30.0]),
        'v_err': np.array([0.5, 0.5, 0.5])
    }

    fit_results = {
        'mond': {
            'predicted': np.array([10.5, 19.5, 30.5]),
            'params': {'a0': 1.2e-10}
        },
        'nfw': {
            'predicted': np.array([9.5, 20.5, 29.5]),
            'params': {'concentration': 10.0}
        }
    }

    residuals = calculate_residuals_for_galaxy(galaxy_data, fit_results)

    assert 'mond' in residuals
    assert 'nfw' in residuals
    assert len(residuals['mond']) == 3
    assert len(residuals['nfw']) == 3

    # Check specific values
    np.testing.assert_array_almost_equal(
        residuals['mond'],
        galaxy_data['v_obs'] - fit_results['mond']['predicted']
    )
    np.testing.assert_array_almost_equal(
        residuals['nfw'],
        galaxy_data['v_obs'] - fit_results['nfw']['predicted']
    )

def test_block_bootstrap_permutation_test():
    """Test block-bootstrap permutation test."""
    np.random.seed(42)
    residuals_mond = np.random.normal(0.0, 1.0, 100)
    residuals_nfw = np.random.normal(0.1, 1.0, 100)

    result = block_bootstrap_permutation_test(
        residuals_mond,
        residuals_nfw,
        n_bootstrap=100,
        block_size=5,
        random_state=42
    )

    assert 'p_value' in result
    assert 'test_statistic' in result
    assert 'bootstrap_distribution' in result
    assert 'confidence_interval' in result

    assert 0.0 <= result['p_value'] <= 1.0
    assert len(result['bootstrap_distribution']) == 100

def test_holm_bonferroni_correction():
    """Test Holm-Bonferroni correction."""
    p_values = [0.01, 0.03, 0.05, 0.10, 0.20]
    alpha = 0.05

    result = holm_bonferroni_correction(p_values, alpha)

    assert 'corrected_p_values' in result
    assert 'rejections' in result
    assert 'step_thresholds' in result

    assert len(result['corrected_p_values']) == 5
    assert len(result['rejections']) == 5
    assert len(result['step_thresholds']) == 5

    # First p-value should be rejected (0.01 * 5 = 0.05 <= 0.05)
    assert result['rejections'][0] == True

def test_holm_bonferroni_empty():
    """Test Holm-Bonferroni with empty input."""
    result = holm_bonferroni_correction([], 0.05)

    assert result['corrected_p_values'] == []
    assert result['rejections'] == []
    assert result['step_thresholds'] == []

def test_generate_residual_stats():
    """Test residual statistics generation."""
    residuals_by_galaxy = {
        'NGC123': {
            'mond': np.array([0.1, -0.2, 0.3]),
            'nfw': np.array([-0.1, 0.2, -0.3])
        },
        'NGC456': {
            'mond': np.array([0.05, -0.15, 0.25]),
            'nfw': np.array([-0.05, 0.15, -0.25])
        }
    }

    bootstrap_results = {
        'NGC123': {
            'mond': {'p_value': 0.03},
            'nfw': {'p_value': 0.04}
        },
        'NGC456': {
            'mond': {'p_value': 0.06},
            'nfw': {'p_value': 0.07}
        }
    }

    correction_results = {
        'NGC123': {
            'corrected_p_values': [0.06, 0.08],
            'rejections': [True, False]
        },
        'NGC456': {
            'corrected_p_values': [0.12, 0.14],
            'rejections': [False, False]
        }
    }

    stats_df = generate_residual_stats(
        residuals_by_galaxy,
        bootstrap_results,
        correction_results
    )

    assert len(stats_df) == 4  # 2 galaxies * 2 models
    assert 'galaxy_id' in stats_df.columns
    assert 'model' in stats_df.columns
    assert 'mean_residual' in stats_df.columns
    assert 'p_value' in stats_df.columns
    assert 'corrected_p_value' in stats_df.columns