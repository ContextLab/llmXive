"""
T021: Apply Bonferroni correction for 6 bands (α = 0.0083).
Flag significant results and write data/processed/correlations_corrected.csv.

Dependencies: T020 (code/06_correlations.py) which produces data/interim/correlations_raw.csv.
"""
import os
import sys
import argparse
import pandas as pd
from pathlib import Path

# Import project config for path handling
# Note: The existing config.py has a flexible get_path/ensure_dirs signature
# that handles various call patterns. We import it directly.
try:
    from config import get_path, ensure_dirs
except ImportError:
    # Fallback for execution context where config is in parent directory
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from config import get_path, ensure_dirs


def load_correlations():
    """
    Load the raw correlations from data/interim/correlations_raw.csv.
    Expects columns: band, r_value, p_value, n
    """
    input_path = get_path("interim", "correlations_raw.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please run code/06_correlations.py (T020) first."
        )
    return pd.read_csv(input_path)


def apply_bonferroni_correction(df, n_tests=6):
    """
    Apply Bonferroni correction to the p-values.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing 'p_value' column.
    n_tests : int
        Number of hypothesis tests performed (default 6 for 6 bands).
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with added columns: 'bonferroni_p_value', 'is_significant'
    """
    # Calculate corrected p-value (clamped at 1.0)
    df = df.copy()
    df['bonferroni_p_value'] = (df['p_value'] * n_tests).clip(upper=1.0)
    
    # Determine significance at alpha = 0.05 / 6 = 0.00833...
    # The task description specifies alpha = 0.0083
    alpha_threshold = 0.05 / n_tests
    df['is_significant'] = df['bonferroni_p_value'] < alpha_threshold
    
    return df


def save_corrected_results(df, output_path):
    """
    Save the corrected correlations to a CSV file.
    """
    ensure_dirs(output_path)
    df.to_csv(output_path, index=False)
    print(f"Corrected correlations saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Apply Bonferroni correction to correlation results (T021)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save the corrected results. Defaults to data/processed/correlations_corrected.csv."
    )
    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_path("processed", "correlations_corrected.csv")

    print("Loading raw correlations...")
    try:
        df = load_correlations()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Applying Bonferroni correction for {len(df)} tests (6 bands)...")
    df_corrected = apply_bonferroni_correction(df, n_tests=6)

    print(f"Saving results to {output_path}...")
    save_corrected_results(df_corrected, output_path)

    # Summary
    sig_count = df_corrected['is_significant'].sum()
    print(f"Analysis complete. Found {sig_count} significant correlations out of {len(df)} tests (α={0.05/6:.4f}).")


if __name__ == "__main__":
    main()
