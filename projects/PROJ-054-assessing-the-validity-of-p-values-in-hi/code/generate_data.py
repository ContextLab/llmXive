"""
Data generation script for high-dimensional p-value validity assessment.
Implements parameter sweep logic for n, p, rho, and distribution_type.
"""
import numpy as np
import json
import hashlib
import os
import logging
import argparse
import csv
from pathlib import Path
from typing import List, Dict, Any, Iterator, Tuple

# Import from local utils
from utils.exceptions import HighDimensionalInstabilityError
from utils.regularization import is_condition_number_acceptable, regularize_covariance
from utils.simulation import RNGWrapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RHO_VALUES = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9]
N_VALUES = [50, 100, 200, 500]
P_VALUES = [500, 1000, 2000, 5000]
DISTRIBUTION_TYPES = ["Normal", "t-dist(df=3)", "Skewed Normal(skew=2.0)"]
MASTER_SEED_FILE = "data/sweep/master_seed.txt"
POWER_ANALYSIS_FILE = "data/sweep/power_analysis_result.json"
PARAMS_OUTPUT_FILE = "data/sweep/params.csv"

class SweepConfig:
    """Configuration for the parameter sweep."""
    def __init__(self, n_values: List[int], p_values: List[int], 
                 rho_values: List[float], dist_types: List[str]):
        self.n_values = n_values
        self.p_values = p_values
        self.rho_values = rho_values
        self.dist_types = dist_types

def load_required_iterations() -> int:
    """
    Load the required iteration count from the power analysis result.
    
    Returns:
        int: The number of iterations required for statistical power >= 0.8.
        
    Raises:
        FileNotFoundError: If the power analysis result file is missing.
        ValueError: If the file is malformed or missing the 'iterations' key.
    """
    power_file = Path(POWER_ANALYSIS_FILE)
    if not power_file.exists():
        raise FileNotFoundError(
            f"Power analysis result not found at {POWER_ANALYSIS_FILE}. "
            f"Please run T011a first to generate this file."
        )
    
    try:
        with open(power_file, 'r') as f:
            data = json.load(f)
        
        if 'iterations' not in data:
            raise ValueError("Power analysis result missing 'iterations' key.")
        
        iterations = data['iterations']
        if not isinstance(iterations, int) or iterations <= 0:
            raise ValueError(f"Iterations must be a positive integer, got {iterations}")
        
        logger.info(f"Loaded required iterations: {iterations}")
        return iterations
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in power analysis file: {e}")

def load_master_seed() -> int:
    """
    Load the master seed from the seed file, creating it if it doesn't exist.
    
    Returns:
        int: The master seed value.
    """
    seed_file = Path(MASTER_SEED_FILE)
    
    # Create the file if it doesn't exist with default seed 42
    if not seed_file.exists():
        logger.info(f"Master seed file not found. Creating with default value 42.")
        seed_file.parent.mkdir(parents=True, exist_ok=True)
        with open(seed_file, 'w') as f:
            f.write("42")
        return 42
    
    try:
        with open(seed_file, 'r') as f:
            content = f.read().strip()
            master_seed = int(content)
            logger.info(f"Loaded master seed: {master_seed}")
            return master_seed
    except ValueError as e:
        raise ValueError(f"Invalid master seed in {MASTER_SEED_FILE}: {e}")

def generate_correlated_data(n: int, p: int, rho: float, rng: RNGWrapper) -> np.ndarray:
    """
    Generate a high-dimensional dataset with controlled correlation structure.
    
    Args:
        n: Number of samples
        p: Number of features
        rho: Correlation coefficient for the equicorrelation matrix
        rng: RNGWrapper instance for deterministic randomness
        
    Returns:
        np.ndarray: Data matrix of shape (n, p)
        
    Raises:
        HighDimensionalInstabilityError: If p/n > 10 or covariance matrix is singular
    """
    # Check p/n ratio constraint
    if p / n > 10:
        raise HighDimensionalInstabilityError(
            f"p/n ratio {p/n} exceeds threshold of 10. "
            f"Configuration: n={n}, p={p}"
        )
    
    # Generate equicorrelation matrix
    # Sigma_ij = rho if i != j, 1 if i == j
    Sigma = np.full((p, p), rho)
    np.fill_diagonal(Sigma, 1.0)
    
    # Check condition number
    try:
        cond_num = np.linalg.cond(Sigma)
        if not is_condition_number_acceptable(cond_num):
            raise HighDimensionalInstabilityError(
                f"Covariance matrix condition number {cond_num} exceeds "
                f"threshold of 1e12. Regularization failed."
            )
    except np.linalg.LinAlgError as e:
        raise HighDimensionalInstabilityError(
            f"Failed to compute condition number: {e}"
        )
    
    # Generate multivariate normal data
    # Use Cholesky decomposition for efficiency
    try:
        L = np.linalg.cholesky(Sigma)
        # Generate standard normal data
        Z = rng.standard_normal((n, p))
        # Transform to correlated data
        X = Z @ L.T
    except np.linalg.LinAlgError:
        # Try regularization if Cholesky fails
        logger.warning("Cholesky decomposition failed. Attempting regularization.")
        try:
            Sigma_reg = regularize_covariance(Sigma)
            L = np.linalg.cholesky(Sigma_reg)
            Z = rng.standard_normal((n, p))
            X = Z @ L.T
        except Exception as e:
            raise HighDimensionalInstabilityError(
                f"Regularization failed to produce a valid covariance matrix: {e}"
            )
    
    return X

