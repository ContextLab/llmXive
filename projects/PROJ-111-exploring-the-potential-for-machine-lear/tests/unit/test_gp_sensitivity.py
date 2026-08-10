import os
import sys
import pytest
import numpy as np
import tempfile
import csv
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from analysis import run_gp_sensitivity_analysis, calculate_total_variance_per_bin

@pytest.fixture
def mock_latent_data(tmp_path):
    """Create mock latent data for testing."""
    latent_dir = tmp_path / "latent_test"
    latent_dir.mkdir()
    
    # Create synthetic latent data that mimics a phase transition
    # Temperatures from 0.1 to 3.0
    temperatures = np.linspace(0.1, 3.0, 30)
    n_samples = 100
    
    # Create a variance peak around T=2.2 (typical XY transition region)
    # Add noise
    base_variance = np.ones_like(temperatures) * 0.1
    peak_idx = np.argmin(np.abs(temperatures - 2.2))
    gaussian_peak = 0.5 * np.exp(-((temperatures - 2.2) / 0.2)**2)
    variances = base_variance + gaussian_peak + np.random.normal(0, 0.02, len(temperatures))
    
    # Expand to batch dimension for latent_mu
    # latent_mu shape: (N_samples_total, latent_dim)
    # We'll fake it: 30 temps * 100 samples = 3000
    n_total = len(temperatures) * n_samples
    latent_dim = 10
    
    latent_mu = np.zeros((n_total, latent_dim))
    expanded_temps = np.repeat(temperatures, n_samples)
    
    # Add some structure to latent_mu to make variance meaningful
    for i, t in enumerate(expanded_temps):
        # Simple function of temperature
        latent_mu[i, 0] = np.sin(t) + np.random.normal(0, 0.1)
        latent_mu[i, 1] = np.cos(t) + np.random.normal(0, 0.1)
    
    # Save files
    np.save(latent_dir / "latent_mu.npy", latent_mu)
    np.save(latent_dir / "temperatures.npy", expanded_temps)
    np.save(latent_dir / "latent_var.npy", np.zeros((n_total, latent_dim))) # Not used by variance calc but required by loader
    
    return str(latent_dir)

def test_run_gp_sensitivity_analysis(mock_latent_data, tmp_path):
    """Test the GP sensitivity analysis sweep."""
    output_dir = tmp_path / "results"
    output_dir.mkdir()
    output_csv = output_dir / "gp_sensitivity.csv"
    
    length_scales = [0.1, 0.5, 1.0, 2.0]
    
    results = run_gp_sensitivity_analysis(
        latent_dir=mock_latent_data,
        output_path=str(output_csv),
        length_scales=length_scales
    )
    
    # Verify output file exists
    assert output_csv.exists(), "Output CSV file was not created."
    
    # Verify results structure
    assert "results" in results
    assert "stability" in results
    assert len(results["results"]) == len(length_scales)
    
    # Verify CSV content
    with open(output_csv, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == len(length_scales)
        
        for i, row in enumerate(rows):
            assert float(row['length_scale']) == length_scales[i]
            assert row['status'] == 'success'
            # Peak temperature should be a number
            assert float(row['peak_temperature']) > 0.0

def test_gp_sensitivity_stability(mock_latent_data, tmp_path):
    """Test that the stability metric is calculated correctly."""
    output_dir = tmp_path / "results"
    output_dir.mkdir()
    output_csv = output_dir / "gp_sensitivity.csv"
    
    # Use a very narrow set of length scales that should yield similar results
    length_scales = [1.0, 1.1]
    
    results = run_gp_sensitivity_analysis(
        latent_dir=mock_latent_data,
        output_path=str(output_csv),
        length_scales=length_scales
    )
    
    assert results["stability"]["is_stable"] is True
    assert results["stability"]["mean_peak_temp"] is not None

def test_gp_sensitivity_missing_data(tmp_path):
    """Test handling of missing data directory."""
    output_dir = tmp_path / "results"
    output_dir.mkdir()
    output_csv = output_dir / "gp_sensitivity.csv"
    
    with pytest.raises(RuntimeError) as excinfo:
        run_gp_sensitivity_analysis(
            latent_dir=str(tmp_path / "non_existent"),
            output_path=str(output_csv)
        )
    assert "Failed to load latent data" in str(excinfo.value)