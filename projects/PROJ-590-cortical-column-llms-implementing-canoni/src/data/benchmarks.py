"""
Synthetic function generation module for benchmarking cortical column LLMs.

Generates deterministic synthetic datasets for:
- Lorenz attractor (chaotic time series)
- Fourier series (periodic functions)
- Polynomial surfaces (multivariate regression)

All generators use deterministic seeding for reproducibility.
"""

import numpy as np
from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass
import json
import os


@dataclass
class DatasetConfig:
    """Configuration for synthetic dataset generation."""
    seed: int
    n_samples: int
    n_features: int
    noise_level: float = 0.0
    output_dir: str = "data"
    filename_prefix: str = "synthetic"


def set_deterministic_seed(seed: int) -> None:
    """Set global random seed for reproducibility."""
    np.random.seed(seed)


def generate_lorenz_attractor(
    seed: int,
    n_steps: int,
    dt: float = 0.01,
    sigma: float = 10.0,
    rho: float = 28.0,
    beta: float = 8.0/3.0,
    noise_level: float = 0.0,
    initial_state: Optional[Tuple[float, float, float]] = None
) -> np.ndarray:
    """
    Generate Lorenz attractor time series.

    Args:
        seed: Random seed for reproducibility
        n_steps: Number of time steps to simulate
        dt: Time step size
        sigma, rho, beta: Lorenz system parameters
        noise_level: Standard deviation of Gaussian noise to add
        initial_state: Starting (x, y, z) or None for default

    Returns:
        Array of shape (n_steps, 3) containing (x, y, z) trajectories
    """
    np.random.seed(seed)

    if initial_state is None:
        x, y, z = 1.0, 1.0, 1.0
    else:
        x, y, z = initial_state

    trajectory = np.zeros((n_steps, 3), dtype=np.float64)

    for i in range(n_steps):
        # Store current state
        trajectory[i] = [x, y, z]

        # Compute derivatives using Euler method
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z

        # Update state
        x += dx * dt
        y += dy * dt
        z += dz * dt

    # Add noise if requested
    if noise_level > 0:
        noise = np.random.normal(0, noise_level, trajectory.shape)
        trajectory += noise

    return trajectory


