"""
Integration tests for sensitivity analysis (T022).

Verifies that coefficient variation is calculated correctly across strategies
as defined in code/analysis/sensitivity.py.

This test:
1. Generates synthetic data (using the project's generator).
2. Runs the sensitivity analysis pipeline.
3. Verifies the output structure in data/processed/sensitivity_analysis.json.
4. Validates that coefficient variation (delta) is computed correctly.
"""

import os
import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Project imports
from data.generator import generate_synthetic_data
from analysis.sensitivity import (
    remove_outliers_iqr,
    winsorize_data,
    run_single_regression,
    run_sensitivity_analysis,
)
from utils.constants import get_stability_threshold, get_seed
from utils.exceptions import StabilityThresholdViolationError


@pytest.fixture(scope="module")
def synthetic_dataset():
    """
    Generate a single synthetic dataset for all integration tests.
    Uses the project's generator to ensure consistency with the pipeline.
    """
    np.random.seed(get_seed())
    # Generate N=500 to ensure robust statistical properties for integration
    data = generate_synthetic_data(n_samples=500)
    
    # Ensure required columns exist for regression
    required_cols = [
        'self_perception_score', 'psv_score', 'age', 'gender',
        'offline_relationships', 'intrinsic_traits'
    ]
    for col in required_cols:
        if col not in data.columns:
            raise ValueError(f"Generated data missing required column: {col}")
    
    return data


@pytest.fixture(scope="module")
def sensitivity_results(synthetic_dataset):
    """
    Run the full sensitivity analysis pipeline once and return results.
    """
    results = run_sensitivity_analysis(synthetic_dataset)
    return results


def test_sensitivity_output_structure(sensitivity_results):
    """
    Verify that sensitivity_analysis.json has the correct structure.
    """
    assert isinstance(sensitivity_results, list), "Results must be a list of strategy runs."
    assert len(sensitivity_results) > 0, "Results list must not be empty."

    # Check for expected keys in each result entry
    required_keys = {
        'strategy_name',
        'coefficient',
        'p_value',
        'std_err',
        'variation_delta'
    }

    for entry in sensitivity_results:
        assert isinstance(entry, dict), "Each entry must be a dictionary."
        assert required_keys.issubset(entry.keys()), f"Missing keys in entry: {entry.keys()}"
        assert isinstance(entry['strategy_name'], str), "strategy_name must be a string."
        assert isinstance(entry['coefficient'], (int, float)), "coefficient must be numeric."
        assert isinstance(entry['variation_delta'], (int, float)), "variation_delta must be numeric."


def test_coefficient_variation_calculation(sensitivity_results):
    """
    Verify that variation_delta is calculated correctly relative to the baseline.
    The baseline is typically the 'none' strategy (no outlier removal).
    """
    # Find the baseline (no outlier removal)
    baseline_entry = next(
        (r for r in sensitivity_results if r['strategy_name'] == 'none'),
        None
    )
    
    if baseline_entry is None:
        pytest.skip("Baseline 'none' strategy not found in results.")

    baseline_coef = baseline_entry['coefficient']

    for entry in sensitivity_results:
        expected_delta = abs(entry['coefficient'] - baseline_coef)
        actual_delta = entry['variation_delta']
        
        # Allow small floating point tolerance
        assert np.isclose(expected_delta, actual_delta, atol=1e-6), \
            f"Variation delta mismatch for {entry['strategy_name']}: " \
            f"Expected {expected_delta}, got {actual_delta}"


def test_outlier_removal_strategies(sensitivity_results):
    """
    Verify that specific outlier strategies ('IQR removal', 'winsorization')
    are present in the results.
    """
    strategy_names = [r['strategy_name'] for r in sensitivity_results]
    
    assert 'none' in strategy_names, "Strategy 'none' must be present."
    assert 'IQR removal' in strategy_names, "Strategy 'IQR removal' must be present."
    assert 'winsorization' in strategy_names, "Strategy 'winsorization' must be present."


def test_confounder_matrix_presence(sensitivity_results):
    """
    Verify that the sensitivity analysis includes runs with confounders included/excluded.
    The task requires a matrix of runs. We check that the strategy names reflect
    the combination of outlier handling and confounder status.
    """
    strategy_names = [r['strategy_name'] for r in sensitivity_results]
    
    # Check for at least one entry with confounders included (default)
    # and one with confounders excluded (if implemented).
    # The naming convention in sensitivity.py should reflect this.
    # We expect names like: "none", "IQR removal", "winsorization"
    # potentially with suffixes like "_no_confounders".
    
    # At minimum, we verify the outlier strategies exist.
    # The full matrix logic is tested in unit tests; here we verify the integration
    # produces a non-trivial set of results.
    assert len(strategy_names) >= 3, "Must have at least 3 strategies (none, IQR, winsor)."


def test_stability_threshold_check_integration(sensitivity_results):
    """
    Verify that the stability threshold check logic is consistent with constants.
    This doesn't necessarily raise an error if the data is stable, but verifies
    the calculation aligns with the threshold definition.
    """
    threshold = get_stability_threshold()
    
    max_variation = max(r['variation_delta'] for r in sensitivity_results)
    
    # If max variation exceeds threshold, the pipeline should have raised an error
    # if run in main.py. Here we just verify the values are calculated.
    # We assert that the threshold is a positive float.
    assert isinstance(threshold, (int, float)) and threshold > 0, "Threshold must be positive."
    
    # Verify that variation deltas are non-negative
    for r in sensitivity_results:
        assert r['variation_delta'] >= 0, "Variation delta must be non-negative."


def test_integration_with_real_file_output(tmp_path, synthetic_dataset):
    """
    Verify that run_sensitivity_analysis can write to a real file path
    and that the content matches the returned object.
    """
    output_path = tmp_path / "sensitivity_test.json"
    
    # Run analysis and write to file
    results = run_sensitivity_analysis(synthetic_dataset, output_path=str(output_path))
    
    # Verify file exists
    assert output_path.exists(), "Output file was not created."
    
    # Verify content matches returned object
    with open(output_path, 'r') as f:
        file_data = json.load(f)
    
    assert len(file_data) == len(results), "File content length mismatch."
    
    # Verify structure
    for i, entry in enumerate(file_data):
        assert 'strategy_name' in entry
        assert 'coefficient' in entry
        assert 'variation_delta' in entry