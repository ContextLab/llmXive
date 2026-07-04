import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Conditional import for PyMC to allow graceful failure if not installed
try:
    import pymc as pm
    import arviz as az
    PYMC_AVAILABLE = True
except ImportError:
    PYMC_AVAILABLE = False
    pm = None
    az = None

from src.utils.logging import get_logger
from src.utils.config import get_project_root, get_data_processed_path

logger = get_logger(__name__)

def fit_random_walk_model(
    data: pd.DataFrame,
    output_path: Optional[str] = None,
    tune_steps: int = 1000,
    draw_steps: int = 1000,
    chains: int = 2,
    random_seed: int = 42,
    convergence_threshold: float = 1.05
) -> Optional[Dict[str, Any]]:
    """
    Fits a Random Walk Bayesian Hierarchical Model to poll data.

    Model Specification:
      Latent weekly preference: theta_t ~ Normal(theta_{t-1}, sigma_t^2)
      Observation: y_i ~ Normal(theta_{week(i)}, tau^2)

    Args:
        data: DataFrame with columns 'date', 'vote_share', 'pollster', 'weight' (optional).
        output_path: Path to save the resulting ArviZ InferenceData object.
        tune_steps: Number of tuning steps for NUTS sampler.
        draw_steps: Number of draws per chain after tuning.
        chains: Number of MCMC chains.
        random_seed: Seed for reproducibility.
        convergence_threshold: Maximum allowed R-hat value. If max R-hat > this,
                             the function halts and raises an error.

    Returns:
        Dictionary containing:
          - 'inference_data': ArviZ InferenceData object
          - 'summary': Dictionary of summary statistics (R-hat, etc.)
          - 'convergence_status': 'passed' or 'failed'

    Raises:
        RuntimeError: If PyMC is not installed or if convergence check fails.
    """
    if not PYMC_AVAILABLE:
        raise RuntimeError(
            "PyMC is not installed. Please install dependencies from requirements.txt "
            "to run Bayesian modeling tasks."
        )

    logger.info("Starting Random Walk Bayesian Model fitting...")

    # Preprocess data for PyMC
    # Ensure data is sorted by date
    data = data.sort_values('date').reset_index(drop=True)

    # Map weeks to integers for the latent process
    # We assume data is already binned into weekly intervals by harmonize.py
    # If not, we create a simple week index
    if 'week_index' not in data.columns:
        # Fallback: create a unique index per unique date (treating each date as a time step if not binned)
        unique_dates = data['date'].unique()
        date_to_idx = {d: i for i, d in enumerate(sorted(unique_dates))}
        data['week_index'] = data['date'].map(date_to_idx)
        logger.warning("No 'week_index' found in data. Created index based on unique dates.")

    # Extract arrays
    y = data['vote_share'].values.astype(np.float32)
    t = data['week_index'].values.astype(np.int32)
    n_weeks = int(t.max() + 1)
    n_obs = len(y)

    if n_weeks < 2:
        raise ValueError("Data must contain at least 2 time steps to fit a Random Walk model.")

    logger.info(f"Fitting model with {n_obs} observations across {n_weeks} time steps.")

    with pm.Model() as rw_model:
        # Priors
        # sigma_t: volatility of the random walk
        sigma_t = pm.HalfNormal("sigma_t", sigma=5.0)
        
        # tau: observation noise
        tau = pm.HalfNormal("tau", sigma=5.0)

        # Latent random walk process
        # theta_0 ~ Normal(50, 10) (centered around 50% for 2-candidate race)
        theta_0 = pm.Normal("theta_0", mu=50.0, sigma=10.0)
        
        # Construct the random walk
        # theta_t = theta_{t-1} + epsilon_t, where epsilon_t ~ Normal(0, sigma_t)
        # We use a scan or manual construction. For simplicity with small n_weeks:
        eps = pm.Normal("eps", mu=0, sigma=sigma_t, shape=n_weeks - 1)
        
        # Build the path
        # theta = [theta_0, theta_0 + eps_0, theta_0 + eps_0 + eps_1, ...]
        # Using cumulative sum
        theta_steps = pm.Deterministic("theta_steps", pm.math.cumsum(eps))
        theta = pm.Deterministic("theta", pm.math.concatenate([[theta_0], theta_steps + theta_0]))

        # Observation model
        # Map observations to their corresponding theta
        theta_obs = theta[t]
        
        y_obs = pm.Normal("y_obs", mu=theta_obs, sigma=tau, observed=y)

        # Sampling
        logger.info(f"Sampling with {chains} chains, {tune_steps} tune, {draw_steps} draws...")
        
        # Set random seed
        pm.random.seed(random_seed)

        try:
            trace = pm.sample(
                draws=draw_steps,
                tune=tune_steps,
                chains=chains,
                target_accept=0.9, # Higher acceptance for better mixing in RW
                compute_convergence_checks=True,
                return_inferencedata=True,
                random_seed=random_seed
            )
        except Exception as e:
            logger.error(f"Sampling failed: {e}")
            raise RuntimeError(f"MCMC sampling failed: {e}")

    # Convergence Checks
    logger.info("Running convergence diagnostics (R-hat)...")
    summary = az.summary(trace, var_names=["theta", "sigma_t", "tau"], stat_funcs=[lambda x: x.mean()])
    
    # Extract R-hat values
    r_hat = az.rhat(trace)
    
    # Check global max R-hat
    # r_hat is a DataArray; we need to check all variables
    max_rhat = float(r_hat.max().values)
    
    logger.info(f"Maximum R-hat observed: {max_rhat:.4f}")
    logger.info(f"Convergence threshold: {convergence_threshold}")

    status = "passed"
    if max_rhat > convergence_threshold:
        status = "failed"
        error_msg = (
            f"Convergence check FAILED. Maximum R-hat ({max_rhat:.4f}) exceeds threshold "
            f"({convergence_threshold}). The model has not converged. "
            "Consider increasing tune_steps, adjusting target_accept, or checking data quality."
        )
        logger.error(error_msg)
        # HALT: Raise error as per task requirement
        raise RuntimeError(error_msg)

    logger.info("Convergence check PASSED.")

    # Save results if path provided
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        trace.to_netcdf(output_path)
        logger.info(f"Model results saved to {output_path}")

    return {
        "inference_data": trace,
        "summary": summary,
        "convergence_status": status,
        "max_rhat": max_rhat
    }

def main():
    """
    Entry point for running the Bayesian model fitting pipeline.
    Loads processed data, fits the model, and saves results.
    """
    project_root = get_project_root()
    data_path = get_data_processed_path("poll_data_cleaned.csv")
    
    if not os.path.exists(data_path):
        logger.error(f"Processed data not found at {data_path}. Run harmonize.py first.")
        sys.exit(1)

    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)

    # Ensure required columns exist
    required_cols = ['date', 'vote_share']
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Data missing required columns: {required_cols}")
        sys.exit(1)

    output_path = os.path.join(project_root, "data", "processed", "bayesian_model_results.nc")
    
    try:
        result = fit_random_walk_model(
            data=df,
            output_path=output_path,
            tune_steps=1000,
            draw_steps=1000,
            chains=2,
            convergence_threshold=1.05
        )
        
        if result["convergence_status"] == "passed":
            logger.info("Pipeline completed successfully. Model converged.")
        else:
            # This should not be reached due to the exception in fit_random_walk_model
            logger.error("Pipeline completed with convergence failure (should have raised error).")
            sys.exit(1)
            
    except RuntimeError as e:
        logger.error(f"Pipeline halted due to error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during pipeline execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()