"""
Validation module for the Early Universe Phase Transition pipeline.

This module implements validation routines for both Inflation and Phase Transition
synthetic datasets to verify the inference pipeline's accuracy and reliability.
"""

import json
import os
import sys
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
from scipy.special import erf

# Import from sibling modules
from synthetic_data import generate_phase_transition_dataset, save_dataset
from inference import run_nested_sampling, check_convergence
from model_generation import generate_theoretical_spectrum
from config import get_config, init_reproducibility

# Constants
TRUE_E_PT = 1.0e15  # True energy scale for Phase Transition (GeV)
TRUE_E_PT_LOG = np.log10(TRUE_E_PT)
CREDIBLE_INTERVAL = 0.95
CENTERING_THRESHOLD = 0.10


def run_inference_on_synthetic_phase_transition(
    synthetic_data: Dict[str, Any],
    n_live_points: int = 50,
    n_walks: int = 10
) -> Tuple[Dict[str, Any], bool]:
    """
    Run nested sampling inference on synthetic Phase Transition data.
    
    Args:
        synthetic_data: Dictionary containing 'l_values', 'cl_values', 'noise_cl'
        n_live_points: Number of live points for nested sampling
        n_walks: Number of walks for the sampler
        
    Returns:
        Tuple of (results_dict, convergence_status)
    """
    # Extract data
    l_values = synthetic_data['l_values']
    cl_values = synthetic_data['cl_values']
    noise_cl = synthetic_data['noise_cl']
    
    # Define log-likelihood for Phase Transition model
    def log_likelihood(theta):
        log_E_pt = theta[0]
        E_pt = 10 ** log_E_pt
        
        # Generate theoretical spectrum for this E_pt
        model_spec = generate_theoretical_spectrum(
            model_type='phase_transition',
            E_PT=E_pt,
            l_values=l_values
        )
        
        # Compute chi-squared
        diff = model_spec['cl_values'] - cl_values
        variance = noise_cl ** 2 + 1e-10  # Prevent division by zero
        chi2 = np.sum((diff ** 2) / variance)
        
        return -0.5 * chi2
    
    # Define prior transform (log-uniform for E_pt in [10^14, 10^16] GeV)
    def prior_transform(u):
        # u is in [0, 1], map to log10(E_pt) in [14, 16]
        log_E_pt = 14.0 + 2.0 * u[0]
        return np.array([log_E_pt])
    
    # Run nested sampling
    results, convergence = run_nested_sampling(
        log_likelihood=log_likelihood,
        prior_transform=prior_transform,
        ndim=1,
        n_live_points=n_live_points,
        n_walks=n_walks
    )
    
    # Extract posterior samples and statistics
    samples = results.samples
    log_E_pt_samples = samples[:, 0]
    E_pt_samples = 10 ** log_E_pt_samples
    
    mean_log_E_pt = np.mean(log_E_pt_samples)
    std_log_E_pt = np.std(log_E_pt_samples)
    mean_E_pt = np.mean(E_pt_samples)
    
    # Compute credible intervals
    lower_percentile = (1 - CREDIBLE_INTERVAL) / 2 * 100
    upper_percentile = (1 + CREDIBLE_INTERVAL) / 2 * 100
    
    log_E_pt_ci_low = np.percentile(log_E_pt_samples, lower_percentile)
    log_E_pt_ci_high = np.percentile(log_E_pt_samples, upper_percentile)
    E_pt_ci_low = 10 ** log_E_pt_ci_low
    E_pt_ci_high = 10 ** log_E_pt_ci_high
    
    # Compute evidence
    log_evidence = results.logz[-1]
    log_evidence_err = results.logzerr[-1]
    
    results_dict = {
        'mean_log_E_pt': float(mean_log_E_pt),
        'std_log_E_pt': float(std_log_E_pt),
        'mean_E_pt': float(mean_E_pt),
        'ci_low_E_pt': float(E_pt_ci_low),
        'ci_high_E_pt': float(E_pt_ci_high),
        'log_evidence': float(log_evidence),
        'log_evidence_err': float(log_evidence_err),
        'samples': E_pt_samples.tolist(),
        'converged': convergence,
        'true_E_pt': TRUE_E_PT,
        'true_log_E_pt': TRUE_E_PT_LOG
    }
    
    return results_dict, convergence


