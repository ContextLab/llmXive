import os
import sys
import csv
import logging
import math
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az

# Import local logging utility
try:
    from src.utils.logging import get_logger, configure_logging
except ImportError:
    # Fallback if src is not in path during local execution
    import logging
    def get_logger(name):
        return logging.getLogger(name)
    def configure_logging():
        pass

logger = get_logger(__name__)

# Constants
R_HAT_THRESHOLD = 1.05
DEFAULT_SEED = 42

def load_processed_poll_data(filepath: str) -> pd.DataFrame:
    """
    Load the harmonized and binned poll data.
    Expected columns: date, week_bin, vote_share, sample_size, pollster
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    # Ensure date is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    # Sort by date to ensure time series order
    df = df.sort_values('date').reset_index(drop=True)
    
    return df

def prepare_random_walk_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare data for the Random Walk model.
    Returns:
      y: vote shares (observations)
      sigma_obs: observation noise (approx 1/sqrt(sample_size))
      n_obs: number of observations
    """
    if df.empty:
        raise ValueError("Input dataframe is empty")
    
    # Extract vote shares
    y = df['vote_share'].values.astype(float)
    
    # Calculate observation noise based on sample size
    # Assuming binomial variance approximation: sigma ~ 1/sqrt(n)
    sample_sizes = df['sample_size'].values.astype(float)
    # Avoid division by zero
    sample_sizes = np.where(sample_sizes == 0, 1, sample_sizes)
    sigma_obs = 1.0 / np.sqrt(sample_sizes)
    
    return y, sigma_obs, len(y)

def run_random_walk_model(
    y: np.ndarray,
    sigma_obs: np.ndarray,
    n_obs: int,
    seed: int = DEFAULT_SEED,
    tune: int = 1000,
    draws: int = 1000,
    chains: int = 2
) -> az.InferenceData:
    """
    Run the Bayesian Random Walk hierarchical model.
    Model:
      theta_0 ~ Normal(0.5, 1)
      theta_t ~ Normal(theta_{t-1}, sigma_rw)
      y_t ~ Normal(theta_t, sigma_obs_t)
    """
    logger.info(f"Starting Random Walk model with {n_obs} observations.")
    
    with pm.Model() as rw_model:
        # Priors
        # Initial state
        theta_0 = pm.Normal("theta_0", mu=0.5, sigma=0.5)
        
        # Random walk step size (sigma_rw)
        sigma_rw = pm.HalfNormal("sigma_rw", sigma=0.05)
        
        # Construct the random walk latent process
        # theta[t] = theta[t-1] + epsilon
        # Using a Gaussian Random Walk
        steps = pm.GaussianRandomWalk(
            "theta", 
            sigma=sigma_rw, 
            steps=n_obs - 1,
            init_dist=pm.Normal.dist(mu=0.5, sigma=0.5) # Initial distribution for theta_0 effectively handled by steps if we index correctly, but let's be explicit
        )
        
        # Ensure theta includes the initial state if steps = n-1
        # Actually, GaussianRandomWalk with steps=n-1 produces n values if init_dist is provided? 
        # No, usually steps is the number of transitions. 
        # Let's manually construct to be safe and clear.
        
        # Re-implementation for clarity:
        # theta[0]
        # theta[t] = theta[t-1] + delta_t
        
        # Let's use the explicit GaussianRandomWalk which returns a vector of length `steps + 1` if init_dist is set?
        # PyMC docs: steps is the number of steps. The result shape is (steps,). 
        # So we need steps = n_obs - 1 to get n_obs values? No, that gives n_obs-1 values.
        # We need to handle the first point separately or use a specific construction.
        
        # Simpler approach for PyMC:
        # theta_0
        # theta_rest ~ GaussianRandomWalk(...)
        # theta = pm.math.concatenate([theta_0, theta_rest])
        
        theta_0_var = pm.Normal("theta_0_var", mu=0.5, sigma=0.5)
        theta_rest = pm.GaussianRandomWalk("theta_rest", sigma=sigma_rw, steps=n_obs - 1)
        theta = pm.Deterministic("theta", pm.math.concatenate([[theta_0_var], theta_rest]))
        
        # Likelihood
        obs = pm.Normal("obs", mu=theta, sigma=sigma_obs, observed=y)
        
        # Sample
        logger.info("Sampling started...")
        try:
            trace = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                seed=seed,
                return_inferencedata=True,
                target_accept=0.95, # Higher for random walks
                random_seed=seed
            )
        except Exception as e:
            logger.error(f"Sampling failed: {e}")
            raise
        
        logger.info("Sampling completed.")
        return trace

