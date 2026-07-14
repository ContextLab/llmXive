"""
Integration test for Nested Sampling convergence (Task T019).
Tests that dynesty converges correctly on synthetic data and that
the posterior covers the true value within the 95% credible interval.
"""
import json
import os
import sys
import pytest
import numpy as np

# Ensure parent directory is in path to import code modules
_code_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
if _code_path not in sys.path:
    sys.path.insert(0, _code_path)

from synthetic_data import generate_inflation_dataset, save_dataset
from inference import run_nested_sampling, check_convergence
from config import init_reproducibility, get_config

# Constants for the test
TEST_OUTPUT_DIR = "data/synthetic/test_inference"
TRUE_R_VALUE = 0.01
N_LIVE_POINTS = 50
N_EFF_THRESHOLD = 100  # Minimum effective sample size for convergence
COVERAGE_TOLERANCE = 0.10  # 10% tolerance for centering

def setup_module(module):
    """Ensure output directories exist."""
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    init_reproducibility()

def test_nested_sampling_convergence_inflation():
    """
    Integration test:
    1. Generate synthetic inflation data with known r=0.01.
    2. Run nested sampling (dynesty).
    3. Verify convergence (ns_run is not None, evidence stable).
    4. Verify posterior covers true value (95% CI) and is centered within 10%.
    """
    # 1. Generate Synthetic Data
    # Use a fixed seed for the data generation to ensure reproducibility of the "observation"
    np.random.seed(42)
    data_dict = generate_inflation_dataset(r_true=TRUE_R_VALUE, noise_level=1e-5)
    
    # Save to disk as required by the pipeline (real file artifact)
    data_path = os.path.join(TEST_OUTPUT_DIR, "synthetic_inflation_obs.json")
    with open(data_path, "w") as f:
        json.dump(data_dict, f)

    # 2. Run Nested Sampling
    # Load the config to ensure we are using the correct priors
    config = get_config()
    
    # We assume the inference module can load from a file or dict
    # Here we pass the loaded dict directly to the function
    with open(data_path, "r") as f:
        observed_data = json.load(f)

    # Run the sampler
    # Note: We use a small number of maxiter for integration speed, 
    # but enough to check convergence logic.
    result = run_nested_sampling(
        observed_data=observed_data,
        model_type="inflation",
        n_live=N_LIVE_POINTS,
        maxiter=5000
    )

    # 3. Verify Convergence
    # The run_nested_sampling function should return a result object or None if failed
    assert result is not None, "Nested sampling failed to produce a result."
    
    # Check convergence criteria (evidence stability or ntol)
    is_converged = check_convergence(result)
    assert is_converged, f"Nested sampling did not converge. LogZ: {result.logz}, dlogz: {result.logzerr}"

    # 4. Verify Posterior Statistics
    # Extract posterior samples for 'r'
    samples = result.samples
    r_samples = samples[:, 0] # Assuming first param is r

    # Calculate 95% Credible Interval
    lower_95 = np.percentile(r_samples, 2.5)
    upper_95 = np.percentile(r_samples, 97.5)
    mean_r = np.mean(r_samples)

    # Metric 1: True value within 95% CI
    covers_true = lower_95 <= TRUE_R_VALUE <= upper_95
    assert covers_true, f"True r ({TRUE_R_VALUE}) not in 95% CI [{lower_95:.4f}, {upper_95:.4f}]"

    # Metric 2: Centered within 10%
    relative_error = abs(mean_r - TRUE_R_VALUE) / TRUE_R_VALUE
    is_centered = relative_error < COVERAGE_TOLERANCE
    assert is_centered, f"Posterior mean ({mean_r:.4f}) not within 10% of true value ({TRUE_R_VALUE}). Error: {relative_error:.2%}"

    print(f"Test Passed: r={TRUE_R_VALUE}, Mean={mean_r:.4f}, 95% CI=[{lower_95:.4f}, {upper_95:.4f}]")

def test_nested_sampling_convergence_phase_transition():
    """
    Integration test for Phase Transition model.
    Verifies convergence and recovery of E_PT.
    """
    TRUE_E_PT = 1.0e15  # 10^15 GeV
    
    # Generate synthetic data
    np.random.seed(123)
    data_dict = generate_inflation_dataset(r_true=0.001, noise_level=1e-5, include_pt=True, E_PT_true=TRUE_E_PT)
    
    data_path = os.path.join(TEST_OUTPUT_DIR, "synthetic_pt_obs.json")
    with open(data_path, "w") as f:
        json.dump(data_dict, f)

    with open(data_path, "r") as f:
        observed_data = json.load(f)

    # Run sampler for Phase Transition model
    result = run_nested_sampling(
        observed_data=observed_data,
        model_type="phase_transition",
        n_live=N_LIVE_POINTS,
        maxiter=5000
    )

    assert result is not None, "Nested sampling failed for PT model."
    
    is_converged = check_convergence(result)
    assert is_converged, "Nested sampling did not converge for PT model."

    # Extract E_PT samples (assuming index 1 or specific handling in inference)
    # The inference module maps params to indices. 
    # For PT model, typically [r, E_PT].
    samples = result.samples
    if samples.shape[1] >= 2:
        e_pt_samples = samples[:, 1]
    else:
        # Fallback if model only returns one param, though PT usually needs E_PT
        e_pt_samples = samples[:, 0] 

    lower_95 = np.percentile(e_pt_samples, 2.5)
    upper_95 = np.percentile(e_pt_samples, 97.5)
    mean_e_pt = np.mean(e_pt_samples)

    # Check coverage
    covers_true = lower_95 <= TRUE_E_PT <= upper_95
    assert covers_true, f"True E_PT ({TRUE_E_PT}) not in 95% CI [{lower_95:.2e}, {upper_95:.2e}]"

    # Check centering (10% tolerance)
    relative_error = abs(mean_e_pt - TRUE_E_PT) / TRUE_E_PT
    is_centered = relative_error < COVERAGE_TOLERANCE
    assert is_centered, f"Posterior mean ({mean_e_pt:.2e}) not within 10% of true E_PT ({TRUE_E_PT}). Error: {relative_error:.2%}"

    print(f"Test Passed: E_PT={TRUE_E_PT:.2e}, Mean={mean_e_pt:.2e}, 95% CI=[{lower_95:.2e}, {upper_95:.2e}]")

if __name__ == "__main__":
    # Allow running directly
    test_nested_sampling_convergence_inflation()
    test_nested_sampling_convergence_phase_transition()
    print("All integration tests passed.")