def validate_phase_transition_pipeline(
    synthetic_data: Optional[Dict[str, Any]] = None,
    save_results: bool = True,
    results_path: str = 'data/derived/phase_transition_validation.json'
) -> Dict[str, Any]:
    """
    Validate the pipeline on synthetic Phase Transition data.
    
    This function:
    1. Generates synthetic Phase Transition data if not provided
    2. Runs the inference pipeline
    3. Verifies that the posterior for E_PT covers the true value within 95% CI
    4. Verifies that the posterior is centered within 10% of the true value
    
    Args:
        synthetic_data: Pre-generated synthetic data (optional)
        save_results: Whether to save results to disk
        results_path: Path for saving results
        
    Returns:
        Dictionary with validation results and metrics
    """
    # Initialize reproducibility
    init_reproducibility()
    
    # Generate synthetic data if not provided
    if synthetic_data is None:
        print("Generating synthetic Phase Transition dataset...")
        synthetic_data = generate_phase_transition_dataset(
            E_PT=TRUE_E_PT,
            n_sims=1,
            l_max=200
        )
        if save_results:
            save_dataset(synthetic_data, 'data/synthetic/phase_transition_ground_truth.json')
    
    print(f"Running inference on Phase Transition data (True E_PT = {TRUE_E_PT:.2e} GeV)...")
    
    # Run inference
    results, converged = run_inference_on_synthetic_phase_transition(synthetic_data)
    
    if not converged:
        print("WARNING: Nested sampling did not converge!")
    
    # Extract metrics
    true_E_pt = results['true_E_pt']
    mean_E_pt = results['mean_E_pt']
    ci_low = results['ci_low_E_pt']
    ci_high = results['ci_high_E_pt']
    
    # Check coverage: true value within 95% credible interval
    covers_true = ci_low <= true_E_pt <= ci_high
    
    # Check centering: |(mean - true)| / true < 0.10
    relative_error = abs(mean_E_pt - true_E_pt) / true_E_pt
    is_centered = relative_error < CENTERING_THRESHOLD
    
    # Overall validation
    validation_passed = covers_true and is_centered and converged
    
    validation_result = {
        'task_id': 'T025b',
        'validation_type': 'phase_transition',
        'true_E_pt_GeV': true_E_pt,
        'mean_E_pt_GeV': mean_E_pt,
        'ci_low_E_pt_GeV': ci_low,
        'ci_high_E_pt_GeV': ci_high,
        'credible_interval': CREDIBLE_INTERVAL,
        'covers_true_value': covers_true,
        'relative_error': relative_error,
        'centering_threshold': CENTERING_THRESHOLD,
        'is_centered': is_centered,
        'converged': converged,
        'validation_passed': validation_passed,
        'log_evidence': results['log_evidence'],
        'log_evidence_err': results['log_evidence_err']
    }
    
    # Print results
    print("\n" + "="*60)
    print("PHASE TRANSITION VALIDATION RESULTS")
    print("="*60)
    print(f"True E_PT:           {true_E_pt:.2e} GeV")
    print(f"Mean E_PT:           {mean_E_pt:.2e} GeV")
    print(f"95% CI:              [{ci_low:.2e}, {ci_high:.2e}] GeV")
    print(f"Covers True Value:   {covers_true}")
    print(f"Relative Error:      {relative_error:.4f} ({relative_error*100:.2f}%)")
    print(f"Centered (<10%):     {is_centered}")
    print(f"Converged:           {converged}")
    print(f"Validation Passed:   {validation_passed}")
    print("="*60 + "\n")
    
    # Save results
    if save_results:
        os.makedirs(os.path.dirname(results_path), exist_ok=True)
        with open(results_path, 'w') as f:
            json.dump(validation_result, f, indent=2)
        print(f"Results saved to: {results_path}")
    
    if not validation_passed:
        reasons = []
        if not covers_true:
            reasons.append("True value outside 95% CI")
        if not is_centered:
            reasons.append(f"Relative error {relative_error:.4f} exceeds threshold {CENTERING_THRESHOLD}")
        if not converged:
            reasons.append("Sampler did not converge")
        raise ValueError(f"Phase transition validation failed: {'; '.join(reasons)}")
    
    return validation_result


def main():
    """Main entry point for Phase Transition validation."""
    print("Starting Phase Transition Pipeline Validation (T025b)...")
    
    try:
        result = validate_phase_transition_pipeline()
        print("\n✓ Phase Transition validation PASSED")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Phase Transition validation FAILED: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()