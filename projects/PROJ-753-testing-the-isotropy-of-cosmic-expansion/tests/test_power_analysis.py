import pytest
import numpy as np
import json
from pathlib import Path
from llmxive_toolkit import paths
from code.power_analysis import estimate_dipole_amplitude

def test_estimate_dipole_amplitude():
    """Test the weighted dipole estimator with a known signal."""
    # Create a synthetic dataset with a clear dipole
    # Residuals r = A * (n . d)
    N = 1000
    rng = np.random.RandomState(42)
    unit_vecs = rng.standard_normal((N, 3))
    unit_vecs /= np.linalg.norm(unit_vecs, axis=1)[:, None]
    
    dipole_dir = np.array([1.0, 0.0, 0.0])
    A = 0.05
    residuals = A * (unit_vecs @ dipole_dir)
    weights = np.ones(N)
    
    amp = estimate_dipole_amplitude(residuals, weights, unit_vecs)
    # The estimator should recover the amplitude A
    assert np.isclose(amp, A, atol=0.01)

def test_power_analysis_artifacts():
    """Verify that the power analysis produces the required JSON files."""
    # This test assumes code/power_analysis.py has been executed.
    meta_path = paths.data("raw", "metadata.json")
    power_path = paths.data("processed", "power_analysis.json")
    
    assert meta_path.exists(), "metadata.json should exist"
    assert power_path.exists(), "power_analysis.json should exist"
    
    with open(power_path, "r") as f:
        data = json.load(f)
        assert "analytic_min_detectable_dipole_mag" in data
        assert "empirical_power" in data
        assert data["num_supernovae"] > 0
        assert 0 <= data["empirical_power"] <= 1.0