"""
T015: Implement relative power calculation and Centered Log-Ratio (CLR) transformation.

This script:
1. Loads raw EEG PSD features (data/interim/eeg_psd.csv)
2. Loads behavioral metrics (data/interim/behavioral_metrics.csv)
3. Calculates relative power (band / total_power)
4. Applies CLR transformation to handle compositional data constraints
5. Merges with behavioral data
6. Outputs data/processed/features_clr.csv

Inputs:
- data/interim/eeg_psd.csv (from T012)
- data/interim/behavioral_metrics.csv (from T013)

Output:
- data/processed/features_clr.csv (CLR-transformed relative power + RT)
"""
import os
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, ensure_dirs, get_band_freqs, get_all_band_names
from utils.eeg_helpers import reject_channels_by_variance

# Define the bands we expect in the input PSD file
BAND_COLUMNS = ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']

def load_raw_features(input_path: str) -> pd.DataFrame:
    """
    Load raw EEG PSD features from CSV.
    
    Args:
        input_path: Path to eeg_psd.csv
        
    Returns:
        DataFrame with participant_id and band power columns
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = ['participant_id'] + BAND_COLUMNS
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
        
    return df[['participant_id'] + BAND_COLUMNS]

def load_behavioral_metrics(input_path: str) -> pd.DataFrame:
    """
    Load behavioral metrics (median RT) from CSV.
    
    Args:
        input_path: Path to behavioral_metrics.csv
        
    Returns:
        DataFrame with participant_id and median_rt
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    df = pd.read_csv(input_path)
    
    # Validate required columns
    if 'participant_id' not in df.columns:
        raise ValueError(f"Missing 'participant_id' column in {input_path}")
    if 'median_rt' not in df.columns:
        raise ValueError(f"Missing 'median_rt' column in {input_path}")
        
    return df[['participant_id', 'median_rt']]

def compute_relative_power(df_psd: pd.DataFrame, epsilon: float = 1e-10) -> pd.DataFrame:
    """
    Calculate relative power for each band (band_power / total_power).
    
    Args:
        df_psd: DataFrame with raw band power values
        epsilon: Small constant to prevent division by zero
        
    Returns:
        DataFrame with participant_id and relative power columns
    """
    # Calculate total power across all bands
    total_power = df_psd[BAND_COLUMNS].sum(axis=1)
    
    # Avoid division by zero
    total_power = total_power.replace(0, epsilon)
    
    # Calculate relative power
    df_relative = df_psd.copy()
    for band in BAND_COLUMNS:
        df_relative[band] = df_psd[band] / total_power
        
    return df_relative

