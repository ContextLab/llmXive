import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import statsmodels.api as sm
from scipy.stats import norm

# Local imports (matching API surface)
from analysis.aggregation_utils import aggregate_power_results
from analysis.glm_fitter import fit_glm, estimate_effect_size, fit_glm_batch
from analysis.split_half_validator import run_split_half_validation
from preprocess.temporal_smoothing import apply_temporal_smoothing, load_roi_timeseries
from simulation.noise_estimator import estimate_noise_parameters
from utils.seed_manager import set_global_seed, get_seed
from utils.timer import log_split, start_run, end_run
from utils.bootstrap_aggregator import aggregate_power_results as agg_power_results_util

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def bootstrap_single_iteration(
    data: Dict[str, Any],
    sample_size: int,
    smoothing_kernel_seconds: float,
    seed: int
) -> Dict[str, Any]:
    """
    Perform a single bootstrap iteration for power analysis.
    
    Args:
        data: Preprocessed ROI timeseries data
        sample_size: Number of subjects to sample
        smoothing_kernel_seconds: Temporal smoothing kernel in seconds (e.g., 4.0, 8.0)
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary containing iteration results (effect_size, p_value, replication_success)
    """
    set_global_seed(seed)
    
    # Sample subjects
    subjects = list(data['subjects'])
    if len(subjects) < sample_size:
        # Clamp to available data (Edge Case 2)
        sample_size = len(subjects)
        logger.warning(f"Requested N={sample_size} but only {len(subjects)} available. Clamping.")
    
    sampled_subjects = np.random.choice(subjects, size=sample_size, replace=False)
    
    # Apply temporal smoothing (T013 dependency)
    smoothed_data = {}
    for subj in sampled_subjects:
        timeseries = data['timeseries'][subj]
        smoothed = apply_temporal_smoothing(
            timeseries, 
            kernel_fwhm=smoothing_kernel_seconds, 
            mode='temporal'
        )
        smoothed_data[subj] = smoothed
    
    # Estimate noise (T014 dependency)
    noise_params = estimate_noise_parameters(smoothed_data)
    
    # Fit GLM (T016 dependency)
    glm_results = fit_glm_batch(smoothed_data, noise_params=noise_params)
    
    # Split-half validation (T017 dependency)
    validation_result = run_split_half_validation(
        smoothed_data, 
        glm_results, 
        seed=seed + 1
    )
    
    return {
        'sample_size': sample_size,
        'kernel_seconds': smoothing_kernel_seconds,
        'effect_size': validation_result.get('effect_size_est'),
        'p_value': validation_result.get('p_value'),
        'replication_success': validation_result.get('replication_success', False),
        'noise_level': noise_params.get('residual_variance', 0.0),
        'seed': seed
    }

