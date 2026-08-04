"""
T023: Implement emcee runner with adaptive stopping based on Gelman-Rubin statistic.

Strategy:
1. Start with a minimum of 5,000 steps.
2. Continue in batches of 1,000 steps.
3. After each batch, calculate the Gelman-Rubin (R-hat) statistic.
4. Stop if R-hat < 1.01 for all parameters.
5. Monitor wall-clock time; if approaching 6 hours, signal for subsampling (handled by T027).
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import numpy as np
import emcee
from tqdm import tqdm

# Project imports
from config import get_logger, setup_logging, ProjectConfig
from data.loaders import HarmonizedDataset
from models.physics import log_likelihood_yukawa, log_likelihood_newtonian

# Constants
MIN_STEPS = 5000
BATCH_SIZE = 1000
MAX_WALL_CLOCK_SECONDS = 6 * 3600  # 6 hours
WARNING_THRESHOLD_SECONDS = 5 * 3600  # 5 hours (trigger for T027)
N_WALKERS = 32
R_HAT_THRESHOLD = 1.01

logger = get_logger("mcmc_runner")


def compute_gelman_rubin(samples: np.ndarray) -> np.ndarray:
    """
    Compute the Gelman-Rubin R-hat statistic for each parameter.
    
    Args:
        samples: Array of shape (n_walkers, n_steps, n_params)
    
    Returns:
        Array of R-hat values for each parameter.
    """
    n_walkers, n_steps, n_params = samples.shape
    
    if n_steps < 2:
        return np.ones(n_params) * np.inf
    
    # Split chain into two halves
    half_steps = n_steps // 2
    if half_steps < 2:
        return np.ones(n_params) * np.inf
        
    chain1 = samples[:, :half_steps, :]
    chain2 = samples[:, half_steps:, :]
    
    # Calculate within-chain variance (W)
    # Mean of each walker's chain
    mean_chain1 = np.mean(chain1, axis=1)  # (n_walkers, n_params)
    mean_chain2 = np.mean(chain2, axis=1)  # (n_walkers, n_params)
    
    # Variance within each chain
    var_chain1 = np.var(chain1, axis=1, ddof=1)  # (n_walkers, n_params)
    var_chain2 = np.var(chain2, axis=1, ddof=1)  # (n_walkers, n_params)
    
    # Average within-chain variance
    W = (np.mean(var_chain1, axis=0) + np.mean(var_chain2, axis=0)) / 2.0
    
    # Between-chain variance (B)
    # Mean of the two halves for each walker
    mean_half1 = np.mean(mean_chain1, axis=0)  # (n_params,)
    mean_half2 = np.mean(mean_chain2, axis=0)  # (n_params,)
    
    # Variance of the means
    B = np.var(np.stack([mean_half1, mean_half2], axis=0), axis=0, ddof=1) * half_steps
    
    # Estimated variance
    sigma_sq = ((2 * half_steps + 1) / (2 * half_steps)) * W + (1 / half_steps) * B
    
    # Potential scale reduction factor
    # R-hat = sqrt(sigma_sq / W)
    # Avoid division by zero
    r_hat = np.sqrt(sigma_sq / (W + 1e-10))
    
    return r_hat


def run_mcmc(
    dataset: HarmonizedDataset,
    model: str = "yukawa",
    output_dir: Optional[Path] = None,
    initial_state: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Run emcee MCMC with adaptive stopping based on Gelman-Rubin statistic.
    
    Args:
        dataset: The harmonized dataset containing separation, force, and covariance.
        model: "yukawa" or "newtonian".
        output_dir: Directory to save results.
        initial_state: Optional initial walker positions (n_walkers, n_params).
    
    Returns:
        Dictionary containing samples, metadata, and diagnostics.
    """
    setup_logging()
    
    if output_dir is None:
        output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine parameters based on model
    if model == "yukawa":
        log_like_func = log_likelihood_yukawa
        n_params = 2  # alpha, lambda
        param_names = ["alpha", "lambda"]
    elif model == "newtonian":
        log_like_func = log_likelihood_newtonian
        n_params = 1  # alpha (fixed to 0 usually, but we treat as 1 param for consistency)
        param_names = ["alpha"]
    else:
        raise ValueError(f"Unknown model: {model}")
    
    # Prepare data
    separation = dataset.separation  # meters
    force = dataset.force  # Newtons
    cov_matrix = dataset.covariance  # (N, N)
    
    # Initialize walkers
    if initial_state is not None:
        pos = initial_state
    else:
        # Random initial positions around reasonable guesses
        # For Yukawa: alpha ~ 10^4, lambda ~ 10^-4
        # For Newtonian: alpha ~ 0
        if model == "yukawa":
            alpha_mean = 1e4
            lambda_mean = 1e-4
        else:
            alpha_mean = 0.0
            lambda_mean = 0.0
            
        pos = np.random.randn(N_WALKERS, n_params)
        pos[:, 0] *= 0.1 * alpha_mean + alpha_mean  # alpha
        if n_params > 1:
            pos[:, 1] *= 0.1 * lambda_mean + lambda_mean  # lambda
        
        # Ensure positive lambda
        if n_params > 1:
            pos[:, 1] = np.abs(pos[:, 1]) + 1e-6
    
    # Create sampler
    sampler = emcee.EnsembleSampler(
        N_WALKERS, 
        n_params, 
        log_like_func, 
        args=(separation, force, cov_matrix)
    )
    
    # Run MCMC with adaptive stopping
    logger.info(f"Starting MCMC run with {N_WALKERS} walkers, {n_params} parameters.")
    logger.info(f"Minimum steps: {MIN_STEPS}, Batch size: {BATCH_SIZE}")
    
    start_time = time.time()
    all_samples = []
    current_step = 0
    converged = False
    last_r_hat = None
    
    # Run initial batch to meet minimum steps requirement
    steps_to_run = MIN_STEPS
    logger.info(f"Running initial {steps_to_run} steps...")
    
    for i in range(steps_to_run):
        sampler.run_mcmc(None, n_steps=1, progress=False)
        current_step += 1
        
        # Progress update every 500 steps
        if (i + 1) % 500 == 0:
            elapsed = time.time() - start_time
            logger.info(f"Step {current_step}/{steps_to_run}, elapsed: {elapsed:.1f}s")
            
            # Check wall clock time
            if elapsed > MAX_WALL_CLOCK_SECONDS:
                logger.warning("Maximum wall clock time exceeded. Stopping.")
                break
    
    # Check convergence after minimum steps
    samples = sampler.get_chain()
    r_hat = compute_gelman_rubin(samples)
    last_r_hat = r_hat
    logger.info(f"After {current_step} steps, R-hat: {r_hat}")
    
    # Continue in batches until convergence or time limit
    while not converged and current_step < MAX_WALL_CLOCK_SECONDS:
        # Check if we've reached convergence
        if current_step >= MIN_STEPS:
            if np.all(r_hat < R_HAT_THRESHOLD):
                logger.info(f"Converged! R-hat = {np.max(r_hat):.4f} < {R_HAT_THRESHOLD}")
                converged = True
                break
            
            # Check wall clock time for T027 trigger
            elapsed = time.time() - start_time
            if elapsed > WARNING_THRESHOLD_SECONDS:
                logger.warning(f"Wall clock time ({elapsed:.1f}s) approaching limit. "
                             f"Consider subsampling data (T027).")
            
            if elapsed > MAX_WALL_CLOCK_SECONDS:
                logger.warning("Maximum wall clock time exceeded. Stopping.")
                break
        
        # Run next batch
        logger.info(f"Running next batch of {BATCH_SIZE} steps...")
        sampler.run_mcmc(None, n_steps=BATCH_SIZE, progress=True)
        current_step += BATCH_SIZE
        
        # Check convergence
        samples = sampler.get_chain()
        r_hat = compute_gelman_rubin(samples)
        last_r_hat = r_hat
        
        logger.info(f"After {current_step} steps, R-hat: {r_hat}")
        
        # Check if converged
        if np.all(r_hat < R_HAT_THRESHOLD):
            logger.info(f"Converged! R-hat = {np.max(r_hat):.4f} < {R_HAT_THRESHOLD}")
            converged = True
            break
    
    # Final results
    final_samples = sampler.get_chain()
    flat_samples = sampler.get_chain(discard=MIN_STEPS, thin=1)
    log_prob = sampler.get_log_prob()
    
    # Calculate statistics
    mean_params = np.mean(flat_samples, axis=0)
    std_params = np.std(flat_samples, axis=0)
    
    result = {
        "samples": final_samples,
        "flat_samples": flat_samples,
        "log_prob": log_prob,
        "mean": mean_params,
        "std": std_params,
        "r_hat": last_r_hat,
        "converged": converged,
        "total_steps": current_step,
        "wall_clock_time": time.time() - start_time,
        "model": model,
        "param_names": param_names
    }
    
    # Save results
    output_file = output_dir / f"mcmc_{model}_results.npz"
    np.savez(
        output_file,
        samples=result["samples"],
        flat_samples=result["flat_samples"],
        log_prob=result["log_prob"],
        mean=result["mean"],
        std=result["std"],
        r_hat=result["r_hat"],
        param_names=param_names
    )
    
    logger.info(f"Results saved to {output_file}")
    logger.info(f"Total steps: {current_step}, Converged: {converged}, "
               f"R-hat: {np.max(result['r_hat']):.4f}, "
               f"Wall clock: {result['wall_clock_time']:.1f}s")
    
    return result


def main():
    """Main entry point for running MCMC."""
    setup_logging()
    
    # Load dataset
    data_path = Path("data/processed/harmonized_dataset.npz")
    if not data_path.exists():
        logger.error(f"Harmonized dataset not found at {data_path}")
        sys.exit(1)
    
    try:
        data = np.load(data_path, allow_pickle=True)
        dataset = HarmonizedDataset(
            separation=data["separation"],
            force=data["force"],
            covariance=data["covariance"],
            metadata=data.get("metadata", {})
        )
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)
    
    # Run MCMC for Yukawa model
    logger.info("Running MCMC for Yukawa model...")
    yukawa_results = run_mcmc(dataset, model="yukawa")
    
    # Run MCMC for Newtonian model (optional, for comparison)
    logger.info("Running MCMC for Newtonian model...")
    newtonian_results = run_mcmc(dataset, model="newtonian")
    
    print("MCMC completed successfully!")
    print(f"Yukawa R-hat: {np.max(yukawa_results['r_hat']):.4f}")
    print(f"Newtonian R-hat: {np.max(newtonian_results['r_hat']):.4f}")


if __name__ == "__main__":
    main()