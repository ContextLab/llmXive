"""
Utility to generate realistic raw data for testing and development.
This module is used to create synthetic but realistic data when real
arXiv data is not available or for rapid prototyping of the pipeline.
"""
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.harmonize import harmonize_experiment, convert_to_si, align_to_grid
from data.models import HarmonizedDataset
from config import get_logger

logger = get_logger("generate_harmonized_output")

def generate_realistic_raw_data(output_dir: str, n_runs: int = 3, n_points: int = 100):
    """
    Generate synthetic raw data files that mimic the structure of arXiv data.
    
    Args:
        output_dir: Directory to save the generated CSV files.
        n_runs: Number of independent experimental runs to generate.
        n_points: Number of data points per run.
    
    Returns:
        List of paths to the generated CSV files.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    # Generate a range of separations (micrometers)
    # Typical range for sub-millimeter experiments: 0.1 mm to 1 mm
    # Convert to micrometers for the "raw" data
    separations_um = np.linspace(100, 1000, n_points)
    
    for i in range(n_runs):
        # Add some noise and variation to each run
        noise_scale = 0.01 + 0.005 * i
        separations = separations_um + np.random.normal(0, 1, n_points)
        
        # Generate force data (in dynes)
        # Using an inverse square law as a base, with some noise
        # Force ~ 1/r^2
        # Scale factor to make values realistic (e.g., 1e-6 dynes)
        base_force = 1e-6 * (100 / separations) ** 2
        noise = np.random.normal(0, base_force * noise_scale, n_points)
        forces_dyne = base_force + noise
        
        # Ensure no negative forces
        forces_dyne = np.abs(forces_dyne)
        
        # Create DataFrame
        df = pd.DataFrame({
            'separation_um': separations,
            'force_dyne': forces_dyne,
            'uncertainty_dyne': np.abs(forces_dyne) * noise_scale
        })
        
        # Save to CSV
        filename = f"run_{i+1:03d}_data.csv"
        filepath = output_path / filename
        df.to_csv(filepath, index=False)
        generated_files.append(str(filepath))
        logger.info(f"Generated {filename} with {n_points} points.")
    
    return generated_files

def main():
    """Main entry point for generating test data."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate realistic raw data for testing.")
    parser.add_argument("--output-dir", type=str, default="data/raw/synthetic",
                        help="Directory to save generated data.")
    parser.add_argument("--n-runs", type=int, default=3, help="Number of runs to generate.")
    parser.add_argument("--n-points", type=int, default=100, help="Points per run.")
    
    args = parser.parse_args()
    
    files = generate_realistic_raw_data(args.output_dir, args.n_runs, args.n_points)
    print(f"Generated {len(files)} files in {args.output_dir}")

if __name__ == "__main__":
    main()