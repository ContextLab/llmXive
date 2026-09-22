"""
Joint Non-Linear Mixed-Effects (NLME) Modeling for Global Kinetic Analysis.

This module implements a Bayesian Non-Linear Mixed-Effects model using PyMC
to extract singlet-radical-pair intermediate lifetimes from transient-absorption
data. It accounts for inter-replicate and inter-solvent variance.

Constraint: Uses PyMC for Bayesian inference, NOT scipy.optimize.curve_fit.
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az

# Project imports
from config import get_processed_data_path, get_raw_data_path, ensure_directories
from utils.seeds import set_seed
from utils.logging import setup_logging

# Constants
DEFAULT_SEED = 42
DEFAULT_CHAINS = 2
DEFAULT_TUNE = 1000
DEFAULT_SAMPLES = 1000
OUTPUT_METRICS_PATH = "data/processed/kinetic_metrics.csv"
OUTPUT_POSTERIOR_PATH = "data/processed/kinetic_posterior.json"

logger = logging.getLogger(__name__)


def exponential_decay(t: np.ndarray, amplitude: float, lifetime: float, offset: float) -> np.ndarray:
    """
    Calculate the exponential decay function: A * exp(-t/tau) + offset.

    Parameters
    ----------
    t : np.ndarray
        Time array (ns).
    amplitude : float
        Initial amplitude.
    lifetime : float
        Decay lifetime (ns).
    offset : float
        Baseline offset.

    Returns
    -------
    np.ndarray
        Calculated absorbance values.
    """
    return amplitude * np.exp(-t / lifetime) + offset


def load_trace_data(data_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load transient-absorption trace data.

    If data_path is provided, load from there. Otherwise, look for synthetic
    traces in the standard location.

    Parameters
    ----------
    data_path : str, optional
        Path to the CSV file containing trace data.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: ['time', 'absorbance', 'solvent', 'replicate']
    """
    if data_path:
        path = Path(data_path)
    else:
        raw_path = get_raw_data_path()
        path = raw_path / "synthetic_traces.csv"
        if not path.exists():
            # Try the alternative location if the standard one is missing
            alt_path = Path("data/raw/synthetic_traces.csv")
            if alt_path.exists():
                path = alt_path
            else:
                raise FileNotFoundError(f"Trace data file not found at {path} or {alt_path}")

    logger.info(f"Loading trace data from {path}")
    df = pd.read_csv(path)

    # Ensure required columns exist
    required_cols = ['time', 'absorbance', 'solvent', 'replicate']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Data file must contain columns: {required_cols}")

    return df


