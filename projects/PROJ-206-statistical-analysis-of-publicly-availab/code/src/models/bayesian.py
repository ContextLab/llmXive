import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
from scipy import stats

from src.utils.config import get_data_root, get_state_root, resolve_path
from src.utils.logging import get_logger

logger = get_logger(__name__)

def configure_nuts_sampler(target_accept: float = 0.9, tune_steps: int = 1000) -> Dict[str, Any]:
    """
    Configure the NUTS sampler for CPU-only execution.
    """
    return {
        "target_accept": target_accept,
        "tune": tune_steps,
        "draws": 1000,
        "cores": 1,  # Force single core for CPU stability
        "random_seed": 42
    }

def fit_random_walk_model(df: pd.DataFrame, sampler_config: Dict[str, Any]) -> Tuple[Any, pm.Model]:
    """
    Fit a Random Walk hierarchical model:
    latent weekly preference θₜ ~ Normal(θₜ₋₁, σₜ²)
    observation noise τᵢ²

    Args:
        df: Harmonized poll data with columns: 'week_start', 'vote_share', 'sample_size', 'pollster_id'
        sampler_config: Configuration dict for NUTS sampler

    Returns:
        (trace, model) tuple
    """
    if df.empty:
        raise ValueError("Input dataframe is empty. Cannot fit model.")

    # Prepare data
    df = df.sort_values('week_start').reset_index(drop=True)
    n_weeks = df['week_start'].nunique()
    n_polls = len(df)

    # Map weeks to integers 0..n_weeks-1
    week_map = {w: i for i, w in enumerate(df['week_start'].unique())}
    df['week_idx'] = df['week_start'].map(week_map)

    y = df['vote_share'].values
    pollster_ids = df['pollster_id'].values if 'pollster_id' in df.columns else np.zeros(n_polls, dtype=int)

    logger.info(f"Fitting Random Walk model with {n_weeks} weeks and {n_polls} polls.")

    with pm.Model() as model:
        # Priors
        sigma_t = pm.HalfNormal('sigma_t', sigma=1.0)  # Random walk step size
        tau = pm.HalfNormal('tau', sigma=1.0)          # Observation noise
        
        # Random Walk prior for latent weekly preferences
        # θ₀ ~ Normal(50, 10) (centered around 50% for 2-party)
        theta = pm.GaussianRandomWalk('theta', sigma=sigma_t, shape=n_weeks, init_dist=pm.Normal.dist(mu=50, sigma=10))

        # Likelihood
        # If pollster_id exists, we could add pollster bias, but for basic RW:
        mu = theta[df['week_idx'].values]
        
        # Observation model
        y_obs = pm.Normal('y_obs', mu=mu, sigma=tau, observed=y)

        # Sample
        trace = pm.sample(
            **sampler_config,
            return_inferencedata=True,
            compute_convergence_checks=False  # We do this manually
        )

    return trace, model

def check_convergence(trace: az.InferenceData, threshold: float = 1.05) -> bool:
    """
    Check convergence of the MCMC sampling using R-hat statistic.
    
    Args:
        trace: Arviz InferenceData object from PyMC sampling
        threshold: Maximum allowed R-hat value (default 1.05)

    Returns:
        True if all parameters have R-hat <= threshold, False otherwise.

    Raises:
        RuntimeError: If R-hat exceeds threshold for any parameter.
    """
    logger.info("Checking convergence (R-hat)...")
    
    # Calculate R-hat
    rhat_data = az.rhat(trace)
    
    # Convert to dict if it's an xarray DataArray
    if hasattr(rhat_data, 'to_dict'):
        rhat_dict = rhat_data.to_dict()
    else:
        rhat_dict = dict(rhat_data)

    failed_params = []
    for param, value in rhat_dict.items():
        # Handle scalar or array values
        if hasattr(value, 'max'):
            max_val = float(value.max())
        else:
            max_val = float(value)
        
        if max_val > threshold:
            failed_params.append((param, max_val))

    if failed_params:
        error_msg = "Convergence check FAILED. R-hat > {:.2f} for the following parameters:\n".format(threshold)
        for param, val in failed_params:
            error_msg += "  - {}: R-hat = {:.4f}\n".format(param, val)
        error_msg += "The model has not converged. Halting pipeline."
        
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("Convergence check PASSED. All R-hat values <= {:.2f}.".format(threshold))
    return True

def run_bayesian_analysis(
    input_path: str,
    output_path: str,
    sampler_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run the full Bayesian analysis pipeline:
    1. Load data
    2. Fit Random Walk model
    3. Check convergence (T023)
    4. Generate forecasts and save results

    Args:
        input_path: Path to harmonized poll data CSV
        output_path: Path to save forecast results CSV
        sampler_config: Optional sampler configuration

    Returns:
        Dictionary with analysis results summary
    """
    if sampler_config is None:
        sampler_config = configure_nuts_sampler()

    # Load data
    data_root = get_data_root()
    df = pd.read_csv(resolve_path(input_path, base=data_root))
    
    if df.empty:
        raise ValueError("Input data is empty.")

    # Fit model
    try:
        trace, model = fit_random_walk_model(df, sampler_config)
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        raise

    # T023: Check convergence
    try:
        check_convergence(trace, threshold=1.05)
    except RuntimeError as e:
        # Re-raise to halt pipeline as per requirement
        raise

    # Generate forecasts (simplified: use posterior mean of last week)
    # In a real scenario, we'd project forward or aggregate for specific election dates
    posterior_mean = trace.posterior['theta'].mean(dim=['chain', 'draw'])
    last_week_forecast = posterior_mean.values[-1]
    
    # Calculate 95% credible interval
    ci_lower = trace.posterior['theta'].quantile(0.025, dim=['chain', 'draw']).values[-1]
    ci_upper = trace.posterior['theta'].quantile(0.975, dim=['chain', 'draw']).values[-1]

    # Save results
    results_df = pd.DataFrame({
        'method': 'Bayesian_RandomWalk',
        'forecast': [last_week_forecast],
        'ci_lower': [ci_lower],
        'ci_upper': [ci_upper]
    })
    
    results_df.to_csv(resolve_path(output_path, base=data_root), index=False)
    logger.info(f"Bayesian forecasts saved to {output_path}")

    return {
        'forecast': last_week_forecast,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'converged': True
    }

def main():
    """
    Entry point for running Bayesian analysis from command line.
    """
    logger.info("Starting Bayesian Analysis (T023 Convergence Check)...")
    
    input_file = "data/processed/poll_data_cleaned.csv"
    output_file = "data/processed/bayesian_forecasts.csv"
    
    try:
        results = run_bayesian_analysis(input_file, output_file)
        logger.info(f"Analysis complete. Forecast: {results['forecast']:.2f}% "
                    f"({results['ci_lower']:.2f} - {results['ci_upper']:.2f})")
    except RuntimeError as e:
        logger.error(f"Pipeline halted due to convergence failure: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()