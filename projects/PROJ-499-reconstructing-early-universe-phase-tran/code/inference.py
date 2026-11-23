"""
Inference module for Bayesian parameter estimation using dynesty Nested Sampling.

This module provides functions for running nested sampling on both observed and
synthetic B-mode polarization data to estimate parameters such as the tensor-to-scalar
ratio (r) and phase transition energy scale (E_PT).
"""
import os
import json
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from dynesty import NestedSampler
from dynesty.utils import resample_equal

import healpy as hp
from scipy.interpolate import interp1d

from config import get_config, init_reproducibility
from model_generation import generate_theoretical_spectrum
from utils import verify_checksum

# Constants
L_MIN = 2
L_MAX = 200
DL_MIN = 1e-2  # Minimum dL to avoid division by zero

def log_likelihood(params: np.ndarray, data_l: np.ndarray, data_cl: np.ndarray, 
                   model_type: str, **model_kwargs) -> float:
    """
    Compute the log-likelihood for observed power spectrum data given model parameters.
    
    Args:
        params: Array of model parameters [r] for inflation or [log10_E_PT] for PT.
        data_l: Array of l-values from observed data.
        data_cl: Array of C_l^BB values from observed data.
        model_type: Type of model ('inflation' or 'phase_transition').
        **model_kwargs: Additional keyword arguments for model generation.
        
    Returns:
        log_likelihood_value: The computed log-likelihood.
    """
    # Extract parameters
    if model_type == 'inflation':
        r = params[0]
        # Clamp r to physically meaningful range
        r = np.clip(r, 1e-5, 0.1)
        
        # Generate theoretical spectrum
        theo_result = generate_theoretical_spectrum(
            model_type='inflation',
            r=r,
            l_range=(L_MIN, L_MAX),
            l_step=1
        )
        
        theo_l = np.array(theo_result['l_values'])
        theo_cl = np.array(theo_result['cl_values'])
        
    elif model_type == 'phase_transition':
        log10_E_PT = params[0]
        E_PT = 10 ** log10_E_PT
        
        # Generate theoretical spectrum
        theo_result = generate_theoretical_spectrum(
            model_type='phase_transition',
            E_PT=E_PT,
            l_range=(L_MIN, L_MAX),
            l_step=1
        )
        
        theo_l = np.array(theo_result['l_values'])
        theo_cl = np.array(theo_result['cl_values'])
        
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Interpolate theoretical spectrum to match data l-values
    interp_func = interp1d(theo_l, theo_cl, kind='linear', 
                         bounds_error=False, fill_value=0.0)
    model_cl = interp_func(data_l)
    
    # Calculate chi-squared (assuming Gaussian errors with unit variance for simplicity)
    # In a real scenario, we would use actual measurement errors
    chi2 = np.sum(((data_cl - model_cl) / DL_MIN) ** 2)
    
    return -0.5 * chi2

def prior_transform(u: np.ndarray) -> np.ndarray:
    """
    Transform unit hypercube samples to physical parameter space.
    
    Args:
        u: Array of uniform random variables in [0, 1].
        
    Returns:
        params: Array of physical parameters.
    """
    # For inflation: r in [1e-5, 0.1] (log-uniform)
    # For phase transition: log10(E_PT) in [14, 16] (uniform)
    
    # We'll handle both cases in run_inference_synthetic by passing the transform
    # This is a placeholder; the actual transform is defined per model
    raise NotImplementedError("Prior transform should be defined per model")

def run_nested_sampling(log_likelihood_func, prior_transform_func, 
                      nlive: int = 50, maxiter: int = 1000, 
                      dlogz: float = 0.1) -> Dict[str, Any]:
    """
    Run nested sampling using dynesty.
    
    Args:
        log_likelihood_func: Function that computes log-likelihood.
        prior_transform_func: Function that transforms unit hypercube to physical space.
        nlive: Number of live points.
        maxiter: Maximum number of iterations.
        dlogz: Target precision for log-evidence.
        
    Returns:
        results: Dictionary containing posterior samples, evidence, and diagnostics.
    """
    sampler = NestedSampler(log_likelihood_func, prior_transform_func, 
                          ndim=1, nlive=nlive, dlogz=dlogz)
    
    sampler.run_nested(maxiter=maxiter)
    
    results = {
        'logz': sampler.results.logz,
        'logzerr': sampler.results.logzerr,
        'samples': sampler.results.samples,
        'loglikelihood': sampler.results.logl,
        'niter': sampler.results.ncall,
        'eff': sampler.results.eff
    }
    
    return results

def check_convergence(results: Dict[str, Any], threshold: float = 0.1) -> bool:
    """
    Check if nested sampling has converged based on evidence uncertainty.
    
    Args:
        results: Results dictionary from run_nested_sampling.
        threshold: Convergence threshold for logz error.
        
    Returns:
        converged: True if converged, False otherwise.
    """
    return results['logzerr'] < threshold

