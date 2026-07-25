"""
Bootstrap confidence interval calculation for KS statistics.

This module implements the bootstrap procedure to estimate confidence intervals
for Kolmogorov-Smirnov statistics comparing standard hypothesis test p-values
against a permutation-based gold standard.

Output: data/results/bootstrap_cis.json
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy import stats

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.simulation import SyntheticDataset
from analyze_pvalues import calculate_ks_statistic

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_N_BOOTSTRAP = 1000
DEFAULT_CONFIDENCE_LEVEL = 0.95
OUTPUT_PATH = Path("data/results/bootstrap_cis.json")


def calculate_bootstrap_ci(
    ks_values: np.ndarray,
    confidence_level: float = DEFAULT_CONFIDENCE_LEVEL
) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence interval for KS statistics.
    
    Uses the percentile method to compute the confidence interval from the
    bootstrap distribution of KS statistics.
    
    Args:
        ks_values: Array of KS statistics from bootstrap resamples.
        confidence_level: Confidence level (e.g., 0.95 for 95% CI).
        
    Returns:
        Tuple of (lower_bound, upper_bound) for the confidence interval.
        
    Raises:
        ValueError: If ks_values is empty or has insufficient samples.
    """
    if len(ks_values) == 0:
        raise ValueError("ks_values array is empty")
        
    if len(ks_values) < 10:
        logger.warning(f"Only {len(ks_values)} bootstrap samples available. "
                     "Confidence intervals may be unreliable.")
    
    alpha = 1 - confidence_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    lower_bound = np.percentile(ks_values, lower_percentile)
    upper_bound = np.percentile(ks_values, upper_percentile)
    
    return float(lower_bound), float(upper_bound)


def load_trajectory_data(
    trajectory_path: Path
) -> Dict[str, Any]:
    """
    Load p-value trajectory data from a JSON file.
    
    Args:
        trajectory_path: Path to the trajectory JSON file.
        
    Returns:
        Dictionary containing trajectory data.
        
    Raises:
        FileNotFoundError: If the trajectory file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if not trajectory_path.exists():
        raise FileNotFoundError(f"Trajectory file not found: {trajectory_path}")
        
    with open(trajectory_path, 'r') as f:
        data = json.load(f)
        
    logger.info(f"Loaded trajectory data from {trajectory_path}")
    return data


def run_bootstrap_analysis(
    standard_pvalues: np.ndarray,
    permutation_pvalues: np.ndarray,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
    random_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run bootstrap analysis to calculate confidence intervals for KS statistics.
    
    This function resamples the standard p-values with replacement, calculates
    the KS statistic against the permutation reference for each resample, and
    computes the confidence interval from the bootstrap distribution.
    
    Args:
        standard_pvalues: Array of p-values from standard hypothesis tests.
        permutation_pvalues: Array of p-values from permutation test (gold standard).
        n_bootstrap: Number of bootstrap resamples.
        confidence_level: Confidence level for the interval.
        random_seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing:
            - KS_statistic: The original KS statistic (full sample).
            - bootstrap_ci_lower: Lower bound of the confidence interval.
            - bootstrap_ci_upper: Upper bound of the confidence interval.
            - n_bootstrap: Number of bootstrap samples used.
            - confidence_level: Confidence level used.
            - ks_bootstrap_values: Array of all bootstrap KS values (for diagnostics).
    """
    if random_seed is not None:
        np.random.seed(random_seed)
        
    if len(standard_pvalues) == 0 or len(permutation_pvalues) == 0:
        raise ValueError("Input p-value arrays cannot be empty")
        
    # Calculate original KS statistic (full sample)
    original_ks = calculate_ks_statistic(standard_pvalues, permutation_pvalues)
    logger.info(f"Original KS statistic: {original_ks:.6f}")
    
    # Bootstrap resampling
    ks_bootstrap_values = []
    n = len(standard_pvalues)
    
    logger.info(f"Starting bootstrap analysis with {n_bootstrap} resamples...")
    
    for i in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        resampled_pvalues = standard_pvalues[indices]
        
        # Calculate KS statistic for this resample
        ks_val = calculate_ks_statistic(resampled_pvalues, permutation_pvalues)
        ks_bootstrap_values.append(ks_val)
        
        if (i + 1) % 100 == 0:
            logger.debug(f"Completed {i + 1}/{n_bootstrap} bootstrap resamples")
    
    ks_bootstrap_values = np.array(ks_bootstrap_values)
    
    # Calculate confidence interval
    ci_lower, ci_upper = calculate_bootstrap_ci(
        ks_bootstrap_values, 
        confidence_level
    )
    
    logger.info(f"Bootstrap CI ({confidence_level*100:.0f}%): "
               f"[{ci_lower:.6f}, {ci_upper:.6f}]")
    
    return {
        'KS_statistic': float(original_ks),
        'bootstrap_ci_lower': ci_lower,
        'bootstrap_ci_upper': ci_upper,
        'n_bootstrap': n_bootstrap,
        'confidence_level': confidence_level,
        'ks_bootstrap_values': ks_bootstrap_values.tolist()
    }


