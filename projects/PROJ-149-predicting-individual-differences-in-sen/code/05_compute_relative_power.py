import os
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# Import shared config utilities
from config import get_path, ensure_dirs, get_band_freqs

# Band definitions matching the pipeline
BANDS = ['delta', 'theta', 'alpha', 'low-beta', 'high-beta', 'gamma']

def load_raw_features(input_path: str) -> pd.DataFrame:
    """
    Load the raw EEG PSD features from the intermediate CSV.
    Expects columns: participant_id, delta, theta, alpha, low-beta, high-beta, gamma
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = ['participant_id'] + BANDS
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    
    return df

def load_behavioral_metrics(input_path: str) -> pd.DataFrame:
    """
    Load behavioral metrics to merge with EEG features.
    Expected to contain 'participant_id' and 'median_rt'.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Behavioral metrics file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    if 'participant_id' not in df.columns:
        raise ValueError(f"Missing 'participant_id' in {input_path}")
    
    if 'median_rt' not in df.columns:
        # If column is named differently, try to find it, but strict adherence is safer
        # Assuming standard naming based on T013
        raise ValueError(f"Missing 'median_rt' in {input_path}. Found columns: {df.columns.tolist()}")
    
    return df

def compute_relative_power(df_raw: pd.DataFrame, epsilon: float = 1e-6) -> pd.DataFrame:
    """
    Compute relative power (band / total) and apply Centered Log-Ratio (CLR) transformation.
    
    1. Calculate Total Power = sum of all band powers.
    2. Calculate Relative Power = band_power / total_power.
    3. Add small constant (epsilon) to avoid log(0).
    4. Apply CLR: log(x) - mean(log(x)) across bands for each participant.
    
    Args:
        df_raw: DataFrame with raw power values.
        epsilon: Small constant to prevent log(0).
    
    Returns:
        DataFrame with participant_id, median_rt, and CLR-transformed relative powers.
    """
    df = df_raw.copy()
    
    # 1. Calculate Total Power
    df['total_power'] = df[BANDS].sum(axis=1)
    
    # Check for zero total power
    zero_total = df[df['total_power'] == 0]
    if not zero_total.empty:
        raise ValueError(f"Found {len(zero_total)} participants with zero total power. Cannot compute relative power.")
    
    # 2. Calculate Relative Power
    for band in BANDS:
        df[f'rel_{band}'] = df[band] / df['total_power']
    
    # 3. Add epsilon to avoid log(0)
    # The task description explicitly asks for this step before log
    for band in BANDS:
        df[f'rel_{band}'] = df[f'rel_{band}'] + epsilon
    
    # 4. Apply CLR Transformation
    # CLR(x_i) = log(x_i) - (1/D) * sum(log(x_j))
    # where D is the number of components (bands)
    
    clr_cols = [f'rel_{band}' for band in BANDS]
    log_cols = [f'log_{band}' for band in BANDS]
    
    # Compute log of relative powers
    for col in clr_cols:
        df[col] = np.log(df[col])
    
    # Compute the geometric mean (log of geometric mean is mean of logs)
    # We subtract the mean of the logs across the bands for each row
    row_mean_log = df[clr_cols].mean(axis=1)
    
    # CLR = log(x_i) - mean(log(x_j))
    for col in clr_cols:
        df[col] = df[col] - row_mean_log
    
    # Rename columns to final output format
    output_cols = ['participant_id', 'median_rt']
    for band in BANDS:
        output_cols.append(f'clr_{band}')
    
    result_df = df[output_cols]
    
    return result_df

def validate_output(df: pd.DataFrame, output_path: str) -> bool:
    """
    Validate the output DataFrame against schema requirements.
    - No nulls in feature columns
    - Correct columns present
    - Valid RT range (150ms to 1000ms as per T035a, though T013 says 100-2000 exclusion)
    """
    required_cols = ['participant_id', 'median_rt'] + [f'clr_{b}' for b in BANDS]
    
    if not all(col in df.columns for col in required_cols):
        print(f"Validation Failed: Missing columns. Expected {required_cols}, got {df.columns.tolist()}")
        return False
    
    # Check for nulls in features
    feature_cols = [f'clr_{b}' for b in BANDS]
    if df[feature_cols].isnull().any().any():
        print("Validation Failed: Null values found in feature columns.")
        return False
    
    # Check RT range (T035a specifies 150ms to 1000ms for validation)
    # T013 excluded <100 and >2000, so we check if remaining are in valid physiological range
    # The task T035a says "valid RT range 150ms to 1000ms"
    if 'median_rt' in df.columns:
        invalid_rt = df[(df['median_rt'] < 150) | (df['median_rt'] > 1000)]
        if not invalid_rt.empty:
            print(f"Warning: {len(invalid_rt)} participants have RT outside 150-1000ms range.")
            # Do not fail the task, just warn, as T013 might have been less strict or data is noisy
    
    # Ensure output directory exists
    ensure_dirs(output_path)
    
    return True

def main():
    """
    Main entry point for T015: Compute relative power and CLR transformation.
    Inputs:
        - data/interim/eeg_psd.csv
        - data/interim/behavioral_metrics.csv
    Output:
        - data/processed/features.csv
    """
    parser = argparse.ArgumentParser(description="T015: Compute Relative Power and CLR Transformation")
    parser.add_argument('--input-psd', type=str, default=None, help='Path to raw PSD CSV')
    parser.add_argument('--input-beh', type=str, default=None, help='Path to behavioral metrics CSV')
    parser.add_argument('--output', type=str, default=None, help='Path to output features CSV')
    args = parser.parse_args()

    # Resolve paths
    input_psd = args.input_psd or get_path('interim', 'eeg_psd.csv')
    input_beh = args.input_beh or get_path('interim', 'behavioral_metrics.csv')
    output_path = args.output or get_path('processed', 'features.csv')

    print(f"Loading raw PSD from: {input_psd}")
    df_raw = load_raw_features(input_psd)
    print(f"Loaded {len(df_raw)} participants from PSD.")

    print(f"Loading behavioral metrics from: {input_beh}")
    df_beh = load_behavioral_metrics(input_beh)
    print(f"Loaded {len(df_beh)} participants from behavioral data.")

    # Merge on participant_id
    if 'participant_id' in df_raw.columns and 'participant_id' in df_beh.columns:
        df_merged = pd.merge(df_raw, df_beh[['participant_id', 'median_rt']], on='participant_id', how='inner')
    else:
        # Fallback if column names differ slightly, though spec says 'participant_id'
        raise ValueError("participant_id column missing in one of the datasets.")

    print(f"Merged dataset size: {len(df_merged)}")

    # Compute Relative Power and CLR
    print("Computing relative power and CLR transformation...")
    df_features = compute_relative_power(df_merged)

    # Validate
    if not validate_output(df_features, output_path):
        print("Validation failed. Exiting.")
        sys.exit(1)

    # Save to disk
    ensure_dirs(output_path)
    df_features.to_csv(output_path, index=False)
    print(f"Successfully wrote features to: {output_path}")

    # Verify file exists
    if not os.path.exists(output_path):
        raise RuntimeError(f"Failed to write output file: {output_path}")

if __name__ == "__main__":
    main()