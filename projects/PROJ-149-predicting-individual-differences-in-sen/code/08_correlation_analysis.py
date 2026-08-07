"""
T020: Implement Pearson correlation tests between relative band powers and median RT.

Reads data/processed/features.csv (produced by T015/T016).
Computes Pearson correlation coefficients and p-values for each band power vs median RT.
Writes results to data/processed/correlations.csv.

Dependencies:
  - data/processed/features.csv (T015, T016)

Outputs:
  - data/processed/correlations.csv
"""
import os
import sys
import argparse
import json
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import get_path


def load_features():
    """Load the validated features dataset."""
    features_path = get_path("processed", "features.csv")
    if not os.path.exists(features_path):
        raise FileNotFoundError(
            f"Required input file not found: {features_path}. "
            "Ensure T015 and T016 have completed successfully."
        )
    df = pd.read_csv(features_path)
    
    # Verify required columns exist
    required_cols = ['participant_id', 'median_rt'] + [
        f'rel_{band}_power' for band in ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in features.csv: {missing}")
    
    return df


def run_correlations(df):
    """
    Compute Pearson correlation between each relative band power and median RT.
    
    Returns a DataFrame with columns:
      - band: band name
      - r: Pearson correlation coefficient
      - p: p-value
      - n: sample size
      - significant_raw: boolean (p < 0.05)
    """
    bands = ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
    results = []
    
    y = df['median_rt'].values
    n = len(y)
    
    for band in bands:
        col_name = f'rel_{band}_power'
        x = df[col_name].values
        
        # Handle NaNs if any (though T016 should have filtered them)
        mask = ~(np.isnan(x) | np.isnan(y))
        if np.sum(mask) < 2:
            raise ValueError(f"Not enough valid data points for {band} correlation.")
        
        r, p = stats.pearsonr(x[mask], y[mask])
        
        results.append({
            'band': band,
            'r': r,
            'p': p,
            'n': int(np.sum(mask)),
            'significant_raw': p < 0.05
        })
    
    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(description="Run Pearson correlation analysis between EEG band powers and RT.")
    parser.add_argument('--output', type=str, default=None, help="Path to output CSV (default: data/processed/correlations.csv)")
    args = parser.parse_args()
    
    # Set random seed for reproducibility (though correlation is deterministic)
    from config import get_seed
    seed = get_seed()
    np.random.seed(seed)
    
    print(f"Loading features from {get_path('processed', 'features.csv')}...")
    df = load_features()
    print(f"Loaded {len(df)} participants.")
    
    print("Running Pearson correlations...")
    corr_results = run_correlations(df)
    
    output_path = args.output if args.output else get_path("processed", "correlations.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    corr_results.to_csv(output_path, index=False)
    print(f"Correlation results saved to {output_path}")
    
    # Print summary
    print("\nCorrelation Summary:")
    print(corr_results.to_string(index=False))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
