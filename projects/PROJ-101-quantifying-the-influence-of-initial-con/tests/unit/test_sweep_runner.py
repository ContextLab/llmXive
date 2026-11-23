"""
Unit tests for T045: Sweep Runner.

Verifies that the sweep execution correctly aggregates results 
across window sizes and noise levels.
"""

import pytest
import numpy as np
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from analysis.sweep_runner import run_full_sweep, save_sweep_results, WINDOW_SIZES
from analysis.ftle import FTLEResult
from data.loader import load_trajectory

@pytest.fixture
def mock_config():
    """Mock config to return specific N and noise levels."""
    mock_config = MagicMock()
    mock_config.simulation.noise_levels = [0.0, 0.1]
    mock_config.simulation.n_oscillators = [5]
    return mock_config

@pytest.fixture
def mock_baseline():
    """Mock baseline data."""
    return {
        "lambda_max": 0.9056,
        "error_estimate": 1e-6,
        "converged": True
    }

@pytest.fixture
def mock_trajectory_data():
    """Mock trajectory data with shape (1000, 15) for N=5."""
    # N=5 oscillators -> 5 * 3 = 15 dimensions
    states = np.random.randn(1000, 15) * 0.1
    return {
        "states": states,
        "dt": 0.01
    }

@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary raw and processed directories."""
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    
    # Create a dummy baseline file
    baseline_file = processed_dir / "baseline_5.json"
    with open(baseline_file, 'w') as f:
        json.dump({"lambda_max": 0.9, "error_estimate": 1e-6, "converged": True}, f)
    
    # Create a dummy trajectory file
    traj_file = raw_dir / "trajectory_N5_sigma0.0000.npz"
    np.savez_compressed(str(traj_file), states=np.random.randn(1000, 15), dt=0.01)
    
    return raw_dir, processed_dir

def test_run_full_sweep_aggregation(temp_dirs, mock_config, mock_baseline, mock_trajectory_data):
    """
    Test that run_full_sweep aggregates results for all T values.
    """
    raw_dir, processed_dir = temp_dirs
    
    # Mock dependencies
    with patch('analysis.sweep_runner.get_full_config', return_value=mock_config), \
         patch('analysis.sweep_runner.load_baseline_result', return_value=mock_baseline), \
         patch('analysis.sweep_runner.validate_and_gate_for_baseline'), \
         patch('analysis.sweep_runner.load_trajectory', return_value=mock_trajectory_data), \
         patch('analysis.sweep_runner.check_numerical_validity'), \
         patch('analysis.sweep_runner.run_sliding_window_sweep') as mock_sweep:
         
         # Mock the sweep to return FTLEResult objects for each T
         mock_results = [
             FTLEResult(window_size=T, lambda_max=0.9 + T*0.001, error_estimate=1e-6)
             for T in WINDOW_SIZES
         ]
         mock_sweep.return_value = mock_results
         
         results = run_full_sweep(
             data_dir=raw_dir,
             processed_dir=processed_dir,
             baseline_file="baseline_5.json"
         )
         
         # Verify we got results for each T
         assert len(results) == len(WINDOW_SIZES)
         
         # Verify structure
         for res in results:
             assert "N" in res
             assert "sigma_noise" in res
             assert "window_size_T" in res
             assert "lambda_max" in res
             assert res["window_size_T"] in WINDOW_SIZES

def test_save_sweep_results(tmp_path):
    """Test saving results to JSON."""
    results = [
        {"N": 5, "sigma_noise": 0.1, "window_size_T": 500, "lambda_max": 0.91},
        {"N": 5, "sigma_noise": 0.1, "window_size_T": 1000, "lambda_max": 0.92}
    ]
    output_file = tmp_path / "results.json"
    
    save_sweep_results(results, output_file)
    
    assert output_file.exists()
    with open(output_file) as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert data[0]["window_size_T"] == 500