def check_convergence(trace: az.InferenceData) -> Tuple[bool, Dict[str, float]]:
    """
    Check convergence using R-hat statistics.
    Halts and reports error if any R-hat > 1.05.
    
    Returns:
      is_converged: bool
      r_hat_values: dict of variable names to R-hat values
    """
    logger.info("Checking model convergence...")
    
    try:
        r_hat_stats = az.rhat(trace)
    except Exception as e:
        logger.error(f"Failed to compute R-hat: {e}")
        raise RuntimeError(f"Convergence check failed: {e}")
    
    # r_hat_stats is a DataArray or dict-like
    # Flatten to check all variables
    converged = True
    r_hat_values = {}
    
    # Handle different types of return from az.rhat
    if hasattr(r_hat_stats, 'items'):
        items = r_hat_stats.items()
    else:
        # If it's a DataArray, convert to dict
        items = r_hat_stats.to_dict().items() if hasattr(r_hat_stats, 'to_dict') else []
    
    # Iterate through variables
    for var_name, value in r_hat_stats.to_dict().items() if hasattr(r_hat_stats, 'to_dict') else r_hat_stats.items():
        # Value might be a scalar or an array (if multiple chains/vars mixed)
        if hasattr(value, '__iter__'):
            max_r = max(value)
        else:
            max_r = value
        
        r_hat_values[var_name] = float(max_r)
        
        if max_r > R_HAT_THRESHOLD:
            logger.error(f"Convergence FAILED for variable '{var_name}': R-hat = {max_r:.4f} (threshold: {R_HAT_THRESHOLD})")
            converged = False
    
    if not converged:
        error_msg = f"Model did not converge. Max R-hat: {max(r_hat_values.values()):.4f} > {R_HAT_THRESHOLD}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("Convergence check PASSED. All R-hat values <= 1.05.")
    return True, r_hat_values

def generate_forecasts(trace: az.InferenceData, n_steps: int = 1) -> pd.DataFrame:
    """
    Generate forecasts from the posterior predictive distribution.
    """
    logger.info("Generating forecasts...")
    
    # Get the posterior samples of the last theta
    # InferenceData structure: trace.posterior['theta']
    theta_samples = trace.posterior['theta'].values
    # Shape: (chains, draws, steps)
    # We want the distribution of the last step (index -1)
    
    last_theta = theta_samples[..., -1]
    # Flatten to (chains * draws,)
    last_theta_flat = last_theta.flatten()
    
    # Calculate mean and credible intervals
    mean_forecast = np.mean(last_theta_flat)
    lower_ci = np.percentile(last_theta_flat, 2.5)
    upper_ci = np.percentile(last_theta_flat, 97.5)
    
    forecast_df = pd.DataFrame({
        'forecast_mean': [mean_forecast],
        'ci_lower_95': [lower_ci],
        'ci_upper_95': [upper_ci]
    })
    
    return forecast_df

def save_forecasts(forecast_df: pd.DataFrame, filepath: str) -> None:
    """
    Save forecasts to CSV.
    """
    logger.info(f"Saving forecasts to {filepath}")
    forecast_df.to_csv(filepath, index=False)
    logger.info("Forecasts saved successfully.")

def main():
    """
    Main entry point for the Bayesian model execution with convergence checks.
    """
    configure_logging()
    
    # Paths
    data_path = os.path.join("data", "processed", "poll_data_cleaned.csv")
    output_path = os.path.join("data", "processed", "bayesian_forecasts.csv")
    
    try:
        # 1. Load Data
        df = load_processed_poll_data(data_path)
        logger.info(f"Loaded {len(df)} records.")
        
        # 2. Prepare Data
        y, sigma_obs, n_obs = prepare_random_walk_data(df)
        
        # 3. Run Model
        trace = run_random_walk_model(y, sigma_obs, n_obs)
        
        # 4. Check Convergence (CRITICAL FOR T023)
        # This will raise RuntimeError if R-hat > 1.05
        is_converged, r_hats = check_convergence(trace)
        
        # 5. Generate Forecasts
        forecasts = generate_forecasts(trace)
        
        # 6. Save Results
        save_forecasts(forecasts, output_path)
        
        logger.info("Pipeline completed successfully.")
        
    except RuntimeError as e:
        logger.critical(f"Pipeline halted due to error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.critical(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()