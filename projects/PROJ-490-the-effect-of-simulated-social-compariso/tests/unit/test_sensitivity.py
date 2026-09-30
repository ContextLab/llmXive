import os
import json
import pytest
import numpy as np
from pathlib import Path
import pandas as pd

# Import the specific function to test from the analysis module
# Based on the provided API surface, this function exists in code/analysis/sensitivity.py
from analysis.sensitivity import calculate_parameter_recovery

# Helper to get project root relative to this test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"
STATE_PATH = PROJECT_ROOT / "state"

def _ensure_directories():
    """Ensure required directories exist for test artifacts."""
    DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
    STATE_PATH.mkdir(parents=True, exist_ok=True)

def _create_synthetic_ground_truth_file():
    """
    Creates a synthetic ground truth file if one does not exist.
    This mimics the output of T010/T012 to provide input for the test.
    """
    _ensure_directories()
    gt_path = DATA_PROCESSED_PATH / "ground_truth_params.json"
    
    # Ground truth parameters as defined in T010
    # intercept=0, main_effect_avatar=0.1, main_effect_comparison=0.1, interaction_beta=0.2, noise_sigma=1.0
    ground_truth = {
        "intercept": 0.0,
        "main_effect_avatar": 0.1,
        "main_effect_comparison": 0.1,
        "interaction_beta": 0.2,
        "noise_sigma": 1.0,
        "data_source_type": "synthetic"
    }
    
    with open(gt_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    return gt_path

def _create_mock_estimated_coefficients_file():
    """
    Creates a mock regression coefficients file to simulate T021 output.
    Used to test the bias calculation logic without running the full regression.
    """
    _ensure_directories()
    coeffs_path = DATA_PROCESSED_PATH / "regression_coefficients.csv"
    
    # Mock coefficients that are close to but not exactly the ground truth
    # to simulate estimation error
    data = {
        'name': ['Intercept', 'avatar_condition', 'comparison_tendency', 'avatar_condition:comparison_tendency'],
        'estimate': [0.05, 0.12, 0.09, 0.21], # Slight deviations
        'std_err': [0.01, 0.02, 0.02, 0.03],
        'p_value': [0.001, 0.02, 0.03, 0.01]
    }
    df = pd.DataFrame(data)
    df.to_csv(coeffs_path, index=False)
    return coeffs_path

def test_parameter_recovery_bias_calculation():
    """
    Unit test for parameter recovery bias calculation (|beta_hat - beta_true|).
    This test verifies that the function correctly calculates the absolute difference
    between estimated coefficients and ground truth parameters.
    
    Scenario:
    1. Ground truth parameters are available (simulated synthetic data).
    2. Estimated coefficients are available (simulated regression output).
    3. The function calculates |beta_hat - beta_true| for each parameter.
    4. The test asserts that the bias values are correct and non-negative.
    """
    # Setup: Create necessary input files
    gt_path = _create_synthetic_ground_truth_file()
    coeffs_path = _create_mock_estimated_coefficients_file()
    
    # Act: Call the function under test
    result = calculate_parameter_recovery(
        ground_truth_path=str(gt_path),
        estimated_path=str(coeffs_path)
    )
    
    # Assert: Verify the result structure and values
    assert result is not None, "Result should not be None"
    assert isinstance(result, dict), "Result should be a dictionary"
    
    # Check for expected keys
    assert 'bias' in result, "Result should contain 'bias' key"
    assert 'parameters' in result, "Result should contain 'parameters' key"
    assert 'data_source_type' in result, "Result should contain 'data_source_type' key"
    
    # Verify data source type
    assert result['data_source_type'] == 'synthetic', "Data source type should be synthetic"
    
    # Verify bias is a list of dictionaries
    assert isinstance(result['bias'], list), "Bias should be a list"
    assert len(result['bias']) > 0, "Bias list should not be empty"
    
    # Verify each bias entry
    for entry in result['bias']:
        assert 'parameter' in entry, "Each bias entry should have 'parameter' key"
        assert 'true_value' in entry, "Each bias entry should have 'true_value' key"
        assert 'estimated_value' in entry, "Each bias entry should have 'estimated_value' key"
        assert 'bias' in entry, "Each bias entry should have 'bias' key"
        
        # Verify bias is non-negative (absolute difference)
        assert entry['bias'] >= 0, "Bias should be non-negative (absolute difference)"
        
        # Verify calculation: bias = |estimated - true|
        expected_bias = abs(entry['estimated_value'] - entry['true_value'])
        assert np.isclose(entry['bias'], expected_bias), \
            f"Bias calculation incorrect for {entry['parameter']}: expected {expected_bias}, got {entry['bias']}"

def test_parameter_recovery_with_exact_match():
    """
    Test that bias is exactly 0 when estimated values match ground truth.
    """
    _ensure_directories()
    
    # Create ground truth
    gt_path = DATA_PROCESSED_PATH / "ground_truth_exact.json"
    ground_truth = {
        "intercept": 1.0,
        "main_effect_avatar": 2.0,
        "main_effect_comparison": 3.0,
        "interaction_beta": 4.0,
        "noise_sigma": 1.0,
        "data_source_type": "synthetic"
    }
    with open(gt_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    # Create estimated coefficients that exactly match ground truth
    coeffs_path = DATA_PROCESSED_PATH / "regression_exact.csv"
    data = {
        'name': ['Intercept', 'avatar_condition', 'comparison_tendency', 'avatar_condition:comparison_tendency'],
        'estimate': [1.0, 2.0, 3.0, 4.0], # Exact match
        'std_err': [0.01, 0.02, 0.02, 0.03],
        'p_value': [0.001, 0.02, 0.03, 0.01]
    }
    pd.DataFrame(data).to_csv(coeffs_path, index=False)
    
    # Act
    result = calculate_parameter_recovery(
        ground_truth_path=str(gt_path),
        estimated_path=str(coeffs_path)
    )
    
    # Assert
    for entry in result['bias']:
        assert entry['bias'] == 0.0, f"Bias should be 0.0 for exact match, got {entry['bias']}"

def test_parameter_recovery_missing_files():
    """
    Test that the function handles missing files gracefully (returns None or raises appropriate error).
    Based on the implementation, it should handle missing files by returning None or a specific status.
    """
    # Act with non-existent paths
    result = calculate_parameter_recovery(
        ground_truth_path="/nonexistent/path/gt.json",
        estimated_path="/nonexistent/path/coeffs.csv"
    )
    
    # Assert: The function should handle this case. 
    # Depending on implementation, it might return None or a dict with error status.
    # We assert that it doesn't crash and returns a recognizable state.
    assert result is None or (isinstance(result, dict) and 'error' in result), \
        "Function should handle missing files gracefully"

def test_parameter_recovery_mapping_correctness():
    """
    Test that the parameter names are correctly mapped between ground truth and estimated coefficients.
    Ensures that 'main_effect_avatar' maps to 'avatar_condition', etc.
    """
    _ensure_directories()
    
    # Create ground truth with specific mapping
    gt_path = DATA_PROCESSED_PATH / "ground_truth_map.json"
    ground_truth = {
        "intercept": 0.0,
        "main_effect_avatar": 0.5,
        "main_effect_comparison": 0.5,
        "interaction_beta": 0.5,
        "noise_sigma": 1.0,
        "data_source_type": "synthetic"
    }
    with open(gt_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    # Create estimated coefficients
    coeffs_path = DATA_PROCESSED_PATH / "regression_map.csv"
    data = {
        'name': ['Intercept', 'avatar_condition', 'comparison_tendency', 'avatar_condition:comparison_tendency'],
        'estimate': [0.1, 0.6, 0.4, 0.6], # Deliberate deviations
        'std_err': [0.01, 0.02, 0.02, 0.03],
        'p_value': [0.001, 0.02, 0.03, 0.01]
    }
    pd.DataFrame(data).to_csv(coeffs_path, index=False)
    
    # Act
    result = calculate_parameter_recovery(
        ground_truth_path=str(gt_path),
        estimated_path=str(coeffs_path)
    )
    
    # Assert: Check that the mapping is correct
    bias_dict = {entry['parameter']: entry for entry in result['bias']}
    
    # Check intercept
    assert 'Intercept' in bias_dict, "Intercept should be mapped"
    assert np.isclose(bias_dict['Intercept']['bias'], 0.1), "Intercept bias should be 0.1"
    
    # Check avatar_condition (maps to main_effect_avatar)
    assert 'avatar_condition' in bias_dict, "avatar_condition should be mapped"
    assert np.isclose(bias_dict['avatar_condition']['bias'], 0.1), "Avatar main effect bias should be 0.1"
    
    # Check comparison_tendency (maps to main_effect_comparison)
    assert 'comparison_tendency' in bias_dict, "comparison_tendency should be mapped"
    assert np.isclose(bias_dict['comparison_tendency']['bias'], 0.1), "Comparison main effect bias should be 0.1"
    
    # Check interaction (maps to interaction_beta)
    assert 'avatar_condition:comparison_tendency' in bias_dict, "Interaction should be mapped"
    assert np.isclose(bias_dict['avatar_condition:comparison_tendency']['bias'], 0.1), "Interaction bias should be 0.1"