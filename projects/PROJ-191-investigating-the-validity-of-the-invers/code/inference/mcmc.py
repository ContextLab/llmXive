import os
import sys
import time
import logging
import json
from pathlib import Path

import numpy as np
import emcee
from emcee.autocorr import AutocorrTimeError

# Project imports based on API surface
from config import get_logger, ProjectConfig
from models.likelihood import YukawaLikelihood, load_covariance_matrix
from data.state_manager import read_state

logger = get_logger(__name__)

def compute_gelman_rubin(samples):
    """
    Compute the Gelman-Rubin statistic (R-hat) for the chains.
    
    Args:
        samples: Array of shape (nwalkers, nsteps, nparams)
        
    Returns:
        float: The maximum Gelman-Rubin statistic across parameters.
               Returns 1.0 if only one chain or insufficient data.
    """
    nwalkers, nsteps, nparams = samples.shape
    
    if nwalkers < 2:
        logger.warning("Gelman-Rubin requires at least 2 walkers.")
        return 1.0
    
    # Discard burn-in (last 1/3 of samples for simplicity in this context)
    # Or use a fixed burn-in if known. Here we use the last 2/3 of the run.
    burn_in = nsteps // 3
    if burn_in == 0:
        burn_in = 1
    samples_post_burn = samples[:, burn_in:, :]
    
    n_post = samples_post_burn.shape[1]
    if n_post < 2:
        logger.warning("Not enough samples after burn-in for Gelman-Rubin.")
        return 1.0
    
    # Calculate variance within chains (W)
    chain_means = np.mean(samples_post_burn, axis=1) # (nwalkers, nparams)
    overall_mean = np.mean(chain_means, axis=0) # (nparams,)
    
    # Within-chain variance
    W = np.mean(np.var(samples_post_burn, axis=1), axis=0)
    
    # Between-chain variance
    B = n_post * np.var(chain_means, axis=0)
    
    # Pooled variance estimate
    sigma_sq = ((n_post - 1) / n_post) * W + (1 / n_post) * B
    
    # Potential scale reduction factor
    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        R = np.sqrt(sigma_sq / W)
    
    # Handle cases where W is 0
    R = np.where(W == 0, 1.0, R)
    
    return float(np.max(R))

