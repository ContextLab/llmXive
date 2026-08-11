import os
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path if needed, though typically run from root
# Ensure we can import config
sys.path.insert(0, str(Path(__file__).parent))

from config import get_path, ensure_dirs, get_all_band_names


def load_raw_features(psd_path: str, behavioral_path: str) -> pd.DataFrame:
    """
    Load EEG PSD and Behavioral metrics, join on participant_id.
    
    Args:
        psd_path: Path to data/interim/eeg_psd.csv
        behavioral_path: Path to data/interim/behavioral_metrics.csv
        
    Returns:
        Merged DataFrame with participant_id, band powers, and median_rt.
    """
    if not os.path.exists(psd_path):
        raise FileNotFoundError(f"Required PSD file not found: {psd_path}")
    if not os.path.exists(behavioral_path):
        raise FileNotFoundError(f"Required behavioral file not found: {behavioral_path}")
        
    df_psd = pd.read_csv(psd_path)
    df_beh = pd.read_csv(behavioral_path)
    
    # Ensure participant_id is consistent type (usually int or str)
    # Assuming both use 'participant_id' as the key
    required_cols_psd = ['participant_id'] + get_all_band_names()
    if not all(col in df_psd.columns for col in required_cols_psd):
        missing = set(required_cols_psd) - set(df_psd.columns)
        raise ValueError(f"PSD file missing columns: {missing}")
        
    required_cols_beh = ['participant_id', 'median_rt']
    if not all(col in df_beh.columns for col in required_cols_beh):
        missing = set(required_cols_beh) - set(df_beh.columns)
        raise ValueError(f"Behavioral file missing columns: {missing}")
        
    # Merge
    df = pd.merge(df_psd, df_beh[['participant_id', 'median_rt']], on='participant_id', how='inner')
    
    if df.empty:
        raise ValueError("No matching participants found between PSD and Behavioral datasets.")
        
    return df


def compute_relative_power(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute relative power for each band: band_power / total_power.
    Total power is the sum of all band powers.
    
    Args:
        df: DataFrame with absolute band powers.
        
    Returns:
        DataFrame with added columns for relative powers (e.g., rel_delta).
    """
    bands = get_all_band_names()
    df = df.copy()
    
    # Calculate total power per participant
    df['total_power'] = df[bands].sum(axis=1)
    
    # Avoid division by zero
    if (df['total_power'] == 0).any():
        raise ValueError("Zero total power detected for some participants. Check PSD data.")
        
    # Compute relative power
    for band in bands:
        rel_col = f'rel_{band}'
        df[rel_col] = df[band] / df['total_power']
        
    return df


def apply_clr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to relative power features.
    CLR(x) = ln(x / geometric_mean(x))
    
    This handles the compositional nature of relative power data.
    
    Args:
        df: DataFrame with relative power columns (rel_...).
        
    Returns:
        DataFrame with added CLR-transformed columns (clr_...).
    """
    bands = get_all_band_names()
    rel_cols = [f'rel_{b}' for b in bands]
    df = df.copy()
    
    # Check for zeros or negatives in relative power (should not happen with relative, but safe to check)
    if (df[rel_cols] <= 0).any().any():
        raise ValueError("Relative power contains zero or negative values. CLR transformation undefined.")
        
    # Compute geometric mean for each row
    # Geometric mean = exp(mean(log(x)))
    log_vals = np.log(df[rel_cols])
    geo_mean_log = log_vals.mean(axis=1)
    
    # CLR = log(x) - mean(log(x))
    # This is equivalent to log(x / geo_mean)
    for i, band in enumerate(bands):
        clr_col = f'clr_{band}'
        df[clr_col] = log_vals.iloc[:, i] - geo_mean_log
        
    return df


def validate_output(df: pd.DataFrame) -> bool:
    """
    Validate the output DataFrame has all required columns and no nulls.
    
    Args:
        df: Output DataFrame.
        
    Returns:
        True if valid.
        
    Raises:
        ValueError if validation fails.
    """
    bands = get_all_band_names()
    expected_rel = [f'rel_{b}' for b in bands]
    expected_clr = [f'clr_{b}' for b in bands]
    expected_cols = ['participant_id', 'median_rt', 'total_power'] + expected_rel + expected_clr
    
    missing = set(expected_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Output missing required columns: {missing}")
        
    if df.isnull().any().any():
        raise ValueError("Output contains null values.")
        
    return True


def main():
    """
    Main entry point for T015: Compute relative power and CLR transformation.
    Reads eeg_psd.csv and behavioral_metrics.csv, produces features.csv.
    """
    parser = argparse.ArgumentParser(description="T015: Compute relative power and CLR transformation")
    parser.add_argument('--psd-path', type=str, default=None, help="Path to eeg_psd.csv (default: data/interim/eeg_psd.csv)")
    parser.add_argument('--beh-path', type=str, default=None, help="Path to behavioral_metrics.csv (default: data/interim/behavioral_metrics.csv)")
    parser.add_argument('--output-path', type=str, default=None, help="Path to output features.csv (default: data/processed/features.csv)")
    
    args = parser.parse_args()
    
    # Resolve paths using config or defaults
    if args.psd_path is None:
        psd_path = get_path('interim', 'eeg_psd.csv')
    else:
        psd_path = args.psd_path
        
    if args.beh_path is None:
        beh_path = get_path('interim', 'behavioral_metrics.csv')
    else:
        beh_path = args.beh_path
        
    if args.output_path is None:
        out_path = get_path('processed', 'features.csv')
    else:
        out_path = args.output_path
        
    print(f"Loading data from: {psd_path}, {beh_path}")
    df = load_raw_features(psd_path, beh_path)
    
    print("Computing relative power...")
    df = compute_relative_power(df)
    
    print("Applying CLR transformation...")
    df = apply_clr_transformation(df)
    
    print("Validating output...")
    validate_output(df)
    
    # Ensure output directory exists
    ensure_dirs(out_path)
    
    print(f"Saving features to: {out_path}")
    df.to_csv(out_path, index=False)
    
    print(f"Successfully generated {out_path} with {len(df)} participants.")


if __name__ == "__main__":
    main()
