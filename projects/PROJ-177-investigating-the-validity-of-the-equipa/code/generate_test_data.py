"""
Generate synthetic test datasets for pipeline verification.
These are labeled with 'test_' prefix and are NOT used as primary scientific input.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import sys


def load_params(params_path: str = "artifacts/test_params.json") -> dict:
    """Load test parameters from JSON file."""
    with open(params_path, 'r') as f:
        return json.load(f)


def generate_thermal_data(params: dict, n_samples: int = 1000, seed: int = 42) -> pd.DataFrame:
    """
    Generate Maxwell-Boltzmann distributed thermal data.
    """
    np.random.seed(seed)
    mean = params['thermal']['mean']
    scale = params['thermal']['scale']

    # Generate velocities from Maxwell-Boltzmann distribution
    # v ~ sqrt(x^2 + y^2 + z^2) where x,y,z ~ N(0, scale)
    vx = np.random.normal(0, scale, n_samples)
    vy = np.random.normal(0, scale, n_samples)
    vz = np.random.normal(0, scale, n_samples)
    v = np.sqrt(vx**2 + vy**2 + vz**2)

    # Create DataFrame with required columns
    df = pd.DataFrame({
        'particle_id': range(n_samples),
        'timestamp': np.arange(n_samples),
        'x': np.cumsum(vx),
        'y': np.cumsum(vy),
        'z': np.cumsum(vz),
        'v': v,
        'omega': np.random.normal(0, scale/2, n_samples),
        'material_type': 'steel'
    })

    return df


def generate_nonthermal_data(params: dict, n_samples: int = 1000, seed: int = 42) -> pd.DataFrame:
    """
    Generate Pareto distributed non-thermal data.
    """
    np.random.seed(seed)
    shape = params['nonthermal']['shape']

    # Generate velocities from Pareto distribution (non-thermal)
    v = np.random.pareto(shape, n_samples) + 1  # +1 to shift from 0

    # Create DataFrame with required columns
    df = pd.DataFrame({
        'particle_id': range(n_samples),
        'timestamp': np.arange(n_samples),
        'x': np.cumsum(v),
        'y': np.cumsum(np.zeros(n_samples)),
        'z': np.cumsum(np.zeros(n_samples)),
        'v': v,
        'omega': np.random.pareto(shape/2, n_samples) + 1,
        'material_type': 'polymer'
    })

    return df


def main():
    """Main entry point for test data generation."""
    parser = argparse.ArgumentParser(description="Generate synthetic test datasets")
    parser.add_argument('--params', type=str, default='artifacts/test_params.json', help='Path to test parameters')
    parser.add_argument('--n-samples', type=int, default=1000, help='Number of samples per dataset')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    # Load parameters
    params = load_params(args.params)

    # Create derived directory
    derived_dir = Path("data/derived")
    derived_dir.mkdir(exist_ok=True)

    # Generate thermal data
    thermal_df = generate_thermal_data(params, n_samples=args.n_samples, seed=args.seed)
    thermal_path = derived_dir / "test_thermal_data.csv"
    thermal_df.to_csv(thermal_path, index=False)
    print(f"Thermal data written to: {thermal_path}")

    # Generate non-thermal data
    nonthermal_df = generate_nonthermal_data(params, n_samples=args.n_samples, seed=args.seed)
    nonthermal_path = derived_dir / "test_nonthermal_data.csv"
    nonthermal_df.to_csv(nonthermal_path, index=False)
    print(f"Non-thermal data written to: {nonthermal_path}")


if __name__ == "__main__":
    main()
