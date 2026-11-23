"""
Integration test for T022: MSE Comparison Logic.
Verifies that the MSE reduction calculation and threshold logic work correctly.
"""
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the function to test
from code.us2.mse_comparison import run_mse_comparison, compute_mse_reduction
from code.config import PROCESSED_PATH


@pytest.fixture
def mock_interaction_data():
    """
    Create a mock interaction_terms.csv with known properties:
    - Main effects: Cr, Mo
    - Interaction: Cr_Mo
    - Target: y (segregation energy)
    
    We construct data where the interaction term significantly improves prediction.
    y = 2*Cr + 3*Mo + 5*(Cr*Mo) + noise
    """
    np.random.seed(42)
    n_samples = 100
    
    Cr = np.random.uniform(0, 1, n_samples)
    Mo = np.random.uniform(0, 1, n_samples)
    Cr_Mo = Cr * Mo
    
    # True model: strong interaction
    y = 2.0 * Cr + 3.0 * Mo + 5.0 * Cr_Mo + np.random.normal(0, 0.1, n_samples)
    
    df = pd.DataFrame({
        'Cr': Cr,
        'Mo': Mo,
        'Cr_Mo': Cr_Mo,
        'target': y
    })
    return df


def test_compute_mse_reduction_logic():
    """Test the percentage calculation logic."""
    # Case 1: Perfect reduction (full model MSE is 0)
    assert compute_mse_reduction(10.0, 0.0) == 100.0
    
    # Case 2: No reduction
    assert compute_mse_reduction(10.0, 10.0) == 0.0
    
    # Case 3: 15% reduction
    # (10 - 8.5) / 10 = 0.15 -> 15%
    assert abs(compute_mse_reduction(10.0, 8.5) - 15.0) < 1e-6
    
    # Case 4: Increase in MSE (negative reduction)
    assert compute_mse_reduction(10.0, 12.0) == -20.0


def test_mse_comparison_integration(mock_interaction_data, tmp_path):
    """
    End-to-end test:
    1. Write mock data to temp CSV.
    2. Run T022 logic.
    3. Verify output JSON exists and contains expected keys.
    4. Verify that cooperative effects are detected (since we injected strong interaction).
    """
    # Setup paths
    input_file = tmp_path / "interaction_terms.csv"
    output_file = tmp_path / "mse_comparison.json"
    
    # Write mock data
    mock_interaction_data.to_csv(input_file, index=False)
    
    # Run the task logic
    results = run_mse_comparison(input_file, output_file)
    
    # Assertions
    assert output_file.exists(), "Output JSON file was not created."
    
    with open(output_file, 'r') as f:
        saved_results = json.load(f)
    
    assert "mse_additive_binary" in saved_results
    assert "mse_interaction_model" in saved_results
    assert "mse_reduction_percent" in saved_results
    assert "cooperative_effects_detected" in saved_results
    
    # Since we injected a strong interaction term (coeff 5.0), 
    # the reduction should be significant (> 10%)
    assert saved_results["cooperative_effects_detected"] is True
    assert saved_results["mse_reduction_percent"] > 10.0


def test_no_cooperative_effects_scenario(mock_interaction_data, tmp_path):
    """
    Test scenario where interaction term is weak/zero.
    We modify the target to remove the interaction component.
    """
    # Create data with NO interaction effect
    np.random.seed(42)
    n_samples = 100
    Cr = np.random.uniform(0, 1, n_samples)
    Mo = np.random.uniform(0, 1, n_samples)
    Cr_Mo = Cr * Mo
    
    # y depends only on main effects
    y = 2.0 * Cr + 3.0 * Mo + np.random.normal(0, 0.1, n_samples)
    
    df = pd.DataFrame({
        'Cr': Cr,
        'Mo': Mo,
        'Cr_Mo': Cr_Mo,
        'target': y
    })
    
    input_file = tmp_path / "interaction_terms_no_effect.csv"
    output_file = tmp_path / "mse_comparison_no_effect.json"
    
    df.to_csv(input_file, index=False)
    
    # Run logic
    results = run_mse_comparison(input_file, output_file)
    
    # Should NOT detect cooperative effects
    assert results["cooperative_effects_detected"] is False
    assert results["mse_reduction_percent"] <= 10.0