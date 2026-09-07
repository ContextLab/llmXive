"""
Data generation module for high-dimensional p-value validity assessment.

Implements parameter sweep logic to generate synthetic datasets with controlled
correlation structures and distributional properties.
"""
import numpy as np
import json
import hashlib
import os
import logging
import argparse
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Iterator, Callable
from dataclasses import dataclass, asdict

from utils.simulation import RNGWrapper, SimulationConfig, SyntheticDataset
from utils.regularization import regularize_covariance, is_condition_number_acceptable, HighDimensionalInstabilityError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SweepConfig:
    """Configuration for the parameter sweep."""
    n_values: List[int]
    p_values: List[int]
    rho_values: List[float]
    distribution_types: List[str]
    required_iterations: int
    seed_start: int

def load_required_iterations() -> int:
    """
    Load required_iterations from power analysis result or use default.
    
    Returns:
        int: The number of iterations required for the sweep.
    """
    power_analysis_path = Path("data/sweep/power_analysis_result.json")
    
    if power_analysis_path.exists():
        try:
            with open(power_analysis_path, 'r') as f:
                data = json.load(f)
                required_iterations = data.get('required_iterations', 1000)
                logger.info(f"Loaded required_iterations: {required_iterations} from power analysis result.")
                return required_iterations
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse power analysis result: {e}. Using default 1000.")
    
    logger.info("Power analysis result not found or invalid. Using default required_iterations = 1000.")
    return 1000

