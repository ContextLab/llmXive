"""
T015: Compute relative power for all bands.

Consume `data/processed/features_raw.csv` (output of T012/T013 merge)
and produce `data/processed/features.csv` with relative band powers.

Relative Power = Band Power / Total Power
where Total Power = Sum of (Delta + Theta + Alpha + LowBeta + HighBeta + Gamma)

This controls for total power confound (FR-010).
"""
import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, get_all_band_names, get_band_freqs


def load_raw_features(input_path: str) -> pd.DataFrame:
    """
    Load the raw features CSV containing absolute band powers.
    
    Args:
        input_path: Path to features_raw.csv
        
    Returns:
        DataFrame with participant_id and absolute band power columns.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T012 (feature extraction) and T013 (behavioral parsing) have completed."
        )
    
    df = pd.read_csv(input_path)
    
    required_cols = ['participant_id']
    band_names = get_all_band_names()
    for band in band_names:
        # The column name in features_raw.csv is expected to be <band>_power
        col_name = f"{band}_power"
        if col_name not in df.columns:
            raise ValueError(
                f"Missing required column '{col_name}' in {input_path}. "
                f"Available columns: {list(df.columns)}"
            )
        required_cols.append(col_name)
    
    # Check if behavioral metrics (median_rt) are present (from T013 merge)
    if 'median_rt' in df.columns:
        required_cols.append('median_rt')
        
    return df[required_cols]


def compute_relative_power(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate relative power for each band.
    
    Relative Power = Absolute Band Power / Total Power
    Total Power = Sum of all band powers (Delta, Theta, Alpha, LowBeta, HighBeta, Gamma)
    
    Args:
        df: DataFrame with absolute band power columns.
        
    Returns:
        DataFrame with original columns plus relative power columns.
    """
    band_names = get_all_band_names()
    power_cols = [f"{band}_power" for band in band_names]
    
    # Calculate total power
    df['total_power'] = df[power_cols].sum(axis=1)
    
    # Handle zero total power to avoid division by zero
    # If total_power is 0, relative power is undefined (set to NaN)
    # This should not happen with real EEG data, but we handle it defensively
    relative_power_cols = {}
    for band in band_names:
        col_name = f"{band}_power"
        rel_col_name = f"{band}_relative_power"
        
        # Compute relative power
        relative_power_cols[rel_col_name] = df[col_name] / df['total_power']
        
    # Add relative power columns to dataframe
    for col_name, values in relative_power_cols.items():
        df[col_name] = values
        
    # Drop the temporary total_power column if it's not needed in output
    # (Keep it for debugging/verification, but FR-010 specifically asks for relative)
    # We will keep it as it's useful for validation.
    
    return df


def validate_output(df: pd.DataFrame) -> bool:
    """
    Validate the output DataFrame.
    
    Checks:
    1. No nulls in relative power columns
    2. Relative power values are between 0 and 1
    3. Sum of relative powers is approximately 1.0
    
    Args:
        df: Output DataFrame.
        
    Returns:
        True if validation passes, False otherwise.
    """
    band_names = get_all_band_names()
    rel_cols = [f"{band}_relative_power" for band in band_names]
    
    # Check for nulls
    if df[rel_cols].isnull().any().any():
        print("Validation Failed: Null values found in relative power columns.")
        return False
        
    # Check range [0, 1]
    for col in rel_cols:
        if (df[col] < 0).any() or (df[col] > 1).any():
            print(f"Validation Failed: Values out of range [0, 1] in {col}")
            return False
            
    # Check sum approx 1.0
    sum_rel = df[rel_cols].sum(axis=1)
    if not np.allclose(sum_rel, 1.0, atol=1e-6):
        print(f"Validation Failed: Sum of relative powers is not ~1.0. Min: {sum_rel.min()}, Max: {sum_rel.max()}")
        return False
        
    print("Validation Passed: All checks successful.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Compute relative band power from raw features.")
    parser.add_argument(
        "--input", 
        type=str, 
        default=None,
        help="Path to input features_raw.csv. Defaults to data/processed/features_raw.csv"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None,
        help="Path to output features.csv. Defaults to data/processed/features.csv"
    )
    args = parser.parse_args()
    
    # Determine paths
    input_path = args.input or str(get_path("processed", "features_raw.csv"))
    output_path = args.output or str(get_path("processed", "features.csv"))
    
    print(f"Loading raw features from: {input_path}")
    df = load_raw_features(input_path)
    print(f"Loaded {len(df)} participants.")
    
    print("Computing relative power...")
    df_relative = compute_relative_power(df)
    
    print("Validating output...")
    if not validate_output(df_relative):
        print("Error: Validation failed. Aborting.")
        sys.exit(1)
        
    # Save output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_relative.to_csv(output_path, index=False)
    print(f"Successfully saved relative power features to: {output_path}")
    
    # Print summary
    band_names = get_all_band_names()
    print("\nSummary of Relative Power (Mean):")
    for band in band_names:
        col = f"{band}_relative_power"
        print(f"  {band}: {df_relative[col].mean():.4f} (+/- {df_relative[col].std():.4f})")


if __name__ == "__main__":
    main()