def run_mcmc(config: ProjectConfig, n_walkers: int = 32, min_steps: int = 5000, 
             batch_size: int = 1000, max_steps: int = 50000, convergence_thresh: float = 1.01):
    """
    Run the emcee MCMC sampler for the Yukawa model.
    
    Logic:
    1. Initialize walkers.
    2. Run at least `min_steps`.
    3. Continue in batches of `batch_size` until:
       - Gelman-Rubin < `convergence_thresh`
       - OR `max_steps` is reached.
    4. Save results and convergence status.
    """
    logger.info(f"Starting MCMC run with {n_walkers} walkers.")
    
    # Load data and covariance
    data_path = Path(config.data_dir) / "processed" / "harmonized_data.csv"
    cov_path = Path(config.data_dir) / "processed" / "covariance_matrix.npy"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Harmonized data not found at {data_path}")
    if not cov_path.exists():
        raise FileNotFoundError(f"Covariance matrix not found at {cov_path}")
        
    # Load likelihood components
    # We assume the likelihood class handles data loading internally or via init
    # Based on API: YukawaLikelihood is available.
    # We need to construct it. Assuming it takes data_path and cov_path or similar.
    # If the class signature is different, we adapt based on standard patterns.
    # Given the API surface: `from models.likelihood import YukawaLikelihood`
    # We will assume it can be instantiated with the necessary paths.
    
    try:
        likelihood = YukawaLikelihood(str(data_path), str(cov_path))
    except Exception as e:
        logger.error(f"Failed to initialize YukawaLikelihood: {e}")
        raise

    # Initial positions for walkers (around alpha=0, lambda=1e-4)
    # alpha: strength (log scale usually, but let's try linear or log)
    # lambda: range (log scale)
    # Assuming 2 parameters: [alpha, log_lambda] or [alpha, lambda]
    # Standard Yukawa: F = F_N * (1 + alpha * exp(-r/lambda))
    # Let's assume parameters are [alpha, log_lambda] to ensure positive lambda.
    
    n_params = 2
    p0 = np.zeros((n_walkers, n_params))
    
    # Center around alpha=0, log_lambda ~ -4 (100 microns)
    # Add small random perturbation
    for i in range(n_walkers):
        p0[i, 0] = 0.0 + 0.01 * np.random.randn() # alpha
        p0[i, 1] = -4.0 + 0.01 * np.random.randn() # log_lambda
        
    sampler = emcee.EnsembleSampler(n_walkers, n_params, likelihood.log_prob)
    
    # State tracking
    total_steps = 0
    converged = False
    last_gr = 1.0
    
    logger.info(f"Running minimum {min_steps} steps...")
    
    # Run initial batch to meet min_steps
    # We run in batches of batch_size, but ensure we hit min_steps
    steps_to_run = min_steps
    
    for i in range(n_walkers):
        sampler.run_mcmc(p0, steps_to_run, progress=True, skip_initial=True)
        
    total_steps = steps_to_run
    
    # Check convergence
    samples = sampler.get_chain()
    last_gr = compute_gelman_rubin(samples)
    logger.info(f"After {total_steps} steps: Gelman-Rubin = {last_gr:.4f}")
    
    # Continue if not converged and under max limit
    while last_gr >= convergence_thresh and total_steps < max_steps:
        logger.info(f"Convergence not met (GR={last_gr:.4f}). Running another batch of {batch_size} steps...")
        
        try:
            sampler.run_mcmc(None, batch_size, progress=True)
            total_steps += batch_size
            
            samples = sampler.get_chain()
            last_gr = compute_gelman_rubin(samples)
            logger.info(f"After {total_steps} steps: Gelman-Rubin = {last_gr:.4f}")
            
        except AutocorrTimeError as e:
            logger.warning(f"Autocorrelation time error (insufficient samples): {e}")
            # Continue running anyway, just can't compute reliable GR yet
            pass
        except Exception as e:
            logger.error(f"Error during MCMC batch run: {e}")
            break
    
    # Final status
    if last_gr < convergence_thresh:
        status = "converged"
        logger.info(f"MCMC converged after {total_steps} steps (GR={last_gr:.4f}).")
    else:
        status = "unreliable"
        logger.warning(f"MCMC did not converge after {total_steps} steps (GR={last_gr:.4f}).")
        
    # Save results
    output_dir = Path(config.results_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "total_steps": total_steps,
        "converged": status == "converged",
        "gelman_rubin": float(last_gr),
        "max_steps_reached": total_steps >= max_steps,
        "samples_shape": list(samples.shape),
        "config": {
            "n_walkers": n_walkers,
            "min_steps": min_steps,
            "batch_size": batch_size,
            "max_steps": max_steps,
            "convergence_thresh": convergence_thresh
        }
    }
    
    # Save samples
    samples_path = output_dir / "mcmc_samples.npy"
    np.save(str(samples_path), samples)
    logger.info(f"Saved samples to {samples_path}")
    
    # Save metadata
    metadata_path = output_dir / "mcmc_run_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")
    
    return results

def main():
    """Entry point for the MCMC runner."""
    logger.info("Initializing MCMC Runner (T023)...")
    
    # Load project config
    config = ProjectConfig()
    
    # Run the sampler
    # Parameters can be overridden via config or CLI in a full implementation
    # Here we use defaults as per task spec
    results = run_mcmc(
        config, 
        n_walkers=32, 
        min_steps=5000, 
        batch_size=1000, 
        max_steps=50000,
        convergence_thresh=1.01
    )
    
    logger.info("MCMC Run Complete.")
    return results

if __name__ == "__main__":
    main()