def generate_distribution_violations(X: np.ndarray, dist_type: str, rng: RNGWrapper) -> np.ndarray:
    """
    Apply distributional violations to the generated data.
    
    Args:
        X: Base correlated data matrix
        dist_type: Type of distribution violation to apply
        rng: RNGWrapper instance
        
    Returns:
        np.ndarray: Data with applied distributional violations
    """
    if dist_type == "Normal":
        return X
    
    elif dist_type == "t-dist(df=3)":
        # Transform to t-distribution with df=3
        # Use inverse CDF method: transform normal to uniform, then to t
        # Since X is already normal, we can use the probability integral transform
        from scipy import stats
        # Convert normal to uniform
        U = stats.norm.cdf(X)
        # Convert uniform to t-distribution
        X_t = stats.t.ppf(U, df=3)
        return X_t
    
    elif dist_type == "Skewed Normal(skew=2.0)":
        # Apply skew-normal transformation
        from scipy import stats
        # Convert normal to uniform
        U = stats.norm.cdf(X)
        # Convert to skew-normal with alpha=2.0
        X_skew = stats.skewnorm.ppf(U, a=2.0)
        return X_skew
    
    else:
        raise ValueError(f"Unknown distribution type: {dist_type}")

def build_parameter_sweep(config: SweepConfig, iterations: int, master_seed: int) -> List[Dict[str, Any]]:
    """
    Build the full Cartesian product of parameters with deterministic seeds.
    
    Args:
        config: Sweep configuration
        iterations: Number of iterations per parameter combination
        master_seed: Base seed for deterministic generation
        
    Returns:
        List of parameter dictionaries with seeds
    """
    params_list = []
    index = 0
    
    # Create a mapping for rho to index
    rho_to_idx = {rho: i for i, rho in enumerate(sorted(RHO_VALUES))}
    
    for n in config.n_values:
        for p in config.p_values:
            for rho in config.rho_values:
                for dist_type in config.dist_types:
                    for iteration in range(iterations):
                        # Calculate deterministic seed
                        # seed = master_seed + (index * 10000) + (n*100 + p*10 + rho_idx)
                        rho_idx = rho_to_idx[rho]
                        seed = master_seed + (index * 10000) + (n*100 + p*10 + rho_idx)
                        
                        params_list.append({
                            'seed': seed,
                            'n': n,
                            'p': p,
                            'rho': rho,
                            'distribution_type': dist_type,
                            'iteration': iteration
                        })
                        
                        index += 1
    
    logger.info(f"Generated {len(params_list)} parameter combinations")
    return params_list

def write_params_csv(params_list: List[Dict[str, Any]], output_path: str):
    """
    Write parameter sweep results to CSV.
    
    Args:
        params_list: List of parameter dictionaries
        output_path: Path to output CSV file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['seed', 'n', 'p', 'rho', 'distribution_type', 'iteration']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(params_list)
    
    logger.info(f"Wrote {len(params_list)} rows to {output_path}")

def streaming_data_generator(params_list: List[Dict[str, Any]]) -> Iterator[Tuple[np.ndarray, Dict[str, Any]]]:
    """
    Generate data matrices one at a time based on parameters.
    
    Args:
        params_list: List of parameter dictionaries
        
    Yields:
        Tuple of (data_matrix, params_dict)
    """
    for params in params_list:
        seed = params['seed']
        n = params['n']
        p = params['p']
        rho = params['rho']
        dist_type = params['distribution_type']
        
        # Initialize RNG with specific seed
        rng = RNGWrapper()
        rng.reset(seed)
        
        # Generate correlated data
        X = generate_correlated_data(n, p, rho, rng)
        
        # Apply distribution violations
        X = generate_distribution_violations(X, dist_type, rng)
        
        yield X, params

def main():
    """Main entry point for data generation sweep."""
    parser = argparse.ArgumentParser(
        description="Generate high-dimensional datasets for p-value validity assessment"
    )
    parser.add_argument(
        '--out', 
        type=str, 
        default=PARAMS_OUTPUT_FILE,
        help='Output path for parameters CSV'
    )
    parser.add_argument(
        '--n-values', 
        type=int, 
        nargs='+', 
        default=N_VALUES,
        help='Sample sizes to sweep'
    )
    parser.add_argument(
        '--p-values', 
        type=int, 
        nargs='+', 
        default=P_VALUES,
        help='Feature counts to sweep'
    )
    parser.add_argument(
        '--rho-values', 
        type=float, 
        nargs='+', 
        default=RHO_VALUES,
        help='Correlation coefficients to sweep'
    )
    parser.add_argument(
        '--dist-types', 
        type=str, 
        nargs='+', 
        default=DISTRIBUTION_TYPES,
        help='Distribution types to sweep'
    )
    
    args = parser.parse_args()
    
    try:
        # Load required iterations from power analysis
        iterations = load_required_iterations()
        
        # Load or create master seed
        master_seed = load_master_seed()
        
        # Build sweep configuration
        config = SweepConfig(
            n_values=args.n_values,
            p_values=args.p_values,
            rho_values=args.rho_values,
            dist_types=args.dist_types
        )
        
        # Build full parameter sweep
        params_list = build_parameter_sweep(config, iterations, master_seed)
        
        # Write to CSV
        write_params_csv(params_list, args.out)
        
        logger.info("Parameter sweep completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required file: {e}")
        sys.exit(1)
    except HighDimensionalInstabilityError as e:
        logger.error(f"High-dimensional instability detected: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()