def compute_clr_transformation(df_relative: pd.DataFrame, epsilon: float = 1e-10) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to relative power values.
    
    CLR(x)_i = log(x_i / g(x))
    where g(x) is the geometric mean of all components
    
    This handles the compositional nature of relative power data.
    
    Args:
        df_relative: DataFrame with relative power values
        epsilon: Small constant to prevent log(0)
        
    Returns:
        DataFrame with CLR-transformed values
    """
    df_clr = df_relative.copy()
    
    # Ensure no zeros before log transformation
    df_clr[BAND_COLUMNS] = df_clr[BAND_COLUMNS].replace(0, epsilon)
    
    # Calculate geometric mean for each row
    # g(x) = (x1 * x2 * ... * xn)^(1/n)
    log_components = np.log(df_clr[BAND_COLUMNS])
    geometric_mean_log = log_components.mean(axis=1)
    
    # CLR transformation: log(x_i) - log(g(x))
    for band in BAND_COLUMNS:
        df_clr[band] = log_components[band] - geometric_mean_log
        
    return df_clr

def validate_output(df_output: pd.DataFrame, output_path: str) -> bool:
    """
    Validate the output DataFrame schema and content.
    
    Args:
        df_output: Output DataFrame to validate
        output_path: Path where the file will be saved
        
    Returns:
        True if validation passes
    """
    # Check required columns
    required_cols = ['participant_id', 'median_rt'] + [f"{band}_clr" for band in BAND_COLUMNS]
    missing_cols = [col for col in required_cols if col not in df_output.columns]
    
    if missing_cols:
        raise ValueError(f"Output missing required columns: {missing_cols}")
        
    # Check for nulls in numeric columns
    numeric_cols = [col for col in df_output.columns if col != 'participant_id']
    null_counts = df_output[numeric_cols].isnull().sum()
    if null_counts.any():
        raise ValueError(f"Output contains null values:\n{null_counts[null_counts > 0]}")
        
    # Check RT range (100ms to 2000ms as per FR-004)
    rt_col = 'median_rt'
    if rt_col in df_output.columns:
        invalid_rt = df_output[(df_output[rt_col] < 100) | (df_output[rt_col] > 2000)]
        if len(invalid_rt) > 0:
            raise ValueError(f"Found {len(invalid_rt)} participants with RT outside valid range (100-2000ms)")
    
    print(f"✓ Output validation passed: {len(df_output)} participants, no nulls, valid RT range")
    return True

def main():
    """Main entry point for T015."""
    parser = argparse.ArgumentParser(description='Compute relative power and CLR transformation')
    parser.add_argument('--input-psd', type=str, default=None,
                      help='Path to input PSD file (default: from config)')
    parser.add_argument('--input-behavioral', type=str, default=None,
                      help='Path to behavioral metrics file (default: from config)')
    parser.add_argument('--output', type=str, default=None,
                      help='Path to output file (default: from config)')
    parser.add_argument('--epsilon', type=float, default=1e-10,
                      help='Small constant for numerical stability')
    args = parser.parse_args()
    
    # Determine paths
    input_psd = args.input_psd or get_path('interim', 'eeg_psd.csv')
    input_behavioral = args.input_behavioral or get_path('interim', 'behavioral_metrics.csv')
    output_path = args.output or get_path('processed', 'features_clr.csv')
    
    print(f"Loading raw PSD from: {input_psd}")
    print(f"Loading behavioral metrics from: {input_behavioral}")
    print(f"Output will be written to: {output_path}")
    
    # Ensure output directory exists
    ensure_dirs(output_path)
    
    # Load data
    try:
        df_psd = load_raw_features(input_psd)
        print(f"✓ Loaded {len(df_psd)} participants from PSD file")
    except Exception as e:
        print(f"✗ Failed to load PSD file: {e}")
        sys.exit(1)
        
    try:
        df_behavioral = load_behavioral_metrics(input_behavioral)
        print(f"✓ Loaded {len(df_behavioral)} participants from behavioral file")
    except Exception as e:
        print(f"✗ Failed to load behavioral file: {e}")
        sys.exit(1)
    
    # Merge datasets on participant_id
    df_merged = pd.merge(df_psd, df_behavioral, on='participant_id', how='inner')
    
    if len(df_merged) == 0:
        raise ValueError("No matching participants between PSD and behavioral datasets")
        
    print(f"✓ Merged datasets: {len(df_merged)} participants with both EEG and RT data")
    
    # Calculate relative power
    print("Calculating relative power...")
    df_relative = compute_relative_power(df_merged, epsilon=args.epsilon)
    
    # Apply CLR transformation
    print("Applying CLR transformation...")
    df_clr = compute_clr_transformation(df_relative, epsilon=args.epsilon)
    
    # Rename CLR columns to indicate transformation
    df_clr.rename(columns={band: f"{band}_clr" for band in BAND_COLUMNS}, inplace=True)
    
    # Reconstruct final DataFrame
    df_final = pd.DataFrame()
    df_final['participant_id'] = df_merged['participant_id']
    df_final['median_rt'] = df_merged['median_rt']
    for band in BAND_COLUMNS:
        df_final[f"{band}_clr"] = df_clr[f"{band}_clr"]
    
    # Validate output
    print("Validating output...")
    try:
        validate_output(df_final, output_path)
    except Exception as e:
        print(f"✗ Output validation failed: {e}")
        sys.exit(1)
    
    # Save output
    df_final.to_csv(output_path, index=False)
    print(f"✓ Successfully wrote {len(df_final)} rows to {output_path}")
    print(f"✓ Columns: {list(df_final.columns)}")
    
    # Print summary statistics
    print("\n=== Output Summary ===")
    print(f"Participants: {len(df_final)}")
    print(f"Features: {len(BAND_COLUMNS)} CLR-transformed bands")
    print(f"RT range: {df_final['median_rt'].min():.2f}ms - {df_final['median_rt'].max():.2f}ms")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())