def run_inference_synthetic(input_file: str, output_file: str, 
                          model_type: str = 'inflation', 
                          true_params: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Run inference on synthetic B-mode data.
    
    This function loads synthetic B-mode maps from a FITS file, computes the
    angular power spectrum, and runs nested sampling to estimate model parameters.
    
    Args:
        input_file: Path to input synthetic B-mode map file (.fits).
        output_file: Path to output JSON file for inference results.
        model_type: Type of model to fit ('inflation' or 'phase_transition').
        true_params: Dictionary of true parameters used to generate synthetic data.
                    
    Returns:
        results: Dictionary containing inference results.
    """
    # Initialize reproducibility
    init_reproducibility()
    config = get_config()
    
    # Load synthetic data
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Read FITS file
    try:
        bmode_map = hp.read_map(input_file, field=2)  # B-mode component
    except Exception as e:
        raise RuntimeError(f"Failed to read FITS file: {e}")
    
    # Compute power spectrum
    cl_bb, l_values = hp.anafast(bmode_map, lmax=200, pol=True)
    # Extract B-B component (index 2 in [EE, EB, BB, ...] if pol=True)
    if isinstance(cl_bb, dict):
        cl_bb = cl_bb['BB']
    else:
        # If cl_bb is an array, assume it's already the BB spectrum
        cl_bb = cl_bb[2] if len(cl_bb) > 2 else cl_bb
    
    # Ensure we have valid l_values and cl_bb
    l_values = np.array(l_values)
    cl_bb = np.array(cl_bb)
    
    # Filter out l=0 and negative values
    mask = (l_values >= 2) & (cl_bb > 0)
    l_values = l_values[mask]
    cl_bb = cl_bb[mask]
    
    if len(l_values) == 0:
        raise ValueError("No valid l-values found in power spectrum")
    
    # Define log-likelihood function for this model
    def log_likelihood_func(params):
        return log_likelihood(params, l_values, cl_bb, model_type)
    
    # Define prior transform based on model type
    if model_type == 'inflation':
        def prior_transform_func(u):
            # r in [1e-5, 0.1] (log-uniform)
            return np.array([10 ** (u[0] * (np.log10(0.1) - np.log10(1e-5)) + np.log10(1e-5))])
    elif model_type == 'phase_transition':
        def prior_transform_func(u):
            # log10(E_PT) in [14, 16] (uniform)
            return np.array([u[0] * (16 - 14) + 14])
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    
    # Run nested sampling
    print(f"Running nested sampling for {model_type} model...")
    results = run_nested_sampling(log_likelihood_func, prior_transform_func, 
                                nlive=50, maxiter=1000, dlogz=0.1)
    
    # Check convergence
    converged = check_convergence(results)
    if not converged:
        print(f"Warning: Nested sampling may not have converged (logzerr={results['logzerr']:.3f})")
    
    # Extract posterior statistics
    samples = results['samples']
    posterior_mean = np.mean(samples, axis=0)
    posterior_std = np.std(samples, axis=0)
    posterior_median = np.median(samples, axis=0)
    posterior_16 = np.percentile(samples, 16, axis=0)
    posterior_84 = np.percentile(samples, 84, axis=0)
    posterior_2_5 = np.percentile(samples, 2.5, axis=0)
    posterior_97_5 = np.percentile(samples, 97.5, axis=0)
    
    # Prepare results dictionary
    inference_results = {
        'model_type': model_type,
        'input_file': input_file,
        'n_l_values': len(l_values),
        'l_range': [float(l_values[0]), float(l_values[-1])],
        'converged': converged,
        'logz': float(results['logz']),
        'logzerr': float(results['logzerr']),
        'n_iterations': int(results['niter']),
        'efficiency': float(results['eff']),
        'parameters': {}
    }
    
    # Add parameter-specific results
    if model_type == 'inflation':
        r_true = true_params.get('r', None) if true_params else None
        inference_results['parameters'] = {
            'r': {
                'mean': float(posterior_mean[0]),
                'std': float(posterior_std[0]),
                'median': float(posteroid_median[0]),
                '68%_CI': [float(posterior_16[0]), float(posterior_84[0])],
                '95%_CI': [float(posterior_2_5[0]), float(posterior_97_5[0])],
                'true_value': r_true
            }
        }
    elif model_type == 'phase_transition':
        E_PT_true = true_params.get('E_PT', None) if true_params else None
        inference_results['parameters'] = {
            'E_PT': {
                'mean': float(10 ** posterior_mean[0]),
                'std': float(10 ** posterior_std[0]),
                'median': float(10 ** posterior_median[0]),
                '68%_CI': [float(10 ** posterior_16[0]), float(10 ** posterior_84[0])],
                '95%_CI': [float(10 ** posterior_2_5[0]), float(10 ** posterior_97_5[0])],
                'true_value': E_PT_true
            }
        }
    
    # Save results to JSON
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(inference_results, f, indent=2)
    
    print(f"Inference results saved to {output_file}")
    return inference_results

def main():
    """Main function to run inference on synthetic data."""
    # Default paths
    input_file = "data/synthetic/inflation_synthetic.fits"
    output_file = "data/synthetic/inference_results_inflation.json"
    model_type = "inflation"
    true_params = {"r": 0.01}  # Default for inflation synthetic data
    
    # Run inference
    results = run_inference_synthetic(input_file, output_file, model_type, true_params)
    
    # Print summary
    print("\n=== Inference Summary ===")
    print(f"Model: {results['model_type']}")
    print(f"Converged: {results['converged']}")
    print(f"Log Evidence: {results['logz']:.3f} ± {results['logzerr']:.3f}")
    print(f"Efficiency: {results['efficiency']:.3f}")
    
    for param_name, param_data in results['parameters'].items():
        print(f"\n{param_name}:")
        print(f"  Mean: {param_data['mean']:.6f} ± {param_data['std']:.6f}")
        print(f"  Median: {param_data['median']:.6f}")
        print(f"  68% CI: [{param_data['68%_CI'][0]:.6f}, {param_data['68%_CI'][1]:.6f}]")
        print(f"  95% CI: [{param_data['95%_CI'][0]:.6f}, {param_data['95%_CI'][1]:.6f}]")
        if param_data.get('true_value') is not None:
            print(f"  True Value: {param_data['true_value']:.6f}")

if __name__ == "__main__":
    main()
