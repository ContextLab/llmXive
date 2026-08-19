import os
import sys
import time
import logging
import json
import numpy as np
import emcee
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

# Project imports based on API surface
from config import get_logger, ProjectConfig
from models.likelihood import YukawaLikelihood, NewtonianLikelihood, load_covariance_matrix
from data.loaders import HarmonizedDataset
from data.fallback_logic import prepare_analysis_dataset

logger = get_logger(__name__)

# Configuration constants
MIN_STEPS = 5000
BATCH_SIZE = 1000
DEFAULT_MAX_STEPS = 50000
DEFAULT_TIME_LIMIT_HOURS = 5.5
CONVERGENCE_THRESHOLD = 1.01
N_WALKERS = 32
N_BURNIN = 1000

def compute_gelman_rubin(samples: np.ndarray) -> float:
    """
    Compute the Gelman-Rubin statistic (potential scale reduction factor).
    samples: shape (n_walkers, n_steps, n_params)
    Returns the max R-hat across parameters.
    """
    if samples.shape[0] < 2:
        return 1.0
    
    n_walkers, n_steps, n_params = samples.shape
    
    # Split chains into two halves
    half_steps = n_steps // 2
    if half_steps < 2:
        return 1.0
        
    # Calculate variance between chains (B) and within chains (W)
    # We use the last half of the samples for convergence check
    samples_last = samples[:, half_steps:, :]
    
    # Mean of each chain
    chain_means = np.mean(samples_last, axis=1)  # (n_walkers, n_params)
    
    # Overall mean
    overall_mean = np.mean(chain_means, axis=0)  # (n_params,)
    
    # Between-chain variance (B)
    B = (n_walkers / (n_walkers - 1)) * np.var(chain_means, axis=0, ddof=1)
    
    # Within-chain variance (W)
    W = np.mean(np.var(samples_last, axis=1, ddof=1), axis=0)
    
    # Pooled variance estimate
    var_plus = ((n_steps - 1) / n_steps) * W + (1 / n_steps) * B
    
    # Avoid division by zero
    if np.any(W == 0):
        return 1.0
        
    R_hat = np.sqrt(var_plus / W)
    
    return float(np.max(R_hat))

def run_mcmc(
    data: HarmonizedDataset,
    covariance_matrix: np.ndarray,
    n_walkers: int = N_WALKERS,
    min_steps: int = MIN_STEPS,
    max_steps: int = DEFAULT_MAX_STEPS,
    time_limit_hours: float = DEFAULT_TIME_LIMIT_HOURS,
    convergence_threshold: float = CONVERGENCE_THRESHOLD,
    batch_size: int = BATCH_SIZE,
    output_dir: str = "data/results"
) -> Dict[str, Any]:
    """
    Run emcee MCMC sampler for Yukawa model inference.
    
    Args:
        data: HarmonizedDataset containing force and separation data
        covariance_matrix: Pre-computed covariance matrix
        n_walkers: Number of MCMC walkers
        min_steps: Minimum steps to run (default 5000)
        max_steps: Maximum steps allowed
        time_limit_hours: Wall-clock time limit
        convergence_threshold: Gelman-Rubin threshold for convergence
        batch_size: Steps per batch
        output_dir: Directory to save results
        
    Returns:
        Dictionary with results and metadata
    """
    logger.info(f"Starting MCMC run with {n_walkers} walkers")
    logger.info(f"Configuration: min_steps={min_steps}, max_steps={max_steps}, time_limit={time_limit_hours}h")
    
    # Load data
    separation = data.separation
    force = data.force
    n_points = len(separation)
    
    logger.info(f"Data loaded: {n_points} points")
    
    # Initialize likelihood
    likelihood = YukawaLikelihood(separation, force, covariance_matrix)
    
    # Parameter bounds: [log_lambda (microns), log_alpha]
    # lambda: 1e-3 to 1e3 microns -> log_lambda: -7 to 7
    # alpha: 1e-4 to 1e4 -> log_alpha: -9 to 9
    ndim = 2
    p0 = np.random.randn(n_walkers, ndim)
    p0[:, 0] += 0.0  # log_lambda centered at 0 (1 micron)
    p0[:, 1] -= 2.0  # log_alpha centered at -2 (0.01)
    
    # Setup sampler
    sampler = emcee.EnsembleSampler(n_walkers, ndim, likelihood.log_prob, progress=True)
    
    # Run parameters
    start_time = time.time()
    total_steps = 0
    converged = False
    time_limited = False
    gelman_rubin_history = []
    
    # Initial burn-in (fixed)
    logger.info(f"Running burn-in of {N_BURNIN} steps...")
    sampler.run_mcmc(p0, N_BURNIN, progress=True)
    total_steps += N_BURNIN
    
    # Check time after burn-in
    elapsed = time.time() - start_time
    if elapsed > time_limit_hours * 3600:
        logger.warning("TIME_LIMIT_REACHED during burn-in")
        time_limited = True
        
    # Main sampling loop in batches
    logger.info(f"Starting main sampling loop (min {min_steps}, max {max_steps})...")
    
    while total_steps < max_steps:
        # Check time limit
        elapsed = time.time() - start_time
        if elapsed > time_limit_hours * 3600:
            logger.warning("TIME_LIMIT_REACHED")
            time_limited = True
            # Continue to complete current batch but mark as time-limited
            # We do not stop early unless we've met minimum steps
            if total_steps >= min_steps:
                logger.info("Time limit reached but minimum steps achieved. Stopping.")
                break
            else:
                logger.info("Time limit reached but minimum steps not achieved. Continuing...")
        
        # Run a batch
        batch_steps = min(batch_size, max_steps - total_steps)
        sampler.run_mcmc(None, batch_steps, progress=True)
        total_steps += batch_steps
        
        # Get current samples
        samples = sampler.get_chain()  # (n_walkers, n_steps, n_params)
        
        # Check convergence if we have enough steps
        if total_steps >= N_BURNIN + min_steps:
            gr_stat = compute_gelman_rubin(samples)
            gelman_rubin_history.append(gr_stat)
            logger.info(f"Step {total_steps}: Gelman-Rubin = {gr_stat:.4f}")
            
            if gr_stat < convergence_threshold:
                logger.info(f"Convergence achieved at step {total_steps} with GR = {gr_stat:.4f}")
                converged = True
                break
        
        # Check if we've reached minimum steps and time limit is approaching
        if total_steps >= min_steps:
            elapsed = time.time() - start_time
            if elapsed > time_limit_hours * 3600 * 0.9:  # 90% of time limit
                logger.warning("Approaching time limit with minimum steps achieved")
                # Try to reduce batch size for final steps if needed
                batch_size = min(batch_size, 100)
    
    # Finalize
    final_samples = sampler.get_chain(discard=N_BURNIN, thin=1)
    flat_samples = sampler.get_chain(discard=N_BURNIN, thin=1, flat=True)
    
    # Calculate statistics
    alpha_samples = 10 ** flat_samples[:, 1]  # Convert back from log
    lambda_samples = 10 ** flat_samples[:, 0]  # Convert back from log
    
    alpha_median = float(np.median(alpha_samples))
    alpha_lower = float(np.percentile(alpha_samples, 2.5))
    alpha_upper = float(np.percentile(alpha_samples, 97.5))
    
    lambda_median = float(np.median(lambda_samples))
    lambda_lower = float(np.percentile(lambda_samples, 2.5))
    lambda_upper = float(np.percentile(lambda_samples, 97.5))
    
    final_gr = gelman_rubin_history[-1] if gelman_rubin_history else 1.0
    
    # Prepare results
    results = {
        "status": "converged" if converged else ("time_limited" if time_limited else "max_steps_reached"),
        "total_steps": total_steps,
        "n_walkers": n_walkers,
        "gelman_rubin": final_gr,
        "convergence_threshold": convergence_threshold,
        "time_elapsed_seconds": time.time() - start_time,
        "time_limit_hours": time_limit_hours,
        "parameters": {
            "alpha": {
                "median": alpha_median,
                "lower_95": alpha_lower,
                "upper_95": alpha_upper,
                "unit": "dimensionless"
            },
            "lambda": {
                "median": lambda_median,
                "lower_95": lambda_lower,
                "upper_95": lambda_upper,
                "unit": "micrometers"
            }
        },
        "mcmc_config": {
            "n_walkers": n_walkers,
            "min_steps": min_steps,
            "max_steps": max_steps,
            "batch_size": batch_size,
            "burn_in": N_BURNIN
        }
    }
    
    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save JSON summary
    json_path = output_path / "mcmc_results.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved MCMC results to {json_path}")
    
    # Save samples as numpy array
    samples_path = output_path / "mcmc_samples.npy"
    np.save(samples_path, flat_samples)
    logger.info(f"Saved MCMC samples to {samples_path}")
    
    # Save chain for diagnostics
    chain_path = output_path / "mcmc_chain.npy"
    np.save(chain_path, final_samples)
    logger.info(f"Saved MCMC chain to {chain_path}")
    
    return results

