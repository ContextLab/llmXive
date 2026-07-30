"""
Tests for sensitivity analysis module (T029, T030).
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from sensitivity import (
    SensitivityError,
    load_statistical_results,
    sweep_alpha_thresholds,
    sweep_quasi_thermal_boundaries,
    verify_robustness,
    run_sensitivity_analysis,
    ALPHA_THRESHOLDS,
    QUASI_THERMAL_BOUNDARIES
)

@pytest.fixture
def mock_statistical_results():
    """Create a mock statistical results dictionary."""
    return {
        'bins': {
            'bin_1': {
                'tests': {
                    'ks_test': {'p_value': 0.03, 'rejection': True},
                    'chisq_test': {'p_value': 0.07, 'rejection': False}
                },
                'summary': {'energy_ratio': 1.02}
            },
            'bin_2': {
                'tests': {
                    'ks_test': {'p_value': 0.005, 'rejection': True},
                    'chisq_test': {'p_value': 0.04, 'rejection': True}
                },
                'summary': {'energy_ratio': 0.98}
            },
            'bin_3': {
                'tests': {
                    'ks_test': {'p_value': 0.15, 'rejection': False},
                    'chisq_test': {'p_value': 0.20, 'rejection': False}
                },
                'summary': {'energy_ratio': 1.05}
            }
        }
    }

@pytest.fixture
def temp_json_file(mock_statistical_results):
    """Create a temporary JSON file with mock statistical results."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_statistical_results, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_statistical_results_success(temp_json_file):
    """Test successful loading of statistical results."""
    results = load_statistical_results(temp_json_file)
    assert 'bins' in results
    assert len(results['bins']) == 3

def test_load_statistical_results_file_not_found():
    """Test loading non-existent file raises SensitivityError."""
    with pytest.raises(SensitivityError):
        load_statistical_results('non_existent_file.json')

def test_load_statistical_results_invalid_json():
    """Test loading invalid JSON raises SensitivityError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('invalid json {')
        temp_path = f.name
    try:
        with pytest.raises(SensitivityError):
            load_statistical_results(temp_path)
    finally:
        os.unlink(temp_path)

def test_sweep_alpha_thresholds(mock_statistical_results):
    """Test alpha threshold sweep logic (T029)."""
    results = sweep_alpha_thresholds(mock_statistical_results)

    # Check that all expected thresholds are present
    for alpha in ALPHA_THRESHOLDS:
        assert alpha in results
        assert 'rejection_count' in results[alpha]
        assert 'total_tests' in results[alpha]
        assert 'rejection_rate' in results[alpha]

    # Verify specific counts:
    # alpha=0.01: Only bin_2 ks_test (0.005) is < 0.01 -> 1 rejection
    # alpha=0.05: bin_1 ks_test (0.03), bin_2 ks_test (0.005), bin_2 chisq_test (0.04) -> 3 rejections
    # alpha=0.10: Same as 0.05 plus bin_1 chisq_test (0.07) -> 4 rejections

    assert results[0.01]['rejection_count'] == 1
    assert results[0.05]['rejection_count'] == 3
    assert results[0.10]['rejection_count'] == 4
    assert results[0.01]['total_tests'] == 6
    assert results[0.05]['total_tests'] == 6
    assert results[0.10]['total_tests'] == 6

def test_sweep_quasi_thermal_boundaries(mock_statistical_results):
    """Test quasi-thermal boundary sweep logic (T030)."""
    # Pass results as energy_data proxy
    results = sweep_quasi_thermal_boundaries(mock_statistical_results, mock_statistical_results)

    # Check that all expected boundaries are present
    for boundary in QUASI_THERMAL_BOUNDARIES:
        assert boundary in results
        assert 'threshold_low' in results[boundary]
        assert 'threshold_high' in results[boundary]
        assert 'classification_rate' in results[boundary]

    # Verify thresholds
    assert results[0.01]['threshold_low'] == 0.99
    assert results[0.01]['threshold_high'] == 1.01
    assert results[0.05]['threshold_low'] == 0.95
    assert results[0.05]['threshold_high'] == 1.05

def test_verify_robustness(mock_statistical_results):
    """Test robustness verification logic."""
    alpha_results = sweep_alpha_thresholds(mock_statistical_results)
    robustness = verify_robustness(alpha_results)

    assert 'robust' in robustness
    assert 'decisions' in robustness
    assert 'consistent_across_thresholds' in robustness

def test_run_sensitivity_analysis(mock_statistical_results):
    """Test full sensitivity analysis pipeline (T031)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_statistical_results, f)
        input_path = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name

    try:
        report = run_sensitivity_analysis(input_path, output_path)

        # Verify report structure
        assert 'alpha_sweep' in report
        assert 'quasi_thermal_boundary_sweep' in report
        assert 'robustness_verification' in report
        assert 'thresholds_tested' in report

        # Verify output file was created
        assert os.path.exists(output_path)

        # Verify output file content
        with open(output_path, 'r') as f:
            saved_report = json.load(f)
        assert saved_report == report

    finally:
        os.unlink(input_path)
        os.unlink(output_path)

def test_alpha_thresholds_constant():
    """Test that ALPHA_THRESHOLDS matches the spec requirement."""
    assert set(ALPHA_THRESHOLDS) == {0.01, 0.05, 0.10}

def test_quasi_thermal_boundaries_constant():
    """Test that QUASI_THERMAL_BOUNDARIES matches the spec requirement."""
    assert set(QUASI_THERMAL_BOUNDARIES) == {0.01, 0.05, 0.10}