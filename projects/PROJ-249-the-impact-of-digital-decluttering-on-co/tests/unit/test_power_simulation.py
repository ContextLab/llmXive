import pytest
import os
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
from code.analysis.power_simulation import (
    run_power_simulation_iteration, 
    simulate_post_intervention, 
    run_power_simulation
)
from code.utils.random_seed import set_global_seed

@pytest.fixture
def mock_baseline_data():
    """Fixture to provide mock baseline data."""
    return [
        {'participant_id': 'P001', 'metric_type': 'SART', 'value': 10.0},
        {'participant_id': 'P002', 'metric_type': 'SART', 'value': 12.0},
        {'participant_id': 'P003', 'metric_type': 'SART', 'value': 9.0},
        {'participant_id': 'P001', 'metric_type': 'Ospan', 'value': 40.0},
        {'participant_id': 'P002', 'metric_type': 'Ospan', 'value': 42.0},
        {'participant_id': 'P003', 'metric_type': 'Ospan', 'value': 38.0},
    ]

@pytest.fixture
def rng():
    """Fixture for a seeded numpy random generator."""
    set_global_seed(42)
    from code.utils.random_seed import get_rng
    return get_rng(42)

def test_simulate_post_intervention(rng):
    """Test that post-intervention values are shifted by the effect size."""
    baseline = [10.0, 12.0, 14.0]
    effect_size = 0.5
    std_dev = 2.0
    
    post = simulate_post_intervention(baseline, effect_size, std_dev, rng)
    
    assert len(post) == len(baseline)
    # The mean of post should be roughly mean(baseline) + effect_size * std_dev
    mean_baseline = np.mean(baseline)
    expected_shift = effect_size * std_dev
    mean_post = np.mean(post)
    
    # Allow some tolerance due to noise
    assert abs(mean_post - (mean_baseline + expected_shift)) < 1.0

def test_run_power_simulation_iteration(rng, mock_baseline_data):
    """Test a single iteration of the power simulation."""
    metrics = ['SART', 'Ospan']
    effect_size = 0.5
    alpha = 0.05
    
    result = run_power_simulation_iteration(
        metrics=metrics,
        baseline_data=mock_baseline_data,
        effect_size=effect_size,
        alpha=alpha,
        rng=rng
    )
    
    assert "detected" in result
    assert "raw_p_values" in result
    assert "corrected_p_values" in result
    assert "metrics" in result
    
    # Check that we have results for the metrics
    assert len(result["metrics"]) > 0
    assert len(result["raw_p_values"]) == len(result["metrics"])
    assert len(result["corrected_p_values"]) == len(result["metrics"])

@patch('code.analysis.power_simulation.load_synthetic_baseline_data')
def test_run_power_simulation(mock_load_data, rng):
    """Test the full power simulation pipeline."""
    mock_data = [
        {'participant_id': 'P001', 'metric_type': 'SART', 'value': 10.0},
        {'participant_id': 'P002', 'metric_type': 'SART', 'value': 12.0},
        {'participant_id': 'P003', 'metric_type': 'SART', 'value': 9.0},
    ]
    mock_load_data.return_value = mock_data
    
    # Run a small simulation
    results = run_power_simulation(n_iterations=10, effect_size=0.5, alpha=0.05, seed=42)
    
    assert "simulation_parameters" in results
    assert "results" in results
    assert "power" in results["results"]
    assert 0.0 <= results["results"]["power"] <= 1.0
    
    assert results["simulation_parameters"]["n_iterations"] == 10
    assert results["simulation_parameters"]["effect_size"] == 0.5
    
    # Check details structure
    assert "details" in results
    assert "sample_iterations" in results["details"]