def main():
    """
    Main entry point for MCMC inference.
    Reads configuration from data/processed/data_config.json and harmonized data.
    """
    logger.info("Starting MCMC inference pipeline")
    
    # Load data config
    config_path = Path("data/processed/data_config.json")
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
        
    with open(config_path, 'r') as f:
        data_config = json.load(f)
    
    mode = data_config.get("mode", "full")
    logger.info(f"Running in mode: {mode}")
    
    # Load harmonized data
    data_path = Path("data/processed/harmonized_data.parquet")
    if not data_path.exists():
        logger.error(f"Harmonized data not found: {data_path}")
        sys.exit(1)
    
    try:
        data = HarmonizedDataset.from_parquet(data_path)
    except Exception as e:
        logger.error(f"Failed to load harmonized data: {e}")
        sys.exit(1)
    
    # Apply subsampling if needed
    if mode == "subsample":
        indices = data_config.get("subset_indices", None)
        if indices is None:
            logger.error("Subsampling requested but no indices provided")
            sys.exit(1)
        
        logger.info(f"Subsampling to {len(indices)} points")
        data = prepare_analysis_dataset(data, indices)
    
    # Load covariance matrix
    cov_path = Path("data/processed/covariance_matrix.npy")
    if not cov_path.exists():
        logger.error(f"Covariance matrix not found: {cov_path}")
        sys.exit(1)
    
    try:
        covariance_matrix = np.load(cov_path)
    except Exception as e:
        logger.error(f"Failed to load covariance matrix: {e}")
        sys.exit(1)
    
    # Read max steps from config if available
    max_steps = data_config.get("max_mcmc_steps", DEFAULT_MAX_STEPS)
    time_limit = data_config.get("time_limit_hours", DEFAULT_TIME_LIMIT_HOURS)
    
    # Run MCMC
    results = run_mcmc(
        data=data,
        covariance_matrix=covariance_matrix,
        max_steps=max_steps,
        time_limit_hours=time_limit
    )
    
    logger.info(f"MCMC completed with status: {results['status']}")
    logger.info(f"Final Gelman-Rubin: {results['gelman_rubin']:.4f}")
    logger.info(f"Alpha (95% CI): [{results['parameters']['alpha']['lower_95']:.2e}, {results['parameters']['alpha']['upper_95']:.2e}]")
    
    return results

if __name__ == "__main__":
    main()