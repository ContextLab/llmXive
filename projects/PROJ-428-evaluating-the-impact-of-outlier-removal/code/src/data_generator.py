import numpy as np
import pandas as pd
from pathlib import Path
import json
from typing import Dict, Any, Tuple, List, Optional
import os
import logging
from src.logger import get_logger
from src.setup_dirs import setup_directories

# Global random seed as per project requirements
RANDOM_SEED = 42

def _setup_logging():
    """Setup logger for data generation module."""
    return get_logger(__name__)

def generate_normal_distribution(n_samples: int, mean: float, std: float, seed: Optional[int] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate a Normal (Gaussian) distribution with known parameters.
    
    Args:
        n_samples: Number of samples to generate
        mean: Mean of the distribution
        std: Standard deviation of the distribution
        seed: Random seed for reproducibility (optional)
        
    Returns:
        Tuple of (DataFrame with 'value' column, dict of ground truth params)
    """
    if seed is not None:
        np.random.seed(seed)
    else:
        np.random.seed(RANDOM_SEED)
        
    values = np.random.normal(loc=mean, scale=std, size=n_samples)
    df = pd.DataFrame({'value': values})
    
    params = {
        'distribution': 'normal',
        'n_samples': n_samples,
        'mean': mean,
        'std': std,
        'variance': std ** 2,
        'seed': seed if seed is not None else RANDOM_SEED
    }
    
    return df, params

def generate_lognormal_distribution(n_samples: int, mu: float, sigma: float, seed: Optional[int] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate a LogNormal distribution with known parameters.
    Note: mu and sigma are parameters of the underlying normal distribution.
    
    Args:
        n_samples: Number of samples to generate
        mu: Mean of the underlying normal distribution
        sigma: Standard deviation of the underlying normal distribution
        seed: Random seed for reproducibility (optional)
        
    Returns:
        Tuple of (DataFrame with 'value' column, dict of ground truth params)
    """
    if seed is not None:
        np.random.seed(seed)
    else:
        np.random.seed(RANDOM_SEED)
        
    values = np.random.lognormal(mean=mu, sigma=sigma, size=n_samples)
    df = pd.DataFrame({'value': values})
    
    # Calculate theoretical variance for lognormal: (exp(sigma^2) - 1) * exp(2*mu + sigma^2)
    theoretical_variance = (np.exp(sigma**2) - 1) * np.exp(2*mu + sigma**2)
    
    params = {
        'distribution': 'lognormal',
        'n_samples': n_samples,
        'mu': mu,
        'sigma': sigma,
        'theoretical_variance': theoretical_variance,
        'seed': seed if seed is not None else RANDOM_SEED
    }
    
    return df, params

def generate_exponential_distribution(n_samples: int, scale: float, seed: Optional[int] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate an Exponential distribution with known scale parameter.
    Note: scale = 1/lambda where lambda is the rate parameter.
    
    Args:
        n_samples: Number of samples to generate
        scale: Scale parameter (1/lambda)
        seed: Random seed for reproducibility (optional)
        
    Returns:
        Tuple of (DataFrame with 'value' column, dict of ground truth params)
    """
    if seed is not None:
        np.random.seed(seed)
    else:
        np.random.seed(RANDOM_SEED)
        
    values = np.random.exponential(scale=scale, size=n_samples)
    df = pd.DataFrame({'value': values})
    
    # Theoretical variance for exponential: scale^2
    theoretical_variance = scale ** 2
    
    params = {
        'distribution': 'exponential',
        'n_samples': n_samples,
        'scale': scale,
        'theoretical_variance': theoretical_variance,
        'seed': seed if seed is not None else RANDOM_SEED
    }
    
    return df, params

def generate_beta_distribution(n_samples: int, alpha: float, beta: float, seed: Optional[int] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate a Beta distribution with known shape parameters.
    
    Args:
        n_samples: Number of samples to generate
        alpha: First shape parameter (must be > 0)
        beta: Second shape parameter (must be > 0)
        seed: Random seed for reproducibility (optional)
        
    Returns:
        Tuple of (DataFrame with 'value' column, dict of ground truth params)
    """
    if seed is not None:
        np.random.seed(seed)
    else:
        np.random.seed(RANDOM_SEED)
        
    values = np.random.beta(a=alpha, b=beta, size=n_samples)
    df = pd.DataFrame({'value': values})
    
    # Theoretical variance for beta: (alpha * beta) / ((alpha + beta)^2 * (alpha + beta + 1))
    theoretical_variance = (alpha * beta) / ((alpha + beta)**2 * (alpha + beta + 1))
    
    params = {
        'distribution': 'beta',
        'n_samples': n_samples,
        'alpha': alpha,
        'beta': beta,
        'theoretical_variance': theoretical_variance,
        'seed': seed if seed is not None else RANDOM_SEED
    }
    
    return df, params

def generate_gamma_distribution(n_samples: int, shape: float, scale: float, seed: Optional[int] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate a Gamma distribution with known shape and scale parameters.
    Note: In numpy, gamma(shape, scale) where scale = 1/rate.
    
    Args:
        n_samples: Number of samples to generate
        shape: Shape parameter (k or alpha)
        scale: Scale parameter (theta = 1/rate)
        seed: Random seed for reproducibility (optional)
        
    Returns:
        Tuple of (DataFrame with 'value' column, dict of ground truth params)
    """
    if seed is not None:
        np.random.seed(seed)
    else:
        np.random.seed(RANDOM_SEED)
        
    values = np.random.gamma(shape=shape, scale=scale, size=n_samples)
    df = pd.DataFrame({'value': values})
    
    # Theoretical variance for gamma: shape * scale^2
    theoretical_variance = shape * (scale ** 2)
    
    params = {
        'distribution': 'gamma',
        'n_samples': n_samples,
        'shape': shape,
        'scale': scale,
        'theoretical_variance': theoretical_variance,
        'seed': seed if seed is not None else RANDOM_SEED
    }
    
    return df, params

def save_ground_truth_params(params_list: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save ground truth parameters to a JSON file.
    
    Args:
        params_list: List of parameter dictionaries to save
        output_path: Path to the output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(params_list, f, indent=2)
        
    logging.info(f"Ground truth parameters saved to {output_path}")

def generate_and_save_distribution(
    generator_func,
    n_samples: int,
    output_filename: str,
    params: Dict[str, Any],
    data_dir: Path
) -> None:
    """
    Generate a distribution and save it to CSV along with ground truth parameters.
    
    Args:
        generator_func: Function to generate the distribution (e.g., generate_normal_distribution)
        n_samples: Number of samples to generate
        output_filename: Name of the output CSV file (without path)
        params: Dictionary of parameters to pass to the generator function
        data_dir: Directory where the output CSV will be saved
    """
    logger = _setup_logging()
    
    # Generate the data
    df, ground_truth_params = generator_func(n_samples=n_samples, **params)
    
    # Save the data
    output_path = data_dir / output_filename
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} samples to {output_path}")
    
    return ground_truth_params

def main():
    """
    Main function to generate all synthetic clean distributions and save them.
    Outputs:
        - data/raw/synthetic_clean_normal.csv
        - data/raw/synthetic_clean_lognormal.csv
        - data/raw/synthetic_clean_exponential.csv
        - data/raw/synthetic_clean_beta.csv
        - data/raw/synthetic_clean_gamma.csv
        - state/synthetic_params.json
    """
    logger = _setup_logging()
    logger.info("Starting synthetic data generation for User Story 1")
    
    # Setup directories
    setup_directories()
    
    # Define output paths
    data_raw_dir = Path("data/raw")
    state_dir = Path("state")
    
    # Ensure directories exist
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Define distributions and their parameters
    distributions = [
        {
            'name': 'normal',
            'func': generate_normal_distribution,
            'params': {'mean': 10.0, 'std': 2.0},
            'filename': 'synthetic_clean_normal.csv',
            'n_samples': 1000
        },
        {
            'name': 'lognormal',
            'func': generate_lognormal_distribution,
            'params': {'mu': 2.0, 'sigma': 0.5},
            'filename': 'synthetic_clean_lognormal.csv',
            'n_samples': 1000
        },
        {
            'name': 'exponential',
            'func': generate_exponential_distribution,
            'params': {'scale': 1.0},
            'filename': 'synthetic_clean_exponential.csv',
            'n_samples': 1000
        },
        {
            'name': 'beta',
            'func': generate_beta_distribution,
            'params': {'alpha': 2.0, 'beta': 5.0},
            'filename': 'synthetic_clean_beta.csv',
            'n_samples': 1000
        },
        {
            'name': 'gamma',
            'func': generate_gamma_distribution,
            'params': {'shape': 3.0, 'scale': 2.0},
            'filename': 'synthetic_clean_gamma.csv',
            'n_samples': 1000
        }
    ]
    
    all_params = []
    
    for dist in distributions:
        logger.info(f"Generating {dist['name']} distribution...")
        try:
            ground_truth_params = generate_and_save_distribution(
                generator_func=dist['func'],
                n_samples=dist['n_samples'],
                output_filename=dist['filename'],
                params=dist['params'],
                data_dir=data_raw_dir
            )
            all_params.append(ground_truth_params)
            logger.info(f"Successfully generated {dist['name']} distribution")
        except Exception as e:
            logger.error(f"Failed to generate {dist['name']} distribution: {str(e)}")
            raise
    
    # Save all ground truth parameters
    params_output_path = state_dir / "synthetic_params.json"
    save_ground_truth_params(all_params, params_output_path)
    logger.info(f"All ground truth parameters saved to {params_output_path}")
    
    logger.info("Synthetic data generation completed successfully")
    
    return all_params

if __name__ == "__main__":
    main()
