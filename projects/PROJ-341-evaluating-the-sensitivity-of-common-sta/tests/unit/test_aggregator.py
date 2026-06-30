import os
import csv
import tempfile
import pytest
from code.analysis.aggregator import calculate_error_rates, save_aggregated_results

def test_calculate_error_rates_type_1():
    """
    Test that Type I error is calculated correctly when Null is True (effect_size=0).
    Scenario: 10 iterations, all p < 0.05. Expected Type I rate = 1.0.
    """
    # Create mock data
    mock_data = [
        {'sample_size': 10, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.01},
        {'sample_size': 10, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.04},
        {'sample_size': 10, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.03},
        {'sample_size': 10, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.02},
        {'sample_size': 10, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.001},
        {'sample_size': 10, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.049},
        {'sample_size': 10, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.03},
        {'sample_size': 10, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.02},
        {'sample_size': 10, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.01},
        {'sample_size': 10, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.04},
    ]

    # Write to temp CSV
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_size', 'effect_size', 'test_type', 'p_value'])
        writer.writeheader()
        writer.writerows(mock_data)
        temp_path = f.name

    try:
        results = calculate_error_rates(temp_path, alpha=0.05)
        assert len(results) == 1
        res = results[0]
        assert res['null_true_trials'] == 10
        assert res['type_1_errors'] == 10
        assert abs(res['type_1_error_rate'] - 1.0) < 1e-9
        assert res['null_false_trials'] == 0
    finally:
        os.unlink(temp_path)

def test_calculate_error_rates_type_2():
    """
    Test that Type II error is calculated correctly when Null is False (effect_size > 0).
    Scenario: 10 iterations, all p >= 0.05. Expected Type II rate = 1.0.
    """
    mock_data = [
        {'sample_size': 20, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.10},
        {'sample_size': 20, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.20},
        {'sample_size': 20, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.50},
        {'sample_size': 20, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.60},
        {'sample_size': 20, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.05}, # Exactly alpha -> not reject -> Type II
        {'sample_size': 20, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.70},
        {'sample_size': 20, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.80},
        {'sample_size': 20, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.90},
        {'sample_size': 20, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.15},
        {'sample_size': 20, 'effect_size': 0.5, 'test_type': 't-test', 'p_value': 0.25},
    ]

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_size', 'effect_size', 'test_type', 'p_value'])
        writer.writeheader()
        writer.writerows(mock_data)
        temp_path = f.name

    try:
        results = calculate_error_rates(temp_path, alpha=0.05)
        assert len(results) == 1
        res = results[0]
        assert res['null_false_trials'] == 10
        assert res['type_2_errors'] == 10
        assert abs(res['type_2_error_rate'] - 1.0) < 1e-9
        assert res['power'] == 0.0
    finally:
        os.unlink(temp_path)

def test_mixed_conditions():
    """
    Test aggregation with mixed null/alt hypotheses and different test types.
    """
    mock_data = [
        # Condition A: Null True, 50% reject (Type I = 0.5)
        {'sample_size': 5, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.01},
        {'sample_size': 5, 'effect_size': 0.0, 'test_type': 't-test', 'p_value': 0.10},
        # Condition B: Alt True, 50% fail to reject (Type II = 0.5)
        {'sample_size': 5, 'effect_size': 1.0, 'test_type': 't-test', 'p_value': 0.10},
        {'sample_size': 5, 'effect_size': 1.0, 'test_type': 't-test', 'p_value': 0.01},
        # Condition C: Chi-squared, Null True
        {'sample_size': 5, 'effect_size': 0.0, 'test_type': 'chi-squared', 'p_value': 0.01},
    ]

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_size', 'effect_size', 'test_type', 'p_value'])
        writer.writeheader()
        writer.writerows(mock_data)
        temp_path = f.name

    try:
        results = calculate_error_rates(temp_path, alpha=0.05)
        assert len(results) == 3
        
        # Sort results for predictable indexing
        results.sort(key=lambda x: (x['test_type'], x['effect_size']))
        
        # Condition A (t-test, 0.0)
        cond_a = next(r for r in results if r['test_type'] == 't-test' and r['effect_size'] == 0.0)
        assert cond_a['type_1_error_rate'] == 0.5
        assert cond_a['null_true_trials'] == 2
        
        # Condition B (t-test, 1.0)
        cond_b = next(r for r in results if r['test_type'] == 't-test' and r['effect_size'] == 1.0)
        assert cond_b['type_2_error_rate'] == 0.5
        assert cond_b['null_false_trials'] == 2
        
        # Condition C (chi-squared, 0.0)
        cond_c = next(r for r in results if r['test_type'] == 'chi-squared' and r['effect_size'] == 0.0)
        assert cond_c['type_1_error_rate'] == 1.0
    finally:
        os.unlink(temp_path)
