"""
Bootstrap resampling analysis for latent space variance stability.

This module implements bootstrap resampling on the latent representations
after thinning the dataset by a factor >= 2 * tau_int (integrated autocorrelation time).

Dependencies:
- utils.calculate_autocorrelation_time (T007)
- utils.thin_dataset (T007)
- analysis.load_latent_data (T026)
"""
import os
import sys
import logging
import argparse
import json
import numpy as np
from typing import Dict, Tuple, List, Optional

# Import from existing project modules
from utils import calculate_autocorrelation_time, thin_dataset
from analysis import load_latent_data, calculate_total_variance_per_bin
from config import get_config

logger = logging.getLogger(__name__)

def bootstrap_resample_variance(
    latent_mu: np.ndarray,
    temperatures: np.ndarray,
    n_bootstrap: int = 1000,
    random_seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Perform bootstrap resampling to estimate confidence intervals for variance.
    
    Args:
        latent_mu: Latent mean vectors of shape (N_samples, latent_dim)
        temperatures: Temperature values corresponding to each sample
        n_bootstrap: Number of bootstrap iterations
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (mean_variance, std_variance, variance_percentile_95)
        where:
        - mean_variance: Mean variance across bootstrap samples per temperature bin
        - std_variance: Standard deviation across bootstrap samples per temperature bin
        - variance_percentile_95: 95th percentile of bootstrap distribution
    """
    if random_seed is not None:
        np.random.seed(random_seed)
        
    unique_temps = np.unique(temperatures)
    n_bins = len(unique_temps)
    latent_dim = latent_mu.shape[1]
    
    # Storage for bootstrap results
    bootstrap_variances = np.zeros((n_bootstrap, n_bins, latent_dim))
    
    logger.info(f"Starting bootstrap resampling: {n_bootstrap} iterations")
    logger.info(f"Data shape: {latent_mu.shape}, Temperature bins: {n_bins}")
    
    for i in range(n_bootstrap):
        if (i + 1) % 100 == 0:
            logger.info(f"Bootstrap iteration {i + 1}/{n_bootstrap}")
            
        # Resample with replacement
        indices = np.random.choice(len(latent_mu), size=len(latent_mu), replace=True)
        resampled_mu = latent_mu[indices]
        resampled_temps = temperatures[indices]
        
        # Calculate variance for each temperature bin
        for j, temp in enumerate(unique_temps):
            mask = resampled_temps == temp
            if np.sum(mask) > 0:
                # Variance across samples for each latent dimension
                bootstrap_variances[i, j, :] = np.var(resampled_mu[mask], axis=0)
            else:
                bootstrap_variances[i, j, :] = np.nan
    
    # Calculate statistics across bootstrap samples
    mean_variance = np.nanmean(bootstrap_variances, axis=0)
    std_variance = np.nanstd(bootstrap_variances, axis=0)
    percentile_95 = np.nanpercentile(bootstrap_variances, 95, axis=0)
    
    return mean_variance, std_variance, percentile_95

def run_bootstrap_analysis(
    data_path: str,
    tau_int_path: str,
    output_path: str,
    n_bootstrap: int = 1000,
    thinning_factor: float = 2.0,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Main function to run bootstrap analysis pipeline.
    
    Args:
        data_path: Path to latent data file
        tau_int_path: Path to autocorrelation time results (from T007)
        output_path: Path to save bootstrap results
        n_bootstrap: Number of bootstrap iterations
        thinning_factor: Factor for thinning (should be >= 2.0)
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing analysis results
    """
    config = get_config()
    
    # Load latent data
    logger.info(f"Loading latent data from {data_path}")
    latent_data = load_latent_data(data_path)
    latent_mu = latent_data['mu']
    temperatures = latent_data['temperatures']
    
    # Load autocorrelation times
    logger.info(f"Loading autocorrelation times from {tau_int_path}")
    with open(tau_int_path, 'r') as f:
        tau_results = json.load(f)
    
    # Determine thinning factor based on max tau_int
    tau_int_values = tau_results.get('tau_int_values', {})
    max_tau = max(tau_int_values.values()) if tau_int_values else 1.0
    effective_thinning = max(int(thinning_factor * max_tau), 1)
    
    logger.info(f"Max tau_int: {max_tau:.2f}, Using thinning factor: {effective_thinning}")
    
    # Thin the dataset
    logger.info("Thinning dataset...")
    thin_indices = thin_dataset(
        np.arange(len(latent_mu)),
        effective_thinning,
        temperatures=temperatures
    )
    
    thinned_mu = latent_mu[thin_indices]
    thinned_temps = temperatures[thin_indices]
    
    logger.info(f"Dataset thinned from {len(latent_mu)} to {len(thinned_mu)} samples")
    
    # Perform bootstrap resampling
    mean_var, std_var, p95_var = bootstrap_resample_variance(
        thinned_mu,
        thinned_temps,
        n_bootstrap=n_bootstrap,
        random_seed=random_seed
    )
    
    # Prepare results
    results = {
        'n_bootstrap': n_bootstrap,
        'thinning_factor': effective_thinning,
        'max_tau_int': max_tau,
        'original_samples': len(latent_mu),
        'thinned_samples': len(thinned_mu),
        'random_seed': random_seed,
        'unique_temperatures': unique_temps.tolist() if (unique_temps := np.unique(thinned_temps)).ndim == 1 else unique_temps,
        'mean_variance': mean_var.tolist(),
        'std_variance': std_var.tolist(),
        'percentile_95_variance': p95_var.tolist(),
        'confidence_interval_95': {
            'lower': (mean_var - 1.96 * std_var).tolist(),
            'upper': (mean_var + 1.96 * std_var).tolist()
        }
    }
    
    # Save results
    logger.info(f"Saving results to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("Bootstrap analysis completed successfully")
    return results

def main():
    """Command-line interface for bootstrap analysis."""
    parser = argparse.ArgumentParser(description='Bootstrap resampling analysis for latent variance')
    parser.add_argument('--data-path', type=str, required=True, help='Path to latent data file')
    parser.add_argument('--tau-int-path', type=str, required=True, help='Path to autocorrelation time results')
    parser.add_argument('--output-path', type=str, required=True, help='Path to save bootstrap results')
    parser.add_argument('--n-bootstrap', type=int, default=1000, help='Number of bootstrap iterations')
    parser.add_argument('--thinning-factor', type=float, default=2.0, help='Thinning factor (>= 2.0)')
    parser.add_argument('--random-seed', type=int, default=42, help='Random seed')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        results = run_bootstrap_analysis(
            data_path=args.data_path,
            tau_int_path=args.tau_int_path,
            output_path=args.output_path,
            n_bootstrap=args.n_bootstrap,
            thinning_factor=args.thinning_factor,
            random_seed=args.random_seed
        )
        
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        logger.error(f"Bootstrap analysis failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
