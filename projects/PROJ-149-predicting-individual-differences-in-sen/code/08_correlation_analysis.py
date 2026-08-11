"""
T020: Implement Pearson correlation tests between relative band powers and median RT.

This script loads the processed features (containing CLR-transformed relative band powers
and median RT) and computes Pearson correlation coefficients and p-values for each band.

Output:
    data/processed/correlations_raw.csv: Contains correlation stats before Bonferroni correction.

Dependencies:
    - T016 (data/processed/features.csv must exist and be valid)
    - T015 (features must contain CLR-transformed relative powers)
"""
import os
import sys
import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs, get_seed
from utils.stats_helpers import bonferroni_correct

def load_features(path_str: str) -> pd.DataFrame:
    """
    Load the processed features CSV.
    
    Args:
        path_str: Path to the features CSV file.
        
    Returns:
        DataFrame with features and behavioral metrics.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Features file not found: {path_str}")
    
    df = pd.read_csv(path)
    
    # Verify expected columns exist (relative to T015 output)
    # We expect columns like: participant_id, median_rt, and band powers (delta, theta, alpha, beta, gamma)
    # The task specifies "relative band powers", which T015 applies CLR to.
    # We look for columns containing 'power' or specific band names.
    required_cols = ['participant_id', 'median_rt']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' missing in features file.")
    
    return df

def run_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Pearson correlations between each band power and median RT.
    
    Args:
        df: DataFrame containing band power columns and 'median_rt'.
        
    Returns:
        DataFrame with correlation statistics (band, r, p_value, n).
    """
    # Identify band power columns. 
    # Based on T015, these should be the relative power columns (possibly CLR transformed).
    # We look for columns that are not participant_id or median_rt.
    # Common naming: 'delta_power', 'theta_power', 'alpha_power', 'beta_power', 'gamma_power'
    # or 'delta', 'theta', etc. We will be flexible and check for common patterns.
    
    exclude_cols = ['participant_id', 'median_rt']
    band_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Filter to likely band power columns (heuristic: contains 'power' or is a known band name)
    known_bands = ['delta', 'theta', 'alpha', 'beta', 'gamma', 'low_beta', 'high_beta']
    valid_band_cols = []
    
    for col in band_cols:
        # Check if column name matches a known band or contains 'power'
        if any(band in col.lower() for band in known_bands) or 'power' in col.lower():
            valid_band_cols.append(col)
    
    if not valid_band_cols:
        # Fallback: assume all remaining numeric columns are bands
        valid_band_cols = [col for col in band_cols if pd.api.types.is_numeric_dtype(df[col])]
        if not valid_band_cols:
            raise ValueError("No band power columns found in features file.")

    results = []
    
    # Drop rows with NaN in median_rt or any band column for correlation calculation
    clean_df = df.dropna(subset=['median_rt'] + valid_band_cols)
    n = len(clean_df)
    
    if n < 3:
        raise ValueError(f"Insufficient samples for correlation (n={n}). Need at least 3.")
    
    for band_col in valid_band_cols:
        # Extract series
        x = clean_df[band_col].values
        y = clean_df['median_rt'].values
        
        # Compute Pearson correlation
        r, p_value = np.corrcoef(x, y)[0, 1]
        
        results.append({
            'band': band_col,
            'r': r,
            'p_value': p_value,
            'n': n
        })
    
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description="Run Pearson correlation analysis (T020)")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/features.csv",
        help="Path to the processed features CSV (default: data/processed/features.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/correlations_raw.csv",
        help="Path to save the raw correlation results (default: data/processed/correlations_raw.csv)"
    )
    args = parser.parse_args()

    # Set global seed for reproducibility if needed (though corrcoef is deterministic)
    set_global_seed()

    # Ensure output directory exists
    output_path = Path(args.output)
    ensure_dirs(output_path)

    print(f"Loading features from {args.input}...")
    try:
        features_df = load_features(args.input)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Running correlations on {len(features_df)} participants...")
    try:
        corr_results = run_correlations(features_df)
    except Exception as e:
        print(f"ERROR during correlation calculation: {e}")
        sys.exit(1)

    print(f"Saving results to {args.output}...")
    corr_results.to_csv(args.output, index=False)

    print(f"Correlation analysis complete. Found {len(corr_results)} bands.")
    print("Sample results:")
    print(corr_results.to_string(index=False))

if __name__ == "__main__":
    main()