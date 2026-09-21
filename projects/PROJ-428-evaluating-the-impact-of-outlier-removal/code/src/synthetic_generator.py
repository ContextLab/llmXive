"""
Synthetic Data Generator Module

Generates synthetic clean distributions (Normal, LogNormal, Exponential, Beta, Gamma)
with known variance parameters, saving data to CSV and ground truth parameters to JSON.
"""
import numpy as np
import pandas as pd
from pathlib import Path
import json
from typing import Dict, Any, Tuple, List, Optional
import os

# Ensure reproducibility
np.random.seed(42)

def generate_normal_distribution(n_samples: int, mean: float, std: float, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate a Normal (Gaussian) distribution.

    Args:
        n_samples: Number of samples to generate.
        mean: Mean of the distribution.
        std: Standard deviation of the distribution.
        seed: Optional seed for reproducibility.

    Returns:
        Tuple of (data array, ground truth parameters dict).
    """
    if seed is not None:
        np.random.seed(seed)
    data = np.random.normal(loc=mean, scale=std, size=n_samples)
    params = {
        "distribution": "Normal",
        "n_samples": n_samples,
        "true_mean": mean,
        "true_std": std,
        "true_variance": std ** 2
    }
    return data, params

def generate_lognormal_distribution(n_samples: int, mu: float, sigma: float, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate a LogNormal distribution.

    Args:
        n_samples: Number of samples to generate.
        mu: Mean of the underlying normal distribution.
        sigma: Standard deviation of the underlying normal distribution.
        seed: Optional seed for reproducibility.

    Returns:
        Tuple of (data array, ground truth parameters dict).
    """
    if seed is not None:
        np.random.seed(seed)
    # LogNormal parameters: mean of log(X) = mu, std of log(X) = sigma
    # Variance of LogNormal = (exp(sigma^2) - 1) * exp(2*mu + sigma^2)
    data = np.random.lognormal(mean=mu, sigma=sigma, size=n_samples)
    true_variance = (np.exp(sigma**2) - 1) * np.exp(2*mu + sigma**2)
    params = {
        "distribution": "LogNormal",
        "n_samples": n_samples,
        "true_mu": mu,
        "true_sigma": sigma,
        "true_variance": true_variance
    }
    return data, params

def generate_exponential_distribution(n_samples: int, scale: float, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate an Exponential distribution.

    Args:
        n_samples: Number of samples to generate.
        scale: Scale parameter (1/lambda).
        seed: Optional seed for reproducibility.

    Returns:
        Tuple of (data array, ground truth parameters dict).
    """
    if seed is not None:
        np.random.seed(seed)
    # Exponential variance = scale^2
    data = np.random.exponential(scale=scale, size=n_samples)
    params = {
        "distribution": "Exponential",
        "n_samples": n_samples,
        "true_scale": scale,
        "true_variance": scale ** 2
    }
    return data, params

def generate_beta_distribution(n_samples: int, alpha: float, beta: float, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate a Beta distribution.

    Args:
        n_samples: Number of samples to generate.
        alpha: Alpha parameter (shape).
        beta: Beta parameter (shape).
        seed: Optional seed for reproducibility.

    Returns:
        Tuple of (data array, ground truth parameters dict).
    """
    if seed is not None:
        np.random.seed(seed)
    # Beta variance = (alpha * beta) / ((alpha + beta)^2 * (alpha + beta + 1))
    data = np.random.beta(a=alpha, b=beta, size=n_samples)
    true_variance = (alpha * beta) / ((alpha + beta)**2 * (alpha + beta + 1))
    params = {
        "distribution": "Beta",
        "n_samples": n_samples,
        "true_alpha": alpha,
        "true_beta": beta,
        "true_variance": true_variance
    }
    return data, params

def generate_gamma_distribution(n_samples: int, shape: float, scale: float, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate a Gamma distribution.

    Args:
        n_samples: Number of samples to generate.
        shape: Shape parameter (k).
        scale: Scale parameter (theta).
        seed: Optional seed for reproducibility.

    Returns:
        Tuple of (data array, ground truth parameters dict).
    """
    if seed is not None:
        np.random.seed(seed)
    # Gamma variance = shape * scale^2
    data = np.random.gamma(shape=shape, scale=scale, size=n_samples)
    params = {
        "distribution": "Gamma",
        "n_samples": n_samples,
        "true_shape": shape,
        "true_scale": scale,
        "true_variance": shape * (scale ** 2)
    }
    return data, params

def save_ground_truth_params(params_list: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save ground truth parameters to a JSON file.

    Args:
        params_list: List of parameter dictionaries.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(params_list, f, indent=2)

def generate_and_save_distribution(
    generator_func,
    n_samples: int,
    output_csv_path: Path,
    param_args: Dict[str, Any],
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a distribution, save to CSV, and return ground truth params.

    Args:
        generator_func: The generator function to call.
        n_samples: Number of samples.
        output_csv_path: Path to save the CSV file.
        param_args: Arguments for the generator function (excluding n_samples and seed).
        seed: Optional seed for reproducibility.

    Returns:
        Ground truth parameters dictionary.
    """
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    data, params = generator_func(n_samples=n_samples, seed=seed, **param_args)
    
    # Create DataFrame
    df = pd.DataFrame({
        "value": data,
        "distribution": params["distribution"]
    })
    
    # Save to CSV
    df.to_csv(output_csv_path, index=False)
    
    return params

def main():
    """
    Main function to generate all synthetic clean distributions.
    """
    # Define project root relative to this file
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    
    # Define output paths
    data_raw_dir = project_root / "data" / "raw"
    state_dir = project_root / "state"
    
    # Ensure directories exist
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuration for distributions
    # We generate parameters within defined ranges to ensure variance is non-trivial
    distributions_config = [
        {
            "name": "Normal",
            "func": generate_normal_distribution,
            "args": {"mean": 50.0, "std": 10.0},
            "filename": "synthetic_clean_normal.csv"
        },
        {
            "name": "LogNormal",
            "func": generate_lognormal_distribution,
            "args": {"mu": 0.0, "sigma": 0.5},
            "filename": "synthetic_clean_lognormal.csv"
        },
        {
            "name": "Exponential",
            "func": generate_exponential_distribution,
            "args": {"scale": 2.0},
            "filename": "synthetic_clean_exponential.csv"
        },
        {
            "name": "Beta",
            "func": generate_beta_distribution,
            "args": {"alpha": 2.0, "beta": 5.0},
            "filename": "synthetic_clean_beta.csv"
        },
        {
            "name": "Gamma",
            "func": generate_gamma_distribution,
            "args": {"shape": 3.0, "scale": 2.0},
            "filename": "synthetic_clean_gamma.csv"
        }
    ]
    
    n_samples = 10000  # Large enough for stable variance estimates
    all_params = []
    
    for config in distributions_config:
        output_path = data_raw_dir / config["filename"]
        params = generate_and_save_distribution(
            generator_func=config["func"],
            n_samples=n_samples,
            output_csv_path=output_path,
            param_args=config["args"],
            seed=42  # Fixed seed for reproducibility across distributions
        )
        all_params.append(params)
        print(f"Generated {config['name']} distribution: {output_path}")
    
    # Save ground truth parameters
    params_output_path = state_dir / "synthetic_params.json"
    save_ground_truth_params(all_params, params_output_path)
    print(f"Saved ground truth parameters to {params_output_path}")

if __name__ == "__main__":
    main()
