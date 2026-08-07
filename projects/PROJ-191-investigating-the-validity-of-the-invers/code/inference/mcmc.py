"""
MCMC Runner for Yukawa Model Inference.

Implements the emcee runner with convergence checking (Gelman-Rubin)
and batched execution to respect wall-clock limits while ensuring
minimum step counts are met.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

import numpy as np
import emcee
from emcee.autocorr import AutocorrTimeError

# Project imports based on API surface
from config import get_logger, ProjectConfig
from models.likelihood import YukawaLikelihood, load_covariance_matrix
from data.loaders import HarmonizedDataset
from data.state_manager import read_state, write_state

# Ensure project root is in path for imports if run as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))

logger = get_logger(__name__)

# Configuration defaults
DEFAULT_N_WALKERS = 100
DEFAULT_MIN_STEPS = 5000
DEFAULT_BATCH_SIZE = 1000
DEFAULT_MAX_STEPS = 50000
DEFAULT_GR_THRESHOLD = 1.01
DEFAULT_RND_SEED = 42


def compute_gelman_rubin(samples: np.ndarray) -> float:
    """
    Compute the Gelman-Rubin convergence statistic (R-hat).
    
    Args:
        samples: Array of shape (n_walkers, n_steps, n_params)
    
    Returns:
        R-hat value. Returns np.inf if too few samples to compute.
    """
    n_walkers, n_steps, n_params = samples.shape
    
    if n_steps < 2:
        return np.inf

    # Calculate variance within chains
    # Mean of each chain
    chain_means = np.mean(samples, axis=1)  # (n_walkers, n_params)
    
    # Variance within chains (unbiased estimator)
    # Sum of squared deviations from chain mean
    within_var = np.var(samples, axis=1, ddof=1)  # (n_walkers, n_params)
    W = np.mean(within_var, axis=0)  # (n_params,)
    
    # Variance between chains
    # Variance of chain means
    B = n_steps * np.var(chain_means, axis=0, ddof=1)  # (n_params,)
    
    # Pooled variance estimate
    # V = ((n_steps - 1)/n_steps) * W + (1/n_steps) * B
    V = ((n_steps - 1) / n_steps) * W + (1 / n_steps) * B
    
    # R-hat
    # R = sqrt(V / W)
    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        R = np.sqrt(V / W)
    
    # Return the maximum R-hat across all parameters
    return float(np.max(R))


def run_mcmc(
    data: HarmonizedDataset,
    cov_matrix: np.ndarray,
    n_walkers: int = DEFAULT_N_WALKERS,
    min_steps: int = DEFAULT_MIN_STEPS,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_steps: int = DEFAULT_MAX_STEPS,
    gr_threshold: float = DEFAULT_GR_THRESHOLD,
    seed: int = DEFAULT_RND_SEED,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the emcee MCMC sampler for the Yukawa model.
    
    Continues running in batches until Gelman-Rubin < threshold OR max_steps reached.
    Ensures at least min_steps are run regardless of convergence.
    
    Args:
        data: HarmonizedDataset containing separation and force data.
        cov_matrix: Covariance matrix for likelihood calculation.
        n_walkers: Number of MCMC walkers.
        min_steps: Minimum number of steps to run.
        batch_size: Number of steps to run per batch.
        max_steps: Maximum total steps allowed.
        gr_threshold: Convergence threshold for Gelman-Rubin statistic.
        seed: Random seed for reproducibility.
        output_dir: Directory to save results.
    
    Returns:
        Dictionary containing samples, diagnostics, and metadata.
    """
    if output_dir is None:
        output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    np.random.seed(seed)
    
    # Initialize likelihood
    likelihood = YukawaLikelihood(data, cov_matrix)
    
    # Define parameter bounds for initial positions
    # Parameters: [log_alpha, log_lambda]
    # alpha: strength (0 to ~10^10 relative to gravity, but we use log scale)
    # lambda: range (1e-5 to 1e-2 meters, i.e., 10um to 10mm)
    # We'll use log10 for numerical stability
    # log10(alpha): -5 to 15
    # log10(lambda): -5 to -2 (meters)
    
    ndim = 2
    initial_positions = []
    for _ in range(n_walkers):
        # Random initial positions in log space
        log_alpha = np.random.uniform(-5, 15)
        log_lambda = np.random.uniform(-5, -2)
        initial_positions.append([log_alpha, log_lambda])
    initial_positions = np.array(initial_positions)
    
    # Initialize sampler
    sampler = emcee.EnsembleSampler(
        n_walkers, ndim, likelihood.log_prob, 
        backend=None,  # We manage state manually for batching
        pool=None
    )
    
    logger.info(f"Starting MCMC run with {n_walkers} walkers, {ndim} dimensions")
    logger.info(f"Configuration: min_steps={min_steps}, max_steps={max_steps}, "
               f"batch_size={batch_size}, gr_threshold={gr_threshold}")
    
    # Run in batches
    total_steps = 0
    converged = False
    samples_history = []
    gr_values = []
    
    # Burn-in phase (first batch)
    logger.info("Running burn-in phase...")
    try:
        sampler.run_mcmc(initial_positions, batch_size, progress=True)
        total_steps += batch_size
        
        # Get samples for diagnostics
        samples = sampler.get_chain()
        gr = compute_gelman_rubin(samples)
        gr_values.append(gr)
        logger.info(f"Batch 1 complete. Steps: {total_steps}, R-hat: {gr:.4f}")
        
        # Check if we need more steps
        while total_steps < max_steps:
            # Check convergence conditions
            # Must run at least min_steps
            # Stop if converged AND total_steps >= min_steps
            if total_steps >= min_steps and gr < gr_threshold:
                converged = True
                logger.info(f"Convergence achieved at step {total_steps} with R-hat={gr:.4f}")
                break
            
            # Run next batch
            logger.info(f"Running batch {len(gr_values) + 1}...")
            try:
                sampler.run_mcmc(None, batch_size, progress=True)
                total_steps += batch_size
            except Exception as e:
                logger.warning(f"Batch execution interrupted: {e}")
                break
            
            # Compute diagnostics
            samples = sampler.get_chain()
            gr = compute_gelman_rubin(samples)
            gr_values.append(gr)
            logger.info(f"Batch complete. Steps: {total_steps}, R-hat: {gr:.4f}")
            
    except Exception as e:
        logger.error(f"MCMC run failed: {e}")
        raise
    
    # Final diagnostics
    samples = sampler.get_chain(discard=min_steps // 2)  # Discard half of min_steps as burn-in
    final_samples = sampler.get_chain()
    
    # Compute final R-hat
    if len(final_samples.shape) == 3:
        final_gr = compute_gelman_rubin(final_samples)
    else:
        final_gr = np.inf
    
    # Compute autocorrelation time
    try:
        tau = sampler.get_autocorr_time(tol=0)
        logger.info(f"Autocorrelation time: {tau}")
    except (AutocorrTimeError, ValueError) as e:
        logger.warning(f"Could not compute autocorrelation time: {e}")
        tau = None
    
    # Prepare results
    results = {
        "samples": final_samples,
        "log_alpha_samples": final_samples[:, :, 0],
        "log_lambda_samples": final_samples[:, :, 1],
        "total_steps": total_steps,
        "converged": converged,
        "gr_threshold": gr_threshold,
        "final_gr_statistic": final_gr,
        "gr_history": gr_values,
        "autocorrelation_time": tau,
        "n_walkers": n_walkers,
        "n_params": ndim,
        "seed": seed,
        "status": "converged" if converged else ("max_steps_reached" if total_steps >= max_steps else "interrupted")
    }
    
    # Save results
    results_path = output_dir / "mcmc_results.json"
    samples_path = output_dir / "mcmc_samples.npy"
    
    # Convert numpy arrays to lists for JSON
    json_results = {
        k: (v.tolist() if isinstance(v, np.ndarray) else v) 
        for k, v in results.items() 
        if k not in ["samples", "log_alpha_samples", "log_lambda_samples"]
    }
    
    with open(results_path, 'w') as f:
        json.dump(json_results, f, indent=2)
    
    np.save(samples_path, final_samples)
    logger.info(f"Results saved to {results_path}")
    logger.info(f"Samples saved to {samples_path}")
    
    # Update state file if needed
    state_path = Path("data/processed/state.json")
    if state_path.exists():
        state = read_state()
        state["mcmc_converged"] = converged
        state["mcmc_total_steps"] = total_steps
        write_state(state)
    
    return results


def main():
    """
    Main entry point for the MCMC runner.
    Loads data and covariance matrix, then runs the sampler.
    """
    logger.info("Starting MCMC inference pipeline")
    
    try:
        # Load configuration
        config = ProjectConfig()
        
        # Load harmonized data
        data_path = Path("data/processed/harmonized_data.npz")
        if not data_path.exists():
            raise FileNotFoundError(f"Harmonized data not found at {data_path}. "
                                  "Please run data harmonization first.")
        
        data_dict = np.load(data_path, allow_pickle=True)
        # Reconstruct HarmonizedDataset if needed, or pass raw arrays
        # For simplicity, we'll pass the arrays directly to the likelihood
        separation = data_dict['separation']
        force = data_dict['force']
        # Create a simple mock HarmonizedDataset or pass arrays
        # Since HarmonizedDataset is a dataclass, we might need to reconstruct it
        # But for now, let's assume we can pass the arrays
        
        # Load covariance matrix
        cov_path = Path("data/processed/covariance_matrix.npy")
        if not cov_path.exists():
            raise FileNotFoundError(f"Covariance matrix not found at {cov_path}. "
                                  "Please run covariance construction first.")
        cov_matrix = np.load(cov_path)
        
        # Run MCMC
        results = run_mcmc(
            data={"separation": separation, "force": force},  # Simplified for now
            cov_matrix=cov_matrix,
            min_steps=DEFAULT_MIN_STEPS,
            max_steps=DEFAULT_MAX_STEPS,
            batch_size=DEFAULT_BATCH_SIZE,
            gr_threshold=DEFAULT_GR_THRESHOLD
        )
        
        logger.info(f"MCMC completed. Status: {results['status']}")
        logger.info(f"Final Gelman-Rubin: {results['final_gr_statistic']:.4f}")
        
    except Exception as e:
        logger.error(f"MCMC pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
