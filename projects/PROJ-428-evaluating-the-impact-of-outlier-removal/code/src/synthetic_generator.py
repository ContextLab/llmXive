import numpy as np
import pandas as pd
from pathlib import Path
import json
from typing import Dict, Any, Tuple
import os
import sys

# Ensure src is in path for imports if running as script
if 'code/src' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logger import get_logger
from src.setup_dirs import setup_directories

logger = get_logger(__name__)

# Global random seed configuration (Constitution Principle IV)
np.random.seed(42)

def generate_normal_distribution(n_samples: int, mean_range: Tuple[float, float], var_range: Tuple[float, float]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate a Normal distribution with random parameters.
    
    Args:
        n_samples: Number of samples to generate
        mean_range: Tuple (min, max) for random mean selection
        var_range: Tuple (min, max) for random variance selection
    
    Returns:
        Tuple of (DataFrame with 'value' column, ground truth params dict)
    """
    mean = np.random.uniform(*mean_range)
    std_dev = np.sqrt(np.random.uniform(*var_range))
    
    values = np.random.normal(loc=mean, scale=std_dev, size=n_samples)
    df = pd.DataFrame({'value': values})
    
    params = {
        'distribution': 'Normal',
        'n_samples': n_samples,
        'mean': float(mean),
        'std_dev': float(std_dev),
        'variance': float(std_dev ** 2)
    }
    
    logger.info(f"Generated Normal distribution: mean={mean:.4f}, var={params['variance']:.4f}")
    return df, params

def generate_lognormal_distribution(n_samples: int, mu_range: Tuple[float, float], sigma_range: Tuple[float, float]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate a LogNormal distribution with random parameters.
    Note: In numpy, lognormal takes mu and sigma of the underlying normal.
    
    Args:
        n_samples: Number of samples
        mu_range: Range for underlying normal mean
        sigma_range: Range for underlying normal std dev
    
    Returns:
        Tuple of (DataFrame, ground truth params)
    """
    mu = np.random.uniform(*mu_range)
    sigma = np.random.uniform(*sigma_range)
    
    values = np.random.lognormal(mean=mu, sigma=sigma, size=n_samples)
    df = pd.DataFrame({'value': values})
    
    # Calculate theoretical variance for LogNormal
    # Var = (exp(sigma^2) - 1) * exp(2*mu + sigma^2)
    variance = (np.exp(sigma**2) - 1) * np.exp(2*mu + sigma**2)
    
    params = {
        'distribution': 'LogNormal',
        'n_samples': n_samples,
        'mu': float(mu),
        'sigma': float(sigma),
        'variance': float(variance)
    }
    
    logger.info(f"Generated LogNormal distribution: mu={mu:.4f}, sigma={sigma:.4f}, var={variance:.4f}")
    return df, params

def generate_exponential_distribution(n_samples: int, scale_range: Tuple[float, float]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate an Exponential distribution.
    Scale parameter is 1/lambda. Variance = scale^2.
    
    Args:
        n_samples: Number of samples
        scale_range: Range for scale parameter
    
    Returns:
        Tuple of (DataFrame, ground truth params)
    """
    scale = np.random.uniform(*scale_range)
    
    values = np.random.exponential(scale=scale, size=n_samples)
    df = pd.DataFrame({'value': values})
    
    variance = scale ** 2
    
    params = {
        'distribution': 'Exponential',
        'n_samples': n_samples,
        'scale': float(scale),
        'variance': float(variance)
    }
    
    logger.info(f"Generated Exponential distribution: scale={scale:.4f}, var={variance:.4f}")
    return df, params

def generate_beta_distribution(n_samples: int, alpha_range: Tuple[float, float], beta_range: Tuple[float, float]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate a Beta distribution.
    
    Args:
        n_samples: Number of samples
        alpha_range: Range for alpha parameter
        beta_range: Range for beta parameter
    
    Returns:
        Tuple of (DataFrame, ground truth params)
    """
    alpha = np.random.uniform(*alpha_range)
    beta_param = np.random.uniform(*beta_range)
    
    values = np.random.beta(a=alpha, b=beta_param, size=n_samples)
    df = pd.DataFrame({'value': values})
    
    # Theoretical variance for Beta
    # Var = (alpha * beta) / ((alpha + beta)^2 * (alpha + beta + 1))
    variance = (alpha * beta_param) / ((alpha + beta_param)**2 * (alpha + beta_param + 1))
    
    params = {
        'distribution': 'Beta',
        'n_samples': n_samples,
        'alpha': float(alpha),
        'beta': float(beta_param),
        'variance': float(variance)
    }
    
    logger.info(f"Generated Beta distribution: alpha={alpha:.4f}, beta={beta_param:.4f}, var={variance:.4f}")
    return df, params

def generate_gamma_distribution(n_samples: int, shape_range: Tuple[float, float], scale_range: Tuple[float, float]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate a Gamma distribution.
    Variance = shape * scale^2.
    
    Args:
        n_samples: Number of samples
        shape_range: Range for shape (k) parameter
        scale_range: Range for scale (theta) parameter
    
    Returns:
        Tuple of (DataFrame, ground truth params)
    """
    shape = np.random.uniform(*shape_range)
    scale = np.random.uniform(*scale_range)
    
    values = np.random.gamma(shape=shape, scale=scale, size=n_samples)
    df = pd.DataFrame({'value': values})
    
    variance = shape * (scale ** 2)
    
    params = {
        'distribution': 'Gamma',
        'n_samples': n_samples,
        'shape': float(shape),
        'scale': float(scale),
        'variance': float(variance)
    }
    
    logger.info(f"Generated Gamma distribution: shape={shape:.4f}, scale={scale:.4f}, var={variance:.4f}")
    return df, params

def save_ground_truth_params(all_params: Dict[str, Dict[str, Any]], output_path: Path) -> None:
    """
    Save all ground truth parameters to a JSON file.
    
    Args:
        all_params: Dictionary of distribution name -> params dict
        output_path: Path to save the JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(all_params, f, indent=2)
    logger.info(f"Saved ground truth parameters to {output_path}")

def generate_and_save_distribution(
    generator_func,
    n_samples: int,
    param_ranges: Tuple,
    output_dir: Path,
    filename_prefix: str,
    distribution_name: str
) -> Dict[str, Any]:
    """
    Helper to generate data, save CSV, and return params.
    
    Args:
        generator_func: The generation function to call
        n_samples: Number of samples
        param_ranges: Arguments for the generator
        output_dir: Directory to save CSV
        filename_prefix: Prefix for CSV filename
        distribution_name: Name for the params key
    
    Returns:
        Ground truth params dict
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{filename_prefix}.csv"
    
    df, params = generator_func(n_samples, *param_ranges)
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved {distribution_name} data to {csv_path}")
    
    return params

def main():
    """
    Main entry point to generate all synthetic clean distributions.
    """
    # Setup directories
    setup_directories()
    
    # Configuration
    n_samples = 10000
    raw_dir = Path("data/raw")
    state_dir = Path("state")
    
    # Define parameter ranges for random generation
    # Normal: mean in [0, 10], variance in [1, 5]
    normal_params = ((0.0, 10.0), (1.0, 5.0))
    
    # LogNormal: mu in [0, 1], sigma in [0.5, 1.5]
    lognormal_params = ((0.0, 1.0), (0.5, 1.5))
    
    # Exponential: scale in [1, 3] (variance 1-9)
    exponential_params = ((1.0, 3.0),)
    
    # Beta: alpha in [2, 5], beta in [2, 5]
    beta_params = ((2.0, 5.0), (2.0, 5.0))
    
    # Gamma: shape in [2, 5], scale in [0.5, 2.0] (variance 0.5 - 20)
    gamma_params = ((2.0, 5.0), (0.5, 2.0))
    
    all_params = {}
    
    logger.info("Starting synthetic clean distribution generation...")
    
    # Generate Normal
    all_params['Normal'] = generate_and_save_distribution(
        generate_normal_distribution,
        n_samples, normal_params, raw_dir, 'synthetic_clean_normal', 'Normal'
    )
    
    # Generate LogNormal
    all_params['LogNormal'] = generate_and_save_distribution(
        generate_lognormal_distribution,
        n_samples, lognormal_params, raw_dir, 'synthetic_clean_lognormal', 'LogNormal'
    )
    
    # Generate Exponential
    all_params['Exponential'] = generate_and_save_distribution(
        generate_exponential_distribution,
        n_samples, exponential_params, raw_dir, 'synthetic_clean_exponential', 'Exponential'
    )
    
    # Generate Beta
    all_params['Beta'] = generate_and_save_distribution(
        generate_beta_distribution,
        n_samples, beta_params, raw_dir, 'synthetic_clean_beta', 'Beta'
    )
    
    # Generate Gamma
    all_params['Gamma'] = generate_and_save_distribution(
        generate_gamma_distribution,
        n_samples, gamma_params, raw_dir, 'synthetic_clean_gamma', 'Gamma'
    )
    
    # Save ground truth parameters
    params_path = state_dir / "synthetic_params.json"
    save_ground_truth_params(all_params, params_path)
    
    logger.info("Synthetic clean distribution generation complete.")
    logger.info(f"Ground truth parameters saved to {params_path}")

if __name__ == "__main__":
    main()