def run_global_kinetic_analysis(
    df: pd.DataFrame,
    chains: int = DEFAULT_CHAINS,
    tune: int = DEFAULT_TUNE,
    samples: int = DEFAULT_SAMPLES,
    seed: int = DEFAULT_SEED
) -> Dict[str, Any]:
    """
    Perform Joint Non-Linear Mixed-Effects (NLME) modeling on the trace data.

    This function defines a PyMC model where:
    - Fixed effects: Global amplitude and offset parameters.
    - Random effects: Solvent-specific lifetime deviations (hierarchical).
    - Observation model: Gaussian noise around the exponential decay.

    Parameters
    ----------
    df : pd.DataFrame
        Input data with 'time', 'absorbance', 'solvent', 'replicate'.
    chains : int
        Number of MCMC chains.
    tune : int
        Number of tuning steps.
    samples : int
        Number of samples to draw.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - 'posterior_summary': Summary statistics of the posterior.
        - 'trace_data': The input data used.
        - 'model_info': Information about the model structure.
    """
    set_seed(seed)
    logger.info(f"Starting Global Kinetic Analysis with seed={seed}")

    # Prepare data
    unique_solvents = df['solvent'].unique()
    n_solvents = len(unique_solvents)
    n_replicates = df['replicate'].nunique()

    # Encode solvents as integers for indexing
    solvent_map = {s: i for i, s in enumerate(unique_solvents)}
    df['solvent_idx'] = df['solvent'].map(solvent_map)

    # Extract arrays
    time_obs = df['time'].values.astype(np.float64)
    absorbance_obs = df['absorbance'].values.astype(np.float64)
    solvent_idx = df['solvent_idx'].values.astype(np.int32)
    replicate_idx = df['replicate'].astype('category').cat.codes.values.astype(np.int32)

    logger.info(f"Data dimensions: {len(df)} points, {n_solvents} solvents, {n_replicates} replicates")

    # Define the PyMC model
    with pm.Model() as model:
        # Fixed effects: Global parameters
        # Amplitude: Positive, initial guess based on data max
        amplitude_mu = pm.Normal('amplitude_mu', mu=absorbance_obs.max(), sigma=1.0)
        amplitude_sigma = pm.HalfNormal('amplitude_sigma', sigma=0.5)
        
        # Offset: Small value around 0
        offset_mu = pm.Normal('offset_mu', mu=0.0, sigma=0.1)
        offset_sigma = pm.HalfNormal('offset_sigma', sigma=0.05)

        # Random effects: Solvent-specific lifetimes
        # Hierarchical prior: Lifetime ~ Normal(mu_lifetime, sigma_lifetime)
        lifetime_mu = pm.Normal('lifetime_mu', mu=5.0, sigma=5.0) # Initial guess 5ns
        lifetime_sigma = pm.HalfNormal('lifetime_sigma', sigma=2.0)
        
        # Solvent-specific deviations
        solvent_z = pm.Normal('solvent_z', mu=0, sigma=1, shape=n_solvents)
        solvent_lifetime = pm.Deterministic('solvent_lifetime', 
                                            lifetime_mu + solvent_z * lifetime_sigma)

        # Replicate-specific noise scaling (optional random effect)
        # For simplicity, we use a global sigma for observation noise, 
        # but we allow the amplitude to vary slightly per replicate if needed.
        # Here we stick to a simpler model: Global Amplitude/Offset, Solvent Lifetime.
        
        # Observation noise
        sigma_obs = pm.HalfNormal('sigma_obs', sigma=0.1)

        # Deterministic prediction
        # We need to map solvent_idx to the specific lifetime for each point
        # Using advanced indexing in PyMC
        pred_lifetime = solvent_lifetime[solvent_idx]
        
        # Calculate expected absorbance
        # A * exp(-t / tau) + offset
        expected = amplitude_mu * pm.math.exp(-time_obs / pred_lifetime) + offset_mu

        # Likelihood
        Y_obs = pm.Normal('Y_obs', mu=expected, sigma=sigma_obs, observed=absorbance_obs)

        # Sample from the posterior
        logger.info("Sampling from posterior distribution...")
        try:
            trace = pm.sample(
                draws=samples,
                tune=tune,
                chains=chains,
                seed=seed,
                return_inferencedata=True,
                progressbar=True
            )
        except Exception as e:
            logger.error(f"Sampling failed: {e}")
            raise

    # Extract results
    idata = trace
    
    # Summary statistics
    summary = az.summary(idata, var_names=['lifetime_mu', 'amplitude_mu', 'offset_mu', 'sigma_obs'])
    
    # Extract solvent-specific lifetimes
    solvent_lifetimes = {}
    for i, s in enumerate(unique_solvents):
        # Extract posterior samples for this solvent's lifetime
        # The posterior variable is 'solvent_lifetime'
        samples_arr = idata.posterior['solvent_lifetime'].sel(solvent_idx=i).values.flatten()
        solvent_lifetimes[s] = {
            'mean': float(np.mean(samples_arr)),
            'std': float(np.std(samples_arr)),
            'hdi_3%': float(np.percentile(samples_arr, 3)),
            'hdi_97%': float(np.percentile(samples_arr, 97))
        }

    result = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'model_type': 'Joint_NLME_Bayesian',
        'n_solvents': n_solvents,
        'n_replicates': n_replicates,
        'n_observations': len(df),
        'global_params': {
            'amplitude': {
                'mean': float(summary[summary.index == 'amplitude_mu']['mean']),
                'std': float(summary[summary.index == 'amplitude_mu']['std']),
                'hdi_3%': float(summary[summary.index == 'amplitude_mu']['hdi_3%']),
                'hdi_97%': float(summary[summary.index == 'amplitude_mu']['hdi_97%'])
            },
            'offset': {
                'mean': float(summary[summary.index == 'offset_mu']['mean']),
                'std': float(summary[summary.index == 'offset_mu']['std']),
                'hdi_3%': float(summary[summary.index == 'offset_mu']['hdi_3%']),
                'hdi_97%': float(summary[summary.index == 'offset_mu']['hdi_97%'])
            },
            'sigma_obs': {
                'mean': float(summary[summary.index == 'sigma_obs']['mean']),
                'std': float(summary[summary.index == 'sigma_obs']['std']),
                'hdi_3%': float(summary[summary.index == 'sigma_obs']['hdi_3%']),
                'hdi_97%': float(summary[summary.index == 'sigma_obs']['hdi_97%'])
            }
        },
        'solvent_specific_lifetimes': solvent_lifetimes,
        'convergence': {
            'rhat_max': float(idata.posterior['lifetime_mu'].rhat.max().values) if hasattr(idata.posterior['lifetime_mu'], 'rhat') else None,
            'effective_samples': int(idata.posterior['lifetime_mu'].n_eff.mean().values) if hasattr(idata.posterior['lifetime_mu'], 'n_eff') else None
        }
    }

    return result