def main():
    """
    Main entry point for bootstrap CI calculation.
    
    Reads trajectory data from data/synthetic/trajectories/, performs bootstrap
    analysis for each dataset, and stores results in data/results/bootstrap_cis.json.
    """
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    trajectories_dir = Path("data/synthetic/trajectories")
    if not trajectories_dir.exists():
        logger.error(f"Trajectories directory not found: {trajectories_dir}")
        logger.error("Please run data generation and hypothesis testing first.")
        sys.exit(1)
    
    # Find all trajectory files
    trajectory_files = list(trajectories_dir.glob("*.json"))
    if not trajectory_files:
        logger.error(f"No trajectory files found in {trajectories_dir}")
        sys.exit(1)
    
    logger.info(f"Found {len(trajectory_files)} trajectory files to process")
    
    results = []
    
    for traj_file in trajectory_files:
        try:
            logger.info(f"Processing {traj_file.name}...")
            
            # Load trajectory data
            traj_data = load_trajectory_data(traj_file)
            
            # Extract metadata
            metadata = traj_data.get('metadata', {})
            seed = metadata.get('seed')
            rho = metadata.get('rho')
            n = metadata.get('n')
            p = metadata.get('p')
            
            # Extract p-values
            standard_pvalues = np.array(traj_data.get('standard_pvalues', []))
            permutation_pvalues = np.array(traj_data.get('permutation_pvalues', []))
            
            if len(standard_pvalues) == 0 or len(permutation_pvalues) == 0:
                logger.warning(f"Skipping {traj_file.name}: missing p-value data")
                continue
            
            # Run bootstrap analysis
            bootstrap_result = run_bootstrap_analysis(
                standard_pvalues=standard_pvalues,
                permutation_pvalues=permutation_pvalues,
                n_bootstrap=DEFAULT_N_BOOTSTRAP,
                confidence_level=DEFAULT_CONFIDENCE_LEVEL,
                random_seed=seed if seed is not None else 42
            )
            
            # Format result according to specification
            result_entry = {
                'KS_statistic': bootstrap_result['KS_statistic'],
                'bootstrap_ci_lower': bootstrap_result['bootstrap_ci_lower'],
                'bootstrap_ci_upper': bootstrap_result['bootstrap_ci_upper'],
                'rho': rho,
                'n': n,
                'p': p,
                'seed': seed
            }
            
            results.append(result_entry)
            logger.info(f"Completed {traj_file.name}: KS={bootstrap_result['KS_statistic']:.4f}, "
                       f"CI=[{bootstrap_result['bootstrap_ci_lower']:.4f}, "
                       f"{bootstrap_result['bootstrap_ci_upper']:.4f}]")
            
        except Exception as e:
            logger.error(f"Error processing {traj_file.name}: {str(e)}", exc_info=True)
            continue
    
    # Write results to output file
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Bootstrap CI results written to {OUTPUT_PATH}")
    logger.info(f"Processed {len(results)} datasets successfully")
    
    return results


if __name__ == "__main__":
    main()
