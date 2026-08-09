"""
Generate synthetic test datasets for pipeline validation.
Uses parameters from T020a (artifacts/test_params.json).
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import sys

def load_params(params_path: str) -> dict:
    """Load test parameters from JSON file."""
    path = Path(params_path)
    if not path.exists():
        raise FileNotFoundError(f"Parameters file not found: {params_path}")
    with open(path, 'r') as f:
        return json.load(f)

def generate_thermal_data(params: dict, n_samples: int = 1000, seed: int = 42) -> pd.DataFrame:
    """
    Generate thermal data following Maxwell-Boltzmann distribution.
    
    Args:
        params: Dictionary containing 'maxwell_boltzmann' parameters
        n_samples: Number of samples to generate
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with thermal energy data
    """
    np.random.seed(seed)
    mb_params = params.get('maxwell_boltzmann', {})
    mean = mb_params.get('mean', 1.0)
    scale = mb_params.get('scale', 0.1)
    
    # Generate velocities from Maxwell-Boltzmann distribution
    # Using numpy's random.gamma as an approximation for MB distribution
    # MB distribution: f(v) ~ v^2 * exp(-mv^2 / 2kT)
    # We use a scaled chi distribution with 3 degrees of freedom
    # or equivalently, a gamma distribution for energy
    
    # For simplicity and reproducibility, generate energy directly
    # E ~ Gamma(k=3/2, theta=scale) for 3D Maxwell-Boltzmann
    # Mean of Gamma(k, theta) = k*theta, so we adjust
    k = 1.5  # degrees of freedom / 2
    theta = mean / k  # scale parameter to achieve desired mean
    
    energies = np.random.gamma(shape=k, scale=theta, size=n_samples)
    velocities = np.sqrt(2 * energies)  # Assuming mass=1 for simplicity
    
    # Create DataFrame with required columns for ingestion
    data = {
        'particle_id': [f'P{i:04d}' for i in range(n_samples)],
        'timestamp': np.arange(n_samples) * 0.001,  # 1ms time steps
        'x': np.cumsum(velocities * np.random.randn(n_samples) * 0.01),
        'y': np.cumsum(velocities * np.random.randn(n_samples) * 0.01),
        'z': np.cumsum(velocities * np.random.randn(n_samples) * 0.01),
        'vx': velocities * np.random.randn(n_samples),
        'vy': velocities * np.random.randn(n_samples),
        'vz': velocities * np.random.randn(n_samples),
        'omega_x': np.random.randn(n_samples) * 0.1,
        'omega_y': np.random.randn(n_samples) * 0.1,
        'omega_z': np.random.randn(namples) * 0.1,
        'energy': energies,
        'material_type': 'steel',
        'driving_frequency': 10.0
    }
    
    return pd.DataFrame(data)

def generate_nonthermal_data(params: dict, n_samples: int = 1000, seed: int = 43) -> pd.DataFrame:
    """
    Generate non-thermal data following Pareto distribution (driven granular).
    
    Args:
        params: Dictionary containing 'pareto' parameters
        n_samples: Number of samples to generate
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with non-thermal energy data
    """
    np.random.seed(seed)
    pareto_params = params.get('pareto', {})
    shape = pareto_params.get('shape', 2.0)
    
    # Generate energies from Pareto distribution
    # Pareto: f(x) = alpha * x_m^alpha / x^(alpha+1) for x >= x_m
    # We shift and scale to get reasonable values
    x_m = 0.5  # minimum value
    raw_energies = np.random.pareto(a=shape, size=n_samples) * x_m + x_m
    
    # Normalize to have similar mean to thermal data for comparison
    # but with heavier tails
    target_mean = 1.0
    current_mean = np.mean(raw_energies)
    energies = raw_energies * (target_mean / current_mean)
    
    # Create DataFrame with required columns
    # Non-thermal systems often have bursty, intermittent behavior
    # We simulate this by having clusters of high-energy events
    timestamps = np.cumsum(np.random.exponential(0.001, n_samples))
    particle_ids = []
    vx_list = []
    vy_list = []
    vz_list = []
    
    for i in range(n_samples):
        # Simulate intermittent driving
        if np.random.random() < 0.1:  # 10% chance of driving event
            boost = np.random.uniform(2.0, 5.0)
        else:
            boost = 1.0
        
        particle_ids.append(f'P{i:04d}')
        v_mag = np.sqrt(2 * energies[i] / boost)
        angle = np.random.uniform(0, 2 * np.pi)
        vx_list.append(v_mag * np.cos(angle) * boost)
        vy_list.append(v_mag * np.sin(angle) * boost)
        vz_list.append(np.random.randn() * v_mag * 0.1)  # Small z-component
    
    data = {
        'particle_id': particle_ids,
        'timestamp': timestamps,
        'x': np.cumsum(np.array(vx_list) * 0.001),
        'y': np.cumsum(np.array(vy_list) * 0.001),
        'z': np.cumsum(np.array(vz_list) * 0.001),
        'vx': vx_list,
        'vy': vy_list,
        'vz': vz_list,
        'omega_x': np.random.randn(n_samples) * 0.1 * energies,  # Coupled to energy
        'omega_y': np.random.randn(n_samples) * 0.1 * energies,
        'omega_z': np.random.randn(n_samples) * 0.1 * energies,
        'energy': energies,
        'material_type': 'polymer',
        'driving_frequency': 15.0
    }
    
    return pd.DataFrame(data)

def main():
    """Main entry point for test data generation."""
    parser = argparse.ArgumentParser(
        description='Generate synthetic test datasets for pipeline validation'
    )
    parser.add_argument(
        '--params',
        type=str,
        default='artifacts/test_params.json',
        help='Path to parameters JSON file (default: artifacts/test_params.json)'
    )
    parser.add_argument(
        '--n-samples',
        type=int,
        default=1000,
        help='Number of samples per dataset (default: 1000)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/derived',
        help='Output directory for generated files (default: data/derived)'
    )
    parser.add_argument(
        '--seed-thermal',
        type=int,
        default=42,
        help='Random seed for thermal data (default: 42)'
    )
    parser.add_argument(
        '--seed-nonthermal',
        type=int,
        default=43,
        help='Random seed for non-thermal data (default: 43)'
    )
    
    args = parser.parse_args()
    
    # Load parameters
    try:
        params = load_params(args.params)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Please run T020a first to generate artifacts/test_params.json")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate thermal data
    print(f"Generating thermal data with {args.n_samples} samples...")
    thermal_df = generate_thermal_data(
        params, 
        n_samples=args.n_samples, 
        seed=args.seed_thermal
    )
    thermal_path = output_dir / 'test_thermal_data.csv'
    thermal_df.to_csv(thermal_path, index=False)
    print(f"Written: {thermal_path}")
    
    # Generate non-thermal data
    print(f"Generating non-thermal data with {args.n_samples} samples...")
    nonthermal_df = generate_nonthermal_data(
        params, 
        n_samples=args.n_samples, 
        seed=args.seed_nonthermal
    )
    nonthermal_path = output_dir / 'test_nonthermal_data.csv'
    nonthermal_df.to_csv(nonthermal_path, index=False)
    print(f"Written: {nonthermal_path}")
    
    # Summary
    print("\nGenerated datasets:")
    print(f"  - Thermal (Maxwell-Boltzmann): {thermal_path} ({len(thermal_df)} rows)")
    print(f"  - Non-thermal (Pareto): {nonthermal_path} ({len(nonthermal_df)} rows)")
    print("\nNote: Files prefixed with 'test_' are for validation only.")

if __name__ == '__main__':
    main()