def generate_correlated_data(
    n: int,
    p: int,
    rho: float,
    rng: np.random.Generator
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a covariance matrix with specified correlation structure.
    
    Args:
        n: Number of samples.
        p: Number of features.
        rho: Correlation coefficient for the AR(1) structure.
        rng: Random number generator.
        
    Returns:
        Tuple of (data matrix, covariance matrix).
    """
    if p / n > 10:
        raise HighDimensionalInstabilityError(f"p/n ratio ({p/n}) exceeds threshold of 10.")
    
    # Create AR(1) correlation matrix
    cov = np.full((p, p), rho ** np.abs(np.arange(p)[:, None] - np.arange(p)))
    
    # Ensure positive definiteness
    cov = regularize_covariance(cov)
    
    # Check condition number
    if not is_condition_number_acceptable(cov):
        raise HighDimensionalInstabilityError(f"Covariance matrix condition number too high after regularization.")
    
    # Generate multivariate normal data
    mean = np.zeros(p)
    data = rng.multivariate_normal(mean, cov, size=n)
    
    return data, cov

def generate_distribution_violations(
    data: np.ndarray,
    distribution_type: str,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Transform data to violate normality assumptions.
    
    Args:
        data: Base multivariate normal data.
        distribution_type: Type of distribution violation ('t-dist', 'skew_normal', 'normal').
        rng: Random number generator.
        
    Returns:
        Transformed data matrix.
    """
    if distribution_type == 'normal':
        return data
    
    n, p = data.shape
    
    if distribution_type == 't-dist':
        # Heavy-tailed distribution (t-distribution with low df)
        df = 3.0
        # Standardize then apply t-distribution
        data_standardized = (data - data.mean(axis=0)) / (data.std(axis=0) + 1e-8)
        t_samples = rng.standard_t(df, size=(n, p))
        # Scale to match variance approximately
        scale = np.sqrt(df / (df - 2)) if df > 2 else 1.0
        return t_samples * scale
    
    elif distribution_type == 'skew_normal':
        # Skewed distribution
        # Using a simple skew transformation
        alpha = 5.0  # Skewness parameter
        data_standardized = (data - data.mean(axis=0)) / (data.std(axis=0) + 1e-8)
        # Apply skew-normal transformation: X = alpha * |Z| + Z where Z ~ N(0,1)
        # Simplified: use skewnorm from scipy if available, otherwise approximate
        try:
            from scipy.stats import skewnorm
            samples = skewnorm.rvs(a=alpha, size=(n, p), random_state=rng.integers(0, 2**31-1))
            return samples
        except ImportError:
            # Fallback approximation
            z = rng.standard_normal((n, p))
            return alpha * np.abs(z) + z
    
    else:
        raise ValueError(f"Unknown distribution type: {distribution_type}")

def write_dataset_metadata(
    params: Dict[str, Any],
    seed: int,
    output_path: Path
) -> None:
    """
    Write metadata for a generated dataset.
    
    Args:
        params: Parameter dictionary.
        seed: Random seed used.
        output_path: Path to write metadata JSON.
    """
    # Serialize params with sorted keys for deterministic hashing
    param_str = json.dumps(params, sort_keys=True)
    sha256_hash = hashlib.sha256(param_str.encode()).hexdigest()
    
    metadata = {
        'seed': seed,
        'sha256': sha256_hash,
        **params
    }
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Wrote metadata to {output_path} with hash {sha256_hash}")

def build_parameter_sweep(
    n_values: List[int],
    p_values: List[int],
    rho_values: List[float],
    distribution_types: List[str],
    required_iterations: int,
    seed_start: int
) -> SweepConfig:
    """
    Build the parameter sweep configuration.
    
    Args:
        n_values: List of n values.
        p_values: List of p values.
        rho_values: List of rho values.
        distribution_types: List of distribution types.
        required_iterations: Number of iterations per parameter combination.
        seed_start: Starting seed.
        
    Returns:
        SweepConfig object.
    """
    return SweepConfig(
        n_values=n_values,
        p_values=p_values,
        rho_values=rho_values,
        distribution_types=distribution_types,
        required_iterations=required_iterations,
        seed_start=seed_start
    )

def streaming_data_generator(
    params_csv_path: Path,
    callback: Callable[[np.ndarray, Dict], bool]
) -> None:
    """
    Streaming data generator that reads parameters from CSV and yields data.
    
    Args:
        params_csv_path: Path to the parameters CSV file.
        callback: Function to call with (data, params). 
                 If callback returns False, generation stops.
                
    Raises:
        HighDimensionalInstabilityError: If p/n > 10 or covariance is near-singular.
    """
    with open(params_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            n = int(row['n'])
            p = int(row['p'])
            rho = float(row['rho'])
            distribution_type = row['distribution_type']
            seed = int(row['seed'])
            iteration = int(row['iteration'])
            
            # Check p/n ratio before generation
            if p / n > 10:
                raise HighDimensionalInstabilityError(
                    f"p/n ratio ({p/n}) exceeds threshold of 10 for n={n}, p={p}."
                )
            
            # Initialize RNG with specific seed
            rng = np.random.default_rng(seed)
            
            try:
                # Generate correlated data
                data, cov = generate_correlated_data(n, p, rho, rng)
                
                # Apply distribution violations
                data = generate_distribution_violations(data, distribution_type, rng)
                
                # Call callback with data and params
                params = {
                    'n': n,
                    'p': p,
                    'rho': rho,
                    'distribution_type': distribution_type,
                    'seed': seed,
                    'iteration': iteration
                }
                
                if not callback(data, params):
                    logger.info("Callback requested stop. Stopping generation.")
                    break
                    
            except HighDimensionalInstabilityError:
                raise
            except Exception as e:
                logger.error(f"Error generating data for seed {seed}: {e}")
                raise

def main():
    """
    Main entry point for parameter sweep generation.
    
    Generates data for the full Cartesian product of parameters and writes
    params.csv to data/sweep/params.csv.
    """
    parser = argparse.ArgumentParser(description='Generate parameter sweep CSV')
    parser.add_argument('--out', type=str, default='data/sweep/params.csv',
                      help='Output path for params.csv')
    parser.add_argument('--n-values', type=int, nargs='+', default=[50, 100, 200, 500],
                      help='List of n values')
    parser.add_argument('--p-values', type=int, nargs='+', default=[500, 1000, 2000, 5000],
                      help='List of p values')
    parser.add_argument('--rho-values', type=float, nargs='+', default=[0, 0.1, 0.3, 0.5, 0.7, 0.9],
                      help='List of rho values')
    parser.add_argument('--dist-types', type=str, nargs='+', 
                      default=['Normal', 't-dist', 'Skewed Normal'],
                      help='List of distribution types')
    args = parser.parse_args()
    
    logger.info("Starting parameter sweep generation...")
    
    # Load required iterations
    required_iterations = load_required_iterations()
    logger.info(f"Using required_iterations: {required_iterations}")
    
    # Define parameter sets
    n_values = args.n_values
    p_values = args.p_values
    rho_values = args.rho_values
    distribution_types = args.dist_types
    
    # Create output directory
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read master seed
    master_seed_path = Path('data/sweep/master_seed.txt')
    if master_seed_path.exists():
        with open(master_seed_path, 'r') as f:
            seed_start = int(f.read().strip())
    else:
        seed_start = 42
        master_seed_path.parent.mkdir(parents=True, exist_ok=True)
        with open(master_seed_path, 'w') as f:
            f.write(str(seed_start))
    logger.info(f"Starting seed: {seed_start}")
    
    # Generate full Cartesian product
    seeds = []
    current_seed = seed_start
    
    # Ensure we have enough seeds
    total_combinations = len(n_values) * len(p_values) * len(rho_values) * len(distribution_types)
    total_rows = total_combinations * required_iterations
    
    logger.info(f"Total parameter combinations: {total_combinations}")
    logger.info(f"Required iterations per combination: {required_iterations}")
    logger.info(f"Total rows to generate: {total_rows}")
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['seed', 'n', 'p', 'rho', 'distribution_type', 'iteration'])
        
        for n in n_values:
            for p in p_values:
                for rho in rho_values:
                    for dist_type in distribution_types:
                        for i in range(required_iterations):
                            writer.writerow([
                                current_seed,
                                n,
                                p,
                                rho,
                                dist_type,
                                i
                            ])
                            seeds.append(current_seed)
                            current_seed += 1
    
    logger.info(f"Generated {len(seeds)} parameter rows to {output_path}")
    
    # Update master seed for next run
    with open(master_seed_path, 'w') as f:
        f.write(str(current_seed))
        
    logger.info("Parameter sweep generation complete.")

if __name__ == '__main__':
    main()