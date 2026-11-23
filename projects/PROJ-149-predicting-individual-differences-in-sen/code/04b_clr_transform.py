"""
T012b: Implement mandatory CLR transformation to satisfy compositional data constraints.

Reads data/processed/features.csv (produced by T012) and writes data/processed/features_clr.csv.

Formula: log(x + config.EPSILON) - mean(log(x + config.EPSILON))
where config.EPSILON = 1e-9.

Dependencies: T012 (must produce data/processed/features.csv first).
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np

# Add project root to path to import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import get_epsilon, get_path

BAND_COLUMNS = [
    'delta_rel',
    'theta_rel',
    'alpha_rel',
    'low_beta_rel',
    'high_beta_rel',
    'gamma_rel'
]

def load_features(input_path: str) -> pd.DataFrame:
    """Load the features CSV produced by T012."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T012 (code/04_extract_features.py) has run successfully."
        )
    df = pd.read_csv(input_path)
    required_cols = ['participant_id', 'median_rt'] + BAND_COLUMNS
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Input file missing required columns: {missing}. "
            f"Expected columns: {required_cols}"
        )
    return df

def compute_clr_transformation(df: pd.DataFrame, epsilon: float) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to relative power bands.

    Formula: clr(x) = log(x + epsilon) - mean(log(x + epsilon))

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing relative power band columns.
    epsilon : float
        Small constant to avoid log(0), from config.EPSILON.

    Returns
    -------
    pd.DataFrame
        DataFrame with CLR-transformed band columns.
    """
    df_clr = df.copy()

    for band in BAND_COLUMNS:
        # Compute log(x + epsilon)
        log_vals = np.log(df_clr[band].values + epsilon)

        # Compute mean of log values across all participants for this band
        mean_log = np.mean(log_vals)

        # Compute CLR: log(x + epsilon) - mean(log(x + epsilon))
        clr_vals = log_vals - mean_log

        df_clr[band] = clr_vals

    return df_clr

def save_features_clr(df: pd.DataFrame, output_path: str) -> None:
    """Save the CLR-transformed features to CSV."""
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df.to_csv(output_path, index=False)
    print(f"CLR-transformed features saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="T012b: Apply CLR transformation to EEG band power features."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input features CSV (default: data/processed/features.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output CLR features CSV (default: data/processed/features_clr.csv)"
    )
    args = parser.parse_args()

    # Determine input/output paths
    input_path = args.input if args.input else get_path("data/processed/features.csv")
    output_path = args.output if args.output else get_path("data/processed/features_clr.csv")

    print(f"Loading features from: {input_path}")
    df = load_features(input_path)
    print(f"Loaded {len(df)} participants with {len(BAND_COLUMNS)} band columns.")

    epsilon = get_epsilon()
    print(f"Applying CLR transformation with epsilon={epsilon}...")

    df_clr = compute_clr_transformation(df, epsilon)

    print(f"Saving CLR-transformed features to: {output_path}")
    save_features_clr(df_clr, output_path)

    print("T012b CLR transformation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())