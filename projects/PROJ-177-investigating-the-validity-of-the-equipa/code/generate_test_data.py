"""
Generate synthetic test datasets for pipeline validation.

This module creates two types of test data:
1. Thermal data: Maxwell-Boltzmann distribution (simulating equilibrium)
2. Non-thermal data: Pareto distribution (simulating driven granular systems)

These files are prefixed with 'test_' and are explicitly NOT used as
primary scientific input. They serve only for pipeline validation and
testing statistical methods.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import sys
import logging

# Configure logging to avoid file handler issues in test generation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_params(params_path: str = "artifacts/test_params.json") -> dict:
    """Load test parameters from JSON file.

    Args:
        params_path: Path to the parameters JSON file.

    Returns:
        Dictionary containing test parameters.

    Raises:
        FileNotFoundError: If the parameters file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(params_path)
    if not path.exists():
        raise FileNotFoundError(f"Parameters file not found: {params_path}")

    with open(path, 'r') as f:
        params = json.load(f)

    logger.info(f"Loaded parameters from {params_path}")
    return params

def generate_thermal_data(params: dict, n_samples: int = 10000, seed: int = 42) -> pd.DataFrame:
    """Generate Maxwell-Boltzmann distributed thermal data.

    Args:
        params: Dictionary containing 'maxwell_boltzmann' parameters (mean, scale).
        n_samples: Number of samples to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: particle_id, timestamp, energy_value, distribution_type
    """
    np.random.seed(seed)

    mb_params = params.get('maxwell_boltzmann', {'mean': 1.0, 'scale': 0.1})
    mean = mb_params['mean']
    scale = mb_params['scale']

    # Generate Maxwell-Boltzmann distributed energy values
    # Using chi distribution scaled to approximate MB for 3 DOF
    # E ~ scale * chi^2(k=3/2) or similar approximation
    # For simplicity and test purposes, we use a scaled chi distribution
    # which approximates the MB distribution shape
    dof = 3
    # Maxwell-Boltzmann for speed: f(v) ~ v^2 * exp(-mv^2/2kT)
    # Energy E = 1/2 mv^2, so we sample from chi distribution
    energies = np.random.chisquare(df=dof, size=n_samples) * (mean / dof) * scale

    # Create DataFrame
    df = pd.DataFrame({
        'particle_id': np.repeat(np.arange(n_samples // 10), 10),
        'timestamp': np.tile(np.arange(10), n_samples // 10).astype(float),
        'energy_value': energies,
        'distribution_type': 'maxwell_boltzmann'
    })

    logger.info(f"Generated {n_samples} thermal samples (Maxwell-Boltzmann)")
    return df

def generate_nonthermal_data(params: dict, n_samples: int = 10000, seed: int = 42) -> pd.DataFrame:
    """Generate Pareto distributed non-thermal data.

    Args:
        params: Dictionary containing 'pareto' parameters (shape).
        n_samples: Number of samples to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: particle_id, timestamp, energy_value, distribution_type
    """
    np.random.seed(seed)

    pareto_params = params.get('pareto', {'shape': 2.0})
    shape = pareto_params['shape']

    # Generate Pareto distributed energy values
    # Pareto distribution: f(x) = alpha * x_m^alpha / x^(alpha+1) for x >= x_m
    # We use x_m = 1.0 as the minimum scale
    x_m = 1.0
    energies = x_m * np.random.pareto(a=shape, size=n_samples)

    # Create DataFrame
    df = pd.DataFrame({
        'particle_id': np.repeat(np.arange(n_samples // 10), 10),
        'timestamp': np.tile(np.arange(10), n_samples // 10).astype(float),
        'energy_value': energies,
        'distribution_type': 'pareto'
    })

    logger.info(f"Generated {n_samples} non-thermal samples (Pareto)")
    return df

def main():
    """Main entry point for test data generation."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic test datasets for pipeline validation."
    )
    parser.add_argument(
        "--params",
        type=str,
        default="artifacts/test_params.json",
        help="Path to test parameters JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/derived",
        help="Output directory for generated data files"
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=10000,
        help="Number of samples to generate per dataset"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load parameters
    try:
        params = load_params(args.params)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load parameters: {e}")
        sys.exit(1)

    # Generate thermal data
    thermal_file = output_dir / "test_thermal_data.csv"
    thermal_df = generate_thermal_data(params, n_samples=args.n_samples, seed=args.seed)
    thermal_df.to_csv(thermal_file, index=False)
    logger.info(f"Thermal data saved to: {thermal_file}")

    # Generate non-thermal data
    nonthermal_file = output_dir / "test_nonthermal_data.csv"
    nonthermal_df = generate_nonthermal_data(params, n_samples=args.n_samples, seed=args.seed)
    nonthermal_df.to_csv(nonthermal_file, index=False)
    logger.info(f"Non-thermal data saved to: {nonthermal_file}")

    logger.info("Test data generation complete.")

if __name__ == "__main__":
    main()
