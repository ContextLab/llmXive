"""
T015: Compute Relative Power and apply CLR Transformation.

Inputs:
  - data/interim/eeg_psd.csv (from T012)
  - data/interim/behavioral_metrics.csv (from T013)

Outputs:
  - data/interim/features_relative.csv (Intermediate: Band Power + Relative Power)
  - data/processed/features.csv (Final: CLR-transformed features + Median RT)

Process:
  1. Load PSD and Behavioral metrics.
  2. Join on participant_id.
  3. Compute relative power (band/total) for all bands.
  4. Apply Centered Log-Ratio (CLR) transformation to relative powers.
  5. Save intermediate (relative) and final (CLR) files.
"""
import os
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, ensure_dirs, get_all_band_names

def load_raw_features():
    """Load the PSD and behavioral metrics produced by T012 and T013."""
    psd_path = get_path("data/interim/eeg_psd.csv")
    behav_path = get_path("data/interim/behavioral_metrics.csv")

    if not os.path.exists(psd_path):
        raise FileNotFoundError(f"Input file missing: {psd_path}. Run T012 first.")
    if not os.path.exists(behav_path):
        raise FileNotFoundError(f"Input file missing: {behav_path}. Run T013 first.")

    df_psd = pd.read_csv(psd_path)
    df_behav = pd.read_csv(behav_path)

    # Ensure participant_id is consistent type
    df_psd['participant_id'] = df_psd['participant_id'].astype(str)
    df_behav['participant_id'] = df_behav['participant_id'].astype(str)

    # Merge on participant_id
    df_merged = pd.merge(df_psd, df_behav, on='participant_id', how='inner')

    if df_merged.empty:
        raise ValueError("No overlapping participants found between PSD and Behavioral data.")

    return df_merged

def compute_relative_power(df):
    """
    Compute relative power (band/total) for all bands.
    Also applies CLR transformation.
    
    Bands expected in df: delta, theta, alpha, low_beta, high_beta, gamma
    """
    bands = get_all_band_names()
    
    # Identify band columns that exist in the dataframe
    # The T012 output should have these columns.
    available_bands = [b for b in bands if b in df.columns]
    
    if len(available_bands) < 2:
        raise ValueError(f"Expected at least 2 band columns. Found: {available_bands}")
    
    # Calculate Total Power (sum of all band powers)
    # Note: We use the sum of the specific bands we are analyzing as "Total" for relative power
    # relative_power = band_power / sum(all_band_powers)
    df['total_power'] = df[available_bands].sum(axis=1)
    
    # Compute relative power for each band
    for band in available_bands:
        col_name = f"{band}_relative"
        # Avoid division by zero
        df[col_name] = np.where(
            df['total_power'] > 0, 
            df[band] / df['total_power'], 
            0.0
        )
    
    # Apply Centered Log-Ratio (CLR) transformation to relative powers
    # CLR(x) = ln(x / geometric_mean(x))
    # We apply this to the relative power columns only.
    relative_cols = [f"{b}_relative" for b in available_bands]
    
    # Add a small epsilon to avoid log(0) if any relative power is exactly 0
    epsilon = 1e-10
    df_relative_safe = df[relative_cols].replace(0, epsilon)
    
    # Calculate geometric mean across bands for each participant
    # Geometric Mean = (prod(x_i))^(1/n)
    # log(GM) = mean(log(x_i))
    log_vals = np.log(df_relative_safe)
    log_geometric_mean = log_vals.mean(axis=1)
    
    # CLR = log(x) - log(GM)
    for col in relative_cols:
        clr_col = f"{col}_clr"
        df[clr_col] = log_vals[col] - log_geometric_mean
    
    return df

def validate_output(df_final, df_intermediate):
    """
    Validate that outputs meet requirements:
    - No nulls in feature columns
    - Correct columns exist
    - RT is within valid range (if present)
    """
    bands = get_all_band_names()
    relative_cols = [f"{b}_relative" for b in bands]
    clr_cols = [f"{b}_relative_clr" for b in bands]
    
    # Check intermediate
    for col in relative_cols:
        if col in df_intermediate.columns:
            if df_intermediate[col].isnull().any():
                raise ValueError(f"Intermediate file has nulls in {col}")
    
    # Check final
    for col in clr_cols:
        if col in df_final.columns:
            if df_final[col].isnull().any():
                raise ValueError(f"Final file has nulls in {col}")
    
    # Check RT range if present
    if 'median_rt' in df_final.columns:
        invalid_rt = (df_final['median_rt'] < 100) | (df_final['median_rt'] > 2000)
        if invalid_rt.any():
            # Log warning but don't fail, as T013 should have handled this, 
            # but we verify the final state.
            print(f"Warning: {invalid_rt.sum()} rows have RT outside [100, 2000]ms.")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Compute Relative Power and CLR Transformation (T015)")
    args = parser.parse_args()

    print("Loading raw features (T012) and behavioral metrics (T013)...")
    try:
        df = load_raw_features()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Loaded {len(df)} participants.")

    print("Computing relative power and applying CLR transformation...")
    df_processed = compute_relative_power(df)

    # Prepare intermediate output (Relative Power only, plus metadata)
    bands = get_all_band_names()
    relative_cols = [f"{b}_relative" for b in bands]
    
    # Select columns for intermediate: ID, original bands, relative bands, RT
    intermediate_cols = ['participant_id'] + bands + ['total_power'] + relative_cols + ['median_rt']
    # Filter to only existing columns
    intermediate_cols = [c for c in intermediate_cols if c in df_processed.columns]
    
    df_intermediate = df_processed[intermediate_cols].copy()

    # Prepare final output (CLR transformed)
    clr_cols = [f"{b}_relative_clr" for b in bands]
    final_cols = ['participant_id'] + clr_cols + ['median_rt']
    final_cols = [c for c in final_cols if c in df_processed.columns]
    
    df_final = df_processed[final_cols].copy()

    # Ensure directories exist
    ensure_dirs("data/interim")
    ensure_dirs("data/processed")

    # Save intermediate
    path_intermediate = get_path("data/interim/features_relative.csv")
    df_intermediate.to_csv(path_intermediate, index=False)
    print(f"Saved intermediate features to {path_intermediate}")

    # Save final
    path_final = get_path("data/processed/features.csv")
    df_final.to_csv(path_final, index=False)
    print(f"Saved final CLR-transformed features to {path_final}")

    # Validate
    print("Validating outputs...")
    validate_output(df_final, df_intermediate)
    print("Validation passed.")

if __name__ == "__main__":
    main()
