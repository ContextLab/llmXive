"""
Unit tests for the Alpha Sensitivity Analysis module (T035).
"""
import pytest
import os
import json
import tempfile
import csv
from code.analysis.alpha_sensitivity import (
    calculate_error_rates_for_alpha,
    find_threshold_shifts,
    run_sensitivity_analysis,
    STANDARD_ALPHAS
)

def create_mock_raw_data(num_rows=100, alpha=0.05):
    """Helper to create mock raw p-value data."""
    data = []
    # H0 Data: Should have p-values uniformly distributed (mostly)
    for i in range(num_rows // 2):
        # Generate some p-values < alpha to simulate Type I errors
        p_val = 0.01 if i < (num_rows // 2 * alpha) else 0.10
        data.append({
            'sample_size': 50,
            'test_type': 't-test',
            'effect_size': 0.0,
            'hypothesis': 'H0',
            'p_value': p_val
        })
    
    # H1 Data: Should have power (p < alpha)
    for i in range(num_rows // 2):
        # Generate some p-values < alpha to simulate Power
        p_val = 0.01 if i < (num_rows // 2 * 0.8) else 0.20
        data.append({
            'sample_size': 50,
            'test_type': 't-test',
            'effect_size': 0.5,
            'hypothesis': 'H1',
            'p_value': p_val
        })
    return data

def test_calculate_error_rates_h0():
    """Test Type I error calculation for H0 hypothesis."""
    raw_data = create_mock_raw_data(num_rows=200, alpha=0.05)
    results = calculate_error_rates_for_alpha(raw_data, alpha=0.05)
    
    # Filter for H0 results
    h0_results = [r for r in results if r['hypothesis'] == 'H0']
    assert len(h0_results) == 1
    
    row = h0_results[0]
    assert row['type_1_error_rate'] is not None
    assert row['power'] is None
    # With 10% of 100 items being < 0.05 (artificially set), rate should be ~0.1
    # But our mock logic sets 10% to 0.01 (which is < 0.05)
    # Wait, mock logic: i < (100 * 0.05) -> 5 items. Rate = 5/100 = 0.05
    assert abs(row['type_1_error_rate'] - 0.05) < 0.01

def test_calculate_error_rates_h1():
    """Test Power calculation for H1 hypothesis."""
    raw_data = create_mock_raw_data(num_rows=200, alpha=0.05)
    results = calculate_error_rates_for_alpha(raw_data, alpha=0.05)
    
    h1_results = [r for r in results if r['hypothesis'] == 'H1']
    assert len(h1_results) == 1
    
    row = h1_results[0]
    assert row['power'] is not None
    assert row['type_1_error_rate'] is None
    # Mock logic: 80% of 100 items < 0.05 -> Power = 0.8
    assert abs(row['power'] - 0.8) < 0.01

def test_find_threshold_shifts():
    """Test logic for identifying sample size threshold shifts."""
    # Construct mock aggregated data
    mock_data = [
        {'sample_size': 10, 'test_type': 't-test', 'effect_size': 0.5, 'alpha': 0.05, 'type_1_error_rate': 0.06, 'power': 0.4},
        {'sample_size': 20, 'test_type': 't-test', 'effect_size': 0.5, 'alpha': 0.05, 'type_1_error_rate': 0.05, 'power': 0.6},
        {'sample_size': 30, 'test_type': 't-test', 'effect_size': 0.5, 'alpha': 0.05, 'type_1_error_rate': 0.05, 'power': 0.85},
        
        {'sample_size': 10, 'test_type': 't-test', 'effect_size': 0.5, 'alpha': 0.01, 'type_1_error_rate': 0.02, 'power': 0.2},
        {'sample_size': 20, 'test_type': 't-test', 'effect_size': 0.5, 'alpha': 0.01, 'type_1_error_rate': 0.01, 'power': 0.4},
        {'sample_size': 30, 'test_type': 't-test', 'effect_size': 0.5, 'alpha': 0.01, 'type_1_error_rate': 0.01, 'power': 0.6},
    ]
    
    shifts = find_threshold_shifts(mock_data, target_metric='power')
    
    key = 't-test_0.5'
    assert key in shifts
    assert 0.05 in shifts[key]
    assert 0.01 in shifts[key]
    
    # For alpha 0.05, power >= 0.80 happens at n=30
    assert shifts[key][0.05]['threshold_sample_size'] == 30
    
    # For alpha 0.01, power never reaches 0.80 in this mock data
    assert shifts[key][0.01]['threshold_sample_size'] is None

def test_run_sensitivity_analysis_integration(tmp_path):
    """Integration test for the full sensitivity analysis pipeline."""
    # Create mock raw data file
    raw_path = os.path.join(tmp_path, 'p_values_raw.csv')
    raw_data = create_mock_raw_data(num_rows=200)
    
    with open(raw_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=raw_data[0].keys())
        writer.writeheader()
        writer.writerows(raw_data)
    
    output_csv = os.path.join(tmp_path, 'results.csv')
    output_json = os.path.join(tmp_path, 'summary.json')
    
    success = run_sensitivity_analysis(
        input_path=raw_path,
        output_path=output_csv,
        summary_path=output_json
    )
    
    assert success
    assert os.path.exists(output_csv)
    assert os.path.exists(output_json)
    
    # Verify JSON structure
    with open(output_json, 'r') as f:
        summary = json.load(f)
    
    assert 'alphas_analyzed' in summary
    assert set(summary['alphas_analyzed']) == set(STANDARD_ALPHAS)
    assert 'type_i_error_thresholds' in summary
    assert 'power_thresholds' in summary