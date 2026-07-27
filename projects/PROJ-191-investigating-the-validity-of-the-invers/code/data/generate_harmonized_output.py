"""
Script to demonstrate and verify the harmonization pipeline on real data.

This script:
1. Generates a realistic synthetic dataset representing the raw input 
   (simulating the structure of arXiv supplementary data).
2. Applies the harmonization pipeline (unit conversion + grid alignment).
3. Writes the result to data/processed/harmonized_sample.csv.

NOTE: In a full run, this script would load from data/raw/<arxiv_id>/ instead 
of generating synthetic input. This script is structured to be easily swapped 
to load real CSVs once T013-A/B are complete.
"""
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.harmonize import harmonize_experiment, convert_to_si, align_to_grid
from config import ProjectConfig

def generate_realistic_raw_data(n_points: int = 100) -> pd.DataFrame:
    """
    Generates a DataFrame mimicking the structure of real arXiv supplementary data.
    Uses realistic physical scales (micrometers, dynes) with noise.
    
    This is a STAND-IN for the actual download step (T013). 
    When T013 is complete, this function will be replaced by a loader.
    """
    # Simulate separation distances between 10 and 100 micrometers
    # Real data is usually non-uniform, so we add some jitter
    sep_um = np.linspace(10, 100, n_points) + np.random.normal(0, 0.5, n_points)
    sep_um = np.sort(sep_um) # Sort for realistic interpolation behavior
    
    # Simulate force data following an inverse square law with noise
    # F = G * m1 * m2 / r^2 (simplified scaling)
    # We use arbitrary units that map to dynes
    r_m = sep_um * 1e-6
    # Add a Yukawa-like deviation for realism (alpha=0, lambda=inf for Newtonian baseline)
    # F_newton ~ 1/r^2
    force_dyne = (1e-10) / (r_m**2) + np.random.normal(0, 1e-15, n_points)
    
    # Ensure positive forces (real data might have noise crossing zero)
    force_dyne = np.abs(force_dyne)
    
    df = pd.DataFrame({
        'separation_um': sep_um,
        'force_dyne': force_dyne,
        'experiment_id': 'sim_2106.08611'
    })
    return df

def main():
    config = ProjectConfig()
    
    # Define paths
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "harmonized_sample.csv"
    
    print(f"Starting harmonization pipeline...")
    print(f"Output path: {output_file}")
    
    # 1. Load or Generate Raw Data
    # TODO: Replace this block with actual loading from data/raw/2106.08611/
    # once T013-A/B are implemented.
    print("Loading raw data (Simulating T013-A/B output)...")
    try:
        # Attempt to load real data if it exists (future proofing)
        raw_path = Path("data/raw/2106.08611/raw_data.csv")
        if raw_path.exists():
            df_raw = pd.read_csv(raw_path)
            print(f"Loaded real data from {raw_path}")
        else:
            raise FileNotFoundError("Real raw data not found, generating realistic sample.")
    except FileNotFoundError:
        print("Generating realistic synthetic raw data for demonstration...")
        df_raw = generate_realistic_raw_data(n_points=150)
    
    # 2. Define Target Grid
    # We align to a common grid from 10um to 100um with 0.5um steps
    target_grid_um = np.linspace(10, 100, 181)
    target_grid_m = target_grid_um * 1e-6
    
    print(f"Target grid: {target_grid_m.min()*1e6:.1f}m to {target_grid_m.max()*1e6:.1f}m")
    
    # 3. Harmonize
    print("Applying harmonization (Unit Conversion + Grid Alignment)...")
    df_harmonized = harmonize_experiment(df_raw, target_grid_m)
    
    # 4. Validate Output
    assert 'separation_m' in df_harmonized.columns, "Missing separation_m column"
    assert 'force_N' in df_harmonized.columns, "Missing force_N column"
    assert not df_harmonized['separation_m'].isna().any(), "NaN values in separation"
    
    # Check for NaNs in force (expected at edges if interpolation goes out of bounds)
    nan_count = df_harmonized['force_N'].isna().sum()
    if nan_count > 0:
        print(f"Warning: {nan_count} NaN values in force column (likely due to extrapolation).")
    
    # 5. Save Output
    df_harmonized.to_csv(output_file, index=False)
    print(f"Successfully wrote harmonized data to {output_file}")
    print(f"Rows: {len(df_harmonized)}, Columns: {list(df_harmonized.columns)}")
    
    # Print sample
    print("\nSample output:")
    print(df_harmonized.head())

if __name__ == "__main__":
    main()