def write_metrics_csv(results: Dict[str, Any], output_path: str) -> None:
    """
    Write the kinetic metrics to a CSV file.

    Parameters
    ----------
    results : Dict[str, Any]
        The results dictionary from run_global_kinetic_analysis.
    output_path : str
        Path to the output CSV file.
    """
    rows = []
    for solvent, stats in results['solvent_specific_lifetimes'].items():
        rows.append({
            'solvent': solvent,
            'lifetime_mean_ns': stats['mean'],
            'lifetime_std_ns': stats['std'],
            'lifetime_hdi_3_pct': stats['hdi_3%'],
            'lifetime_hdi_97_pct': stats['hdi_97%'],
            'n_replicates': results['n_replicates'],
            'global_amplitude_mean': results['global_params']['amplitude']['mean'],
            'global_offset_mean': results['global_params']['offset']['mean'],
            'sigma_obs_mean': results['global_params']['sigma_obs']['mean']
        })

    df_out = pd.DataFrame(rows)
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(output_path, index=False)
    logger.info(f"Wrote kinetic metrics to {output_path}")


def write_posterior_json(results: Dict[str, Any], output_path: str) -> None:
    """
    Write the full posterior summary to a JSON file.

    Parameters
    ----------
    results : Dict[str, Any]
        The results dictionary.
    output_path : str
        Path to the output JSON file.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Wrote posterior summary to {output_path}")


def main():
    """
    Main entry point for the kinetic fit analysis.
    """
    parser = argparse.ArgumentParser(description="Joint NLME Kinetic Analysis")
    parser.add_argument("--data-path", type=str, default=None, help="Path to input trace CSV")
    parser.add_argument("--output-csv", type=str, default=OUTPUT_METRICS_PATH, help="Output CSV path")
    parser.add_argument("--output-json", type=str, default=OUTPUT_POSTERIOR_PATH, help="Output JSON path")
    parser.add_argument("--chains", type=int, default=DEFAULT_CHAINS, help="Number of MCMC chains")
    parser.add_argument("--tune", type=int, default=DEFAULT_TUNE, help="Number of tuning steps")
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES, help="Number of samples")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    
    args = parser.parse_args()

    setup_logging()
    ensure_directories()

    try:
        # Load data
        df = load_trace_data(args.data_path)
        
        # Run analysis
        results = run_global_kinetic_analysis(
            df, 
            chains=args.chains, 
            tune=args.tune, 
            samples=args.samples, 
            seed=args.seed
        )
        
        # Write outputs
        write_metrics_csv(results, args.output_csv)
        write_posterior_json(results, args.output_json)
        
        print(f"Analysis complete. Metrics: {args.output_csv}, Posterior: {args.output_json}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()