def run_bootstrap_loop(
    data: Dict[str, Any],
    sample_sizes: List[int],
    kernel_seconds: float,
    num_iterations: int,
    base_seed: int
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Run bootstrap loop for multiple sample sizes and iterations.
    
    Args:
        data: Preprocessed ROI data
        sample_sizes: List of sample sizes to test
        kernel_seconds: Temporal smoothing kernel (4s or 8s)
        num_iterations: Number of bootstrap iterations per sample size
        base_seed: Base random seed
    
    Returns:
        Dictionary mapping sample_size -> list of iteration results
    """
    all_results = {}
    
    for n in sample_sizes:
        logger.info(f"Running bootstrap for N={n}, kernel={kernel_seconds}s")
        iteration_results = []
        
        for i in range(num_iterations):
            seed = base_seed + (n * 1000) + i
            result = bootstrap_single_iteration(data, n, kernel_seconds, seed)
            iteration_results.append(result)
        
        all_results[n] = iteration_results
        
        # Log progress
        log_split(f"Bootstrap N={n} kernel={kernel_seconds}s")
    
    return all_results

def generate_power_curve(
    bootstrap_results: Dict[int, List[Dict[str, Any]]],
    sample_sizes: List[int]
) -> Dict[str, Any]:
    """
    Aggregate bootstrap results into a power curve.
    
    Args:
        bootstrap_results: Raw results from run_bootstrap_loop
        sample_sizes: List of tested sample sizes
    
    Returns:
        Power curve data structure
    """
    empirical_rates = []
    
    for n in sample_sizes:
        if n not in bootstrap_results:
            continue
        
        results = bootstrap_results[n]
        rate_data = [r['replication_success'] for r in results]
        mean_rate = np.mean(rate_data)
        empirical_rates.append(mean_rate)
    
    return {
        'sample_sizes_tested': sample_sizes,
        'empirical_rates': empirical_rates,
        'kernel_seconds': list(set(r['kernel_seconds'] for r in bootstrap_results.get(sample_sizes[0], [{}])[0] if 'kernel_seconds' in r))
    }

def fit_power_curve_model(
    power_curve_data: Dict[str, Any],
    noise_levels: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Fit a logistic regression model to the power curve.
    
    Args:
        power_curve_data: Aggregated power curve data
        noise_levels: Optional list of noise levels for fixed effect
    
    Returns:
        Model fit results
    """
    sample_sizes = np.array(power_curve_data['sample_sizes_tested'])
    rates = np.array(power_curve_data['empirical_rates'])
    
    # Avoid perfect separation
    rates = np.clip(rates, 0.01, 0.99)
    
    # Prepare features
    X = sample_sizes.reshape(-1, 1)
    if noise_levels and len(noise_levels) == len(sample_sizes):
        X = np.column_stack([X, noise_levels])
    
    y = rates  # Proportion data
    
    # Fit logistic regression (statsmodels)
    X_with_const = sm.add_constant(X)
    model = sm.GLM(y, X_with_const, family=sm.families.Binomial())
    result = model.fit()
    
    return {
        'params': result.params.tolist(),
        'pvalues': result.pvalues.tolist(),
        'log_likelihood': result.llf,
        'converged': result.converged
    }

def calculate_kernel_sensitivity(
    curve_a: Dict[str, Any],
    curve_b: Dict[str, Any]
) -> Dict[str, float]:
    """
    Calculate sensitivity difference between two kernels.
    
    Args:
        curve_a: Power curve for kernel A
        curve_b: Power curve for kernel B
    
    Returns:
        Sensitivity metrics
    """
    # Align sample sizes
    common_sizes = sorted(set(curve_a['sample_sizes_tested']) & set(curve_b['sample_sizes_tested']))
    
    diff_rates = []
    for n in common_sizes:
        idx_a = curve_a['sample_sizes_tested'].index(n)
        idx_b = curve_b['sample_sizes_tested'].index(n)
        diff = curve_a['empirical_rates'][idx_a] - curve_b['empirical_rates'][idx_b]
        diff_rates.append(abs(diff))
    
    return {
        'mean_diff_rate': float(np.mean(diff_rates)) if diff_rates else 0.0,
        'max_diff_rate': float(np.max(diff_rates)) if diff_rates else 0.0,
        'common_sample_sizes': common_sizes
    }

def save_power_curves(
    power_curves: Dict[str, Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save power curves to JSON file.
    
    Args:
        power_curves: Dictionary of power curves by paradigm/kernel
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(power_curves, f, indent=2)
    logger.info(f"Saved power curves to {output_path}")

def get_fdr_justification(
    power_curves: Dict[str, Any],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Calculate FDR justification for power curve results.
    
    Args:
        power_curves: Power curve data
        alpha: Significance threshold
    
    Returns:
        FDR justification metrics
    """
    # Placeholder for FDR logic (T024 dependency)
    return {
        'alpha': alpha,
        'justified': True,
        'method': 'benjamini_hochberg'
    }

def main():
    """
    Main entry point for power curve generation with kernel sensitivity analysis.
    
    This function implements T031 by running separate loops for different
    temporal smoothing kernels (4s, 8s) as specified in the task.
    """
    parser = argparse.ArgumentParser(description='Power Curve Generator with Kernel Sensitivity')
    parser.add_argument('--data', type=str, required=True, help='Path to preprocessed data JSON')
    parser.add_argument('--output', type=str, required=True, help='Output path for power curves JSON')
    parser.add_argument('--sample-sizes', type=str, default='10,20,30,40,50', help='Comma-separated sample sizes')
    parser.add_argument('--iterations', type=int, default=10, help='Number of bootstrap iterations')
    parser.add_argument('--kernels', type=str, default='4,8', help='Temporal smoothing kernels in seconds')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    # Parse arguments
    sample_sizes = [int(s) for s in args.sample_sizes.split(',')]
    kernels = [float(k) for k in args.kernels.split(',')]
    
    logger.info(f"Starting power curve generation for kernels: {kernels}")
    start_run("power_curve_generation")
    
    # Load data (real data only - no synthetic fallback)
    try:
        with open(args.data, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise ValueError(f"Real data file not found: {args.data}. Aborting.")
    
    # Run separate loops for each kernel (T031 requirement)
    all_power_curves = {}
    
    for kernel in kernels:
        logger.info(f"Processing kernel: {kernel}s")
        log_split(f"Kernel {kernel}s loop start")
        
        # Run bootstrap loop for this kernel
        bootstrap_results = run_bootstrap_loop(
            data=data,
            sample_sizes=sample_sizes,
            kernel_seconds=kernel,
            num_iterations=args.iterations,
            base_seed=args.seed + int(kernel * 100)
        )
        
        # Generate power curve
        power_curve = generate_power_curve(bootstrap_results, sample_sizes)
        all_power_curves[f"kernel_{int(kernel)}s"] = power_curve
        
        log_split(f"Kernel {kernel}s loop complete")
    
    # Save results
    save_power_curves(all_power_curves, Path(args.output))
    
    end_run("power_curve_generation")
    logger.info("Power curve generation complete.")

if __name__ == '__main__':
    main()