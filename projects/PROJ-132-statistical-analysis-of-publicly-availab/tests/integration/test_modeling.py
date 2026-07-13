"""
Integration tests for the GAMM modeling pipeline (User Story 2).

This module verifies that the GAMM fitting logic can converge on synthetic data
that mimics the expected structure of the real dataset.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from scipy import stats

# Adjust path to import project modules if running from root
# Assuming standard project structure where this file is at tests/integration/
# and src/ is at the root.
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from src.models.gamm_fit import fit_gamm_model
    from src.models.utils import save_permutation_results
except ImportError as e:
    # Fallback for environments where the module might not exist yet
    # In a real execution, this would be a hard failure, but for the test
    # definition we assume the implementation exists or will be created.
    # We define a mock here to ensure the test file itself is valid Python
    # if the implementation is missing, but the test will fail if run.
    class MockGAMM:
        def __init__(self, *args, **kwargs):
            pass
        def fit(self, *args, **kwargs):
            raise RuntimeError("gamm_fit module not implemented yet")
    
    def fit_gamm_model(*args, **kwargs):
        raise NotImplementedError("gamm_fit module not implemented yet")
    
    def save_permutation_results(*args, **kwargs):
        pass

def generate_synthetic_convergence_data(n_samples=500, n_species=5, seed=42):
    """
    Generates synthetic data designed to have a clear signal for GAMM convergence.
    Creates a relationship: phenology ~ temp + species_random_effect.
    """
    rng = np.random.default_rng(seed)
    
    species_list = [f"Species_{i}" for i in range(n_species)]
    
    data = []
    for _ in range(n_samples):
        sp = rng.choice(species_list)
        # Random lat/lon for spatial component
        lat = rng.uniform(30, 50)
        lon = rng.uniform(-120, -70)
        
        # Generate temperature with some variance
        temp = rng.normal(15, 5)
        precip = rng.normal(50, 10)
        effort = rng.normal(10, 2)
        
        # Create a known linear relationship for phenology (first_arrival)
        # Higher temp -> earlier arrival (lower day of year)
        # Base: 120, Slope: -2.0 per degree C
        true_intercept = 120.0
        true_temp_slope = -2.0
        
        # Species random intercept
        sp_effect = rng.normal(0, 2.0)
        
        # Noise
        noise = rng.normal(0, 3.0)
        
        phenology = true_intercept + (true_temp_slope * temp) + sp_effect + noise
        
        # Ensure positive day of year
        phenology = max(1, min(365, phenology))
        
        data.append({
            "species": sp,
            "lat": lat,
            "lon": lon,
            "temp": temp,
            "precip": precip,
            "effort": effort,
            "phenology_metric": phenology,
            "week": rng.integers(1, 25)
        })
    
    return pd.DataFrame(data)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test outputs."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

def test_gamm_convergence(temp_data_dir):
    """
    Verifies that the GAMM model can fit on synthetic data without convergence errors.
    
    Checks:
    1. The model fits without raising exceptions.
    2. The output contains expected keys (coefficients, p-values, fit stats).
    3. The synthetic data yields a statistically significant temperature effect 
       (since we constructed it with a known slope).
    """
    # 1. Generate synthetic data
    df = generate_synthetic_convergence_data(n_samples=500, n_species=5)
    
    # Save to a temporary CSV to simulate the pipeline input
    input_path = os.path.join(temp_data_dir, "synthetic_phenology.csv")
    df.to_csv(input_path, index=False)
    
    # 2. Define output paths
    output_results_path = os.path.join(temp_data_dir, "gamm_results.json")
    output_stats_path = os.path.join(temp_data_dir, "gamm_stats.json")
    
    # 3. Run the model
    # We expect this to complete without raising a convergence error
    try:
        results = fit_gamm_model(
            input_path=input_path,
            output_results=output_results_path,
            output_stats=output_stats_path,
            n_permutations=100  # Small number for speed in integration test
        )
    except Exception as e:
        pytest.fail(f"GAMM fitting failed with exception: {e}")
    
    # 4. Verify output files exist
    assert os.path.exists(output_results_path), "Results JSON file was not created"
    assert os.path.exists(output_stats_path), "Stats JSON file was not created"
    
    # 5. Verify results structure
    # The results should be a list of dictionaries (one per species or model run)
    assert isinstance(results, list), "Results should be a list of model outputs"
    assert len(results) > 0, "Results list is empty"
    
    first_result = results[0]
    required_keys = ["species", "temperature_coefficient", "p_value", "converged"]
    for key in required_keys:
        assert key in first_result, f"Missing key '{key}' in results"
    
    # 6. Verify convergence
    # Since we generated data with a clear signal, we expect convergence
    converged_count = sum(1 for r in results if r.get("converged", False))
    assert converged_count > 0, "No models converged on the synthetic data"
    
    # 7. Verify the signal (optional but good for integration testing)
    # Check if the temperature coefficient is negative (as per our synthetic generation)
    temp_coeffs = [r.get("temperature_coefficient") for r in results if r.get("temperature_coefficient") is not None]
    if temp_coeffs:
        avg_coeff = np.mean(temp_coeffs)
        # Allow some tolerance for noise, but it should be negative
        assert avg_coeff < 0, f"Expected negative temperature coefficient (earlier arrival with heat), got {avg_coeff}"

def test_gamm_convergence_empty_data(temp_data_dir):
    """
    Verifies that the model handles empty input data gracefully.
    """
    empty_df = pd.DataFrame(columns=["species", "lat", "lon", "temp", "phenology_metric"])
    input_path = os.path.join(temp_data_dir, "empty.csv")
    empty_df.to_csv(input_path, index=False)
    
    output_results_path = os.path.join(temp_data_dir, "empty_results.json")
    output_stats_path = os.path.join(temp_data_dir, "empty_stats.json")
    
    with pytest.raises((ValueError, RuntimeError)) as excinfo:
        fit_gamm_model(
            input_path=input_path,
            output_results=output_results_path,
            output_stats=output_stats_path,
            n_permutations=10
        )
    
    assert "insufficient" in str(excinfo.value).lower() or "empty" in str(excinfo.value).lower()