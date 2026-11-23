"""
T021: Apply Bonferroni correction for 6 bands (alpha = 0.0083).
Flag significant results and write data/processed/correlations_corrected.csv.

Input: data/interim/correlations_raw.csv (produced by T020/code/06_correlations.py)
Output: data/processed/correlations_corrected.csv

Logic:
1. Load raw correlations.
2. Calculate adjusted p-values using Bonferroni correction (alpha / 6).
3. Flag results as significant if adjusted p-value < 0.05.
4. Write the corrected CSV.
"""
import os
import sys
import argparse
import pandas as pd
from pathlib import Path

# Add project root to path to ensure imports work if run from subdirectory
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs


def load_correlations(input_path: str) -> pd.DataFrame:
    """Load the raw correlations CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T020 (code/06_correlations.py) has completed successfully."
        )
    df = pd.read_csv(input_path)
    required_cols = ['band', 'r_value', 'p_value', 'n']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input file missing required columns: {missing}")
    return df


def apply_bonferroni_correction(df: pd.DataFrame, alpha: float = 0.05, n_bands: int = 6) -> pd.DataFrame:
    """
    Apply Bonferroni correction.
    
    The task specifies dividing 0.05 by 6.
    We calculate the adjusted p-value (p * n_bands) capped at 1.0.
    We also calculate the threshold (alpha / n_bands) for flagging.
    """
    if df.empty:
        return df.copy()
    
    # Calculate adjusted p-values
    # Bonferroni: p_adj = p * k, capped at 1.0
    df['p_value_adj'] = df['p_value'] * n_bands
    df['p_value_adj'] = df['p_value_adj'].clip(upper=1.0)
    
    # Calculate the significance threshold
    threshold = alpha / n_bands
    df['threshold'] = threshold
    
    # Flag significant results based on the adjusted p-value against the standard alpha (0.05)
    # OR based on raw p-value against the corrected threshold. Both are mathematically equivalent.
    # We use p_value_adj < 0.05 for clarity.
    df['is_significant'] = df['p_value_adj'] < alpha
    
    return df


def save_corrected_results(df: pd.DataFrame, output_path: str) -> None:
    """Save the corrected correlations to CSV."""
    ensure_dirs(output_path)
    df.to_csv(output_path, index=False)
    print(f"Saved corrected correlations to: {output_path}")
    print(f"Significant results: {df['is_significant'].sum()}")


def main():
    parser = argparse.ArgumentParser(description="Apply Bonferroni correction to correlation results.")
    parser.add_argument(
        "--input", 
        type=str, 
        default=None,
        help="Path to input correlations_raw.csv. Defaults to project standard location."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None,
        help="Path to output correlations_corrected.csv. Defaults to project standard location."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level (default: 0.05)"
    )
    parser.add_argument(
        "--n-bands",
        type=int,
        default=6,
        help="Number of bands for correction (default: 6)"
    )
    
    args = parser.parse_args()
    
    # Determine paths
    if args.input:
        input_path = args.input
    else:
        input_path = get_path("interim", "correlations_raw.csv")
        
    if args.output:
        output_path = args.output
    else:
        output_path = get_path("processed", "correlations_corrected.csv")
        
    print(f"Loading correlations from: {input_path}")
    df = load_correlations(input_path)
    
    print(f"Applying Bonferroni correction (alpha={args.alpha}, n_bands={args.n_bands})")
    df_corrected = apply_bonferroni_correction(df, alpha=args.alpha, n_bands=args.n_bands)
    
    print(f"Saving results to: {output_path}")
    save_corrected_results(df_corrected, output_path)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
