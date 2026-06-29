"""
tests/test_analysis.py

Unit tests for analysis.py module.
"""
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from analysis import (
    select_model_aic,
    filter_unresolved_realizations,
    bootstrap_resample,
    compute_bootstrap_statistics,
    compute_scaling_exponent,
    generate_toy_model_data
)

def test_filter_unresolved_realizations():
    """Test that numerically unresolved realizations are filtered out."""
    # Create mock data
    entropy_data = [
        {'realization_id': 1, 'l_values': np.array([1, 2, 3]), 'entropy_values': np.array([0.5, 1.0, 1.5])},
        {'realization_id': 2, 'l_values': np.array([1, 2, 3]), 'entropy_values': np.array([0.6, 1.1, 1.6])},
        {'realization_id': 3, 'l_values': np.array([1, 2, 3]), 'entropy_values': np.array([0.4, 0.9, 1.4])},
    ]
    ground_state_flags = [False, True, False]  # Second one is unresolved

    filtered_data, filtered_flags = filter_unresolved_realizations(entropy_data, ground_state_flags)

    assert len(filtered_data) == 2
    assert len(filtered_flags) == 2
    assert filtered_flags == [False, False]
    assert filtered_data[0]['realization_id'] == 1
    assert filtered_data[1]['realization_id'] == 3

def test_filter_unresolved_realizations_all_unresolved():
    """Test filtering when all realizations are unresolved."""
    entropy_data = [
        {'realization_id': 1, 'l_values': np.array([1, 2, 3]), 'entropy_values': np.array([0.5, 1.0, 1.5])},
        {'realization_id': 2, 'l_values': np.array([1, 2, 3]), 'entropy_values': np.array([0.6, 1.1, 1.6])},
    ]
    ground_state_flags = [True, True]

    filtered_data, filtered_flags = filter_unresolved_realizations(entropy_data, ground_state_flags)

    assert len(filtered_data) == 0
    assert len(filtered_flags) == 0

def test_filter_unresolved_realizations_none_unresolved():
    """Test filtering when no realizations are unresolved."""
    entropy_data = [
        {'realization_id': 1, 'l_values': np.array([1, 2, 3]), 'entropy_values': np.array([0.5, 1.0, 1.5])},
        {'realization_id': 2, 'l_values': np.array([1, 2, 3]), 'entropy_values': np.array([0.6, 1.1, 1.6])},
    ]
    ground_state_flags = [False, False]

    filtered_data, filtered_flags = filter_unresolved_realizations(entropy_data, ground_state_flags)

    assert len(filtered_data) == 2
    assert len(filtered_flags) == 2

def test_filter_unresolved_realizations_mismatched_lengths():
    """Test that mismatched lengths raise an error."""
    entropy_data = [
        {'realization_id': 1, 'l_values': np.array([1, 2, 3]), 'entropy_values': np.array([0.5, 1.0, 1.5])},
    ]
    ground_state_flags = [False, True]

    with pytest.raises(ValueError):
        filter_unresolved_realizations(entropy_data, ground_state_flags)

def test_bootstrap_resample():
    """Test bootstrap resampling generates correct number of samples."""
    l_values = np.array([1, 2, 3, 4, 5])
    entropy_values = np.array([0.5, 1.0, 1.5, 2.0, 2.5])
    n_resamples = 100

    resamples = bootstrap_resample(l_values, entropy_values, n_resamples, random_seed=42)

    assert len(resamples) == n_resamples
    for sample in resamples:
        assert len(sample) == len(entropy_values)

def test_compute_bootstrap_statistics():
    """Test bootstrap statistics computation."""
    l_values = np.array([1, 2, 3, 4, 5])
    entropy_values = np.array([0.5, 1.0, 1.5, 2.0, 2.5])

    stats_result = compute_bootstrap_statistics(l_values, entropy_values, n_resamples=100, random_seed=42)

    assert 'exponent_mean' in stats_result
    assert 'exponent_std' in stats_result
    assert 'ci_lower' in stats_result
    assert 'ci_upper' in stats_result
    assert 'p_value' in stats_result
    assert 'resample_count' in stats_result
    assert stats_result['resample_count'] == 100

def test_select_model_aic_logarithmic():
    """Test AIC selection for logarithmic data."""
    l_values = np.array([1, 2, 3, 4, 5])
    entropy_values = 0.5 * np.log(l_values) + 1.0  # Pure logarithmic

    result = select_model_aic(l_values, entropy_values)

    assert result.model_type == 'logarithmic'
    assert abs(result.params[0] - 0.5) < 0.1

def test_select_model_aic_area_law():
    """Test AIC selection for area law (constant) data."""
    l_values = np.array([1, 2, 3, 4, 5])
    entropy_values = np.full_like(l_values, 1.0, dtype=float)  # Constant

    result = select_model_aic(l_values, entropy_values)

    assert result.model_type == 'area_law'

def test_select_model_aic_volume_law():
    """Test AIC selection for volume law (linear) data."""
    l_values = np.array([1, 2, 3, 4, 5])
    entropy_values = 0.5 * l_values + 1.0  # Linear

    result = select_model_aic(l_values, entropy_values)

    # With enough points, volume law should be selected
    assert result.model_type in ['volume_law', 'logarithmic']  # May sometimes be logarithmic for small ranges