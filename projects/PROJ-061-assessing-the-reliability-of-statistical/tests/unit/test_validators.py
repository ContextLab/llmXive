"""
Unit tests for code/validators.py
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import json
import os
import sys
from pathlib import Path

# Add project root to path for imports if running from tests/
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from validators import (
    bootstrap_validity_check,
    verify_achieved_magnitude,
    validate_power_estimate,
    run_validation_suite,
    MIN_BOOTSTRAP_SAMPLES
)

@pytest.fixture
def sample_bootstrap_estimates_valid():
    """Generate a list of power estimates with low variance."""
    np.random.seed(42)
    # Mean 0.8, std 0.01 -> variance ~0.0001
    return list(np.random.normal(0.8, 0.01, 2000))

@pytest.fixture
def sample_bootstrap_estimates_invalid():
    """Generate a list of power estimates with high variance."""
    np.random.seed(42)
    # Bimodal distribution: 0.5 and 0.9 -> high variance
    return [0.5] * 1000 + [0.9] * 1000

def test_bootstrap_validity_check_reliable(sample_bootstrap_estimates_valid):
    """Test that low variance estimates are marked reliable."""
    analytical_var = 0.0001  # Low theoretical variance
    result = bootstrap_validity_check(sample_bootstrap_estimates_valid, analytical_var)
    
    assert result['is_reliable'] is True
    assert result['variance_ratio'] < 2.0  # Default threshold
    assert "reason" in result

def test_bootstrap_validity_check_unreliable(sample_bootstrap_estimates_invalid):
    """Test that high variance estimates are marked unreliable."""
    analytical_var = 0.0001
    result = bootstrap_validity_check(sample_bootstrap_estimates_invalid, analytical_var)
    
    assert result['is_reliable'] is False
    assert "exceeds" in result['reason'].lower() or "unstable" in result['reason'].lower()

def test_bootstrap_validity_check_insufficient_samples():
    """Test behavior when bootstrap sample count is too low."""
    few_samples = [0.8, 0.81, 0.79]
    result = bootstrap_validity_check(few_samples, 0.0001)
    
    assert result['is_reliable'] is False
    assert "Bootstrap sample size" in result['reason']

def test_verify_achieved_magnitude_pass():
    """Test magnitude verification within tolerance."""
    result = verify_achieved_magnitude(target_magnitude=0.5, achieved_magnitude=0.48)
    assert result['within_tolerance'] is True
    assert result['relative_error'] < 0.05

def test_verify_achieved_magnitude_fail():
    """Test magnitude verification outside tolerance."""
    result = verify_achieved_magnitude(target_magnitude=0.5, achieved_magnitude=0.60)
    assert result['within_tolerance'] is False
    assert result['relative_error'] > 0.05

def test_verify_achieved_magnitude_zero_target():
    """Test magnitude verification when target is zero."""
    result = verify_achieved_magnitude(target_magnitude=0.0, achieved_magnitude=0.01)
    # Relative error calculation for zero target is absolute error
    assert result['within_tolerance'] is False

def test_validate_power_estimate_full_flow():
    """Test the full validation flow for a power estimate."""
    estimate = {
        'bootstrap_estimates': [0.8] * 2000,
        'analytical_variance': 0.0001,
        'sample_size': 100
    }
    dataset_info = {'name': 'test_dataset'}
    
    result = validate_power_estimate(estimate, dataset_info)
    
    assert result['dataset_name'] == 'test_dataset'
    assert result['is_reliable'] is True
    assert result['exclude_from_bias_calculation'] is False

def test_validate_power_estimate_unreliable():
    """Test validation flow for an unreliable estimate."""
    estimate = {
        'bootstrap_estimates': [0.5, 0.9] * 1000,
        'analytical_variance': 0.0001,
        'sample_size': 100
    }
    dataset_info = {'name': 'bad_dataset'}
    
    result = validate_power_estimate(estimate, dataset_info)
    
    assert result['is_reliable'] is False
    assert result['exclude_from_bias_calculation'] is True

def test_validate_power_estimate_small_sample():
    """Test validation flow for small sample size."""
    estimate = {
        'bootstrap_estimates': [0.8] * 2000,
        'analytical_variance': 0.0001,
        'sample_size': 10
    }
    dataset_info = {'name': 'small_dataset'}
    
    result = validate_power_estimate(estimate, dataset_info)
    
    assert result['is_reliable'] is False
    assert "Sample size" in result['validation_details']['reason']

@patch('validators.load_json')
@patch('validators.save_json')
@patch('validators.logger')
def test_run_validation_suite(mock_logger, mock_save, mock_load):
    """Test the run_validation_suite function."""
    mock_data = {
        'results': [
            {
                'name': 'good_data',
                'sample_size': 100,
                'bootstrap_estimates': [0.8] * 2000,
                'analytical_variance': 0.0001
            },
            {
                'name': 'bad_data',
                'sample_size': 100,
                'bootstrap_estimates': [0.5, 0.9] * 1000,
                'analytical_variance': 0.0001
            }
        ]
    }
    mock_load.return_value = mock_data
    
    run_validation_suite("input.json", "output.json")
    
    # Verify save_json was called with the correct report structure
    assert mock_save.called
    call_args = mock_save.call_args[0]
    report = call_args[0]
    
    assert report['total_datasets'] == 2
    assert report['reliable_count'] == 1
    assert report['unreliable_count'] == 1
    assert 'bad_data' in report['excluded_datasets']