def generate_fourier_series(
    seed: int,
    n_samples: int,
  n_frequencies: int = 5,
    domain: Tuple[float, float] = (0, 2 * np.pi),
    noise_level: float = 0.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate Fourier series function samples.

    Args:
        seed: Random seed for reproducibility
        n_samples: Number of x points to sample
        n_frequencies: Number of frequency components
        domain: (min, max) of x domain
        noise_level: Standard deviation of Gaussian noise

    Returns:
        Tuple of (x_values, y_values) each of shape (n_samples,)
    """
    np.random.seed(seed)

    x = np.linspace(domain[0], domain[1], n_samples)

    # Generate random Fourier coefficients
    a_coeffs = np.random.randn(n_frequencies)
    b_coeffs = np.random.randn(n_frequencies)
    frequencies = np.arange(1, n_frequencies + 1)

    y = np.zeros(n_samples)
    for i, freq in enumerate(frequencies):
        y += a_coeffs[i] * np.cos(freq * x)
        y += b_coeffs[i] * np.sin(freq * x)

    # Add noise if requested
    if noise_level > 0:
        noise = np.random.normal(0, noise_level, n_samples)
        y += noise

    return x, y


def generate_polynomial_surface(
    seed: int,
    n_samples: int,
    degree: int = 2,
    n_features: int = 2,
    noise_level: float = 0.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate polynomial surface regression data.

    Args:
        seed: Random seed for reproducibility
        n_samples: Number of data points
        degree: Maximum polynomial degree
        n_features: Number of input features
        noise_level: Standard deviation of Gaussian noise

    Returns:
        Tuple of (X, y) where X is (n_samples, n_features) and y is (n_samples,)
    """
    np.random.seed(seed)

    # Generate random input features
    X = np.random.randn(n_samples, n_features)

    # Generate random polynomial coefficients
    # For degree d and n features, number of terms is roughly (n+d)!/(n!d!)
    # We'll use a simpler approach: generate coefficients for all monomials up to degree
    n_terms = 0
    for d in range(degree + 1):
        # Number of combinations with replacement
        from math import comb
        n_terms += comb(n_features + d - 1, d) if d > 0 else 1

    coefficients = np.random.randn(n_terms)

    # Compute polynomial features
    y = np.zeros(n_samples)
    coef_idx = 0

    for d in range(degree + 1):
        if d == 0:
            y += coefficients[coef_idx]
            coef_idx += 1
        else:
            # Generate all monomials of degree d
            from itertools import combinations_with_replacement
            for combo in combinations_with_replacement(range(n_features), d):
                term = np.ones(n_samples)
                for feature_idx in combo:
                    term *= X[:, feature_idx]
                y += coefficients[coef_idx] * term
                coef_idx += 1

    # Add noise if requested
    if noise_level > 0:
        noise = np.random.normal(0, noise_level, n_samples)
        y += noise

    return X, y


def save_dataset(
    data: Dict[str, Any],
    config: DatasetConfig,
    dataset_type: str
) -> str:
    """
    Save synthetic dataset to disk in NPZ format.

    Args:
        data: Dictionary containing dataset arrays
        config: Dataset configuration
        dataset_type: Type of dataset (lorenz, fourier, polynomial)

    Returns:
        Path to saved file
    """
    os.makedirs(config.output_dir, exist_ok=True)

    filename = f"{config.filename_prefix}_{dataset_type}_seed{config.seed}.npz"
    filepath = os.path.join(config.output_dir, filename)

    # Save data
    np.savez(filepath, **data)

    # Save metadata
    metadata = {
        "dataset_type": dataset_type,
        "seed": config.seed,
        "n_samples": config.n_samples,
        "n_features": config.n_features,
        "noise_level": config.noise_level,
        "timestamp": None  # Will be set by caller if needed
    }

    metadata_path = filepath.replace(".npz", "_meta.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    return filepath


def load_dataset(filepath: str) -> Dict[str, Any]:
    """
    Load synthetic dataset from disk.

    Args:
        filepath: Path to .npz file

    Returns:
        Dictionary containing dataset arrays
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found: {filepath}")

    data = np.load(filepath, allow_pickle=True)
    return {key: data[key] for key in data.files}


def generate_synthetic_dataset(
    dataset_type: str,
    seed: int,
    n_samples: int,
    n_features: int = 2,
    noise_level: float = 0.0,
    output_dir: str = "data",
    filename_prefix: str = "synthetic"
) -> str:
    """
    Generate and save a synthetic dataset.

    Args:
        dataset_type: One of 'lorenz', 'fourier', 'polynomial'
        seed: Random seed for reproducibility
        n_samples: Number of samples
        n_features: Number of features (for polynomial)
        noise_level: Noise standard deviation
        output_dir: Directory to save output
        filename_prefix: Prefix for output filename

    Returns:
        Path to saved dataset file

    Raises:
        ValueError: If dataset_type is not recognized
    """
    config = DatasetConfig(
        seed=seed,
        n_samples=n_samples,
        n_features=n_features,
        noise_level=noise_level,
        output_dir=output_dir,
        filename_prefix=filename_prefix
    )

    if dataset_type == "lorenz":
        trajectory = generate_lorenz_attractor(
            seed=seed,
            n_steps=n_samples,
            noise_level=noise_level
        )
        data = {"trajectory": trajectory}
        return save_dataset(data, config, "lorenz")

    elif dataset_type == "fourier":
        x, y = generate_fourier_series(
            seed=seed,
            n_samples=n_samples,
            noise_level=noise_level
        )
        data = {"x": x, "y": y}
        return save_dataset(data, config, "fourier")

    elif dataset_type == "polynomial":
        X, y = generate_polynomial_surface(
            seed=seed,
            n_samples=n_samples,
            n_features=n_features,
            noise_level=noise_level
        )
        data = {"X": X, "y": y}
        return save_dataset(data, config, "polynomial")

    else:
        raise ValueError(f"Unknown dataset type: {dataset_type}. "
                       f"Supported: lorenz, fourier, polynomial")


def main():
    """Main entry point for generating benchmark datasets."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate synthetic benchmark datasets for cortical column LLMs"
    )
    parser.add_argument(
        "--type",
        choices=["lorenz", "fourier", "polynomial"],
        required=True,
        help="Type of dataset to generate"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=1000,
        help="Number of samples to generate"
    )
    parser.add_argument(
        "--n-features",
        type=int,
        default=2,
        help="Number of features (for polynomial datasets)"
    )
    parser.add_argument(
        "--noise",
        type=float,
        default=0.0,
        help="Noise level (standard deviation)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Output directory"
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="synthetic",
        help="Filename prefix"
    )

    args = parser.parse_args()

    filepath = generate_synthetic_dataset(
        dataset_type=args.type,
        seed=args.seed,
        n_samples=args.n_samples,
        n_features=args.n_features,
        noise_level=args.noise,
        output_dir=args.output_dir,
        filename_prefix=args.prefix
    )

    print(f"Generated dataset: {filepath}")

    # Verify file exists and can be loaded
    data = load_dataset(filepath)
    print(f"Dataset keys: {list(data.keys())}")
    for key, value in data.items():
        print(f"  {key}: shape={value.shape}, dtype={value.dtype}")


if __name__ == "__main__":
    main()
