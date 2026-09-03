"""
Task T021: Apply Bonferroni correction for 6 bands (α = 0.0083).
Flag significant results and write data/processed/correlations_corrected.csv.

Dependencies: T020 (06_correlations.py) which produces data/interim/correlations_raw.csv.
"""
import os
import sys
import argparse
import pandas as pd
from pathlib import Path

# Add project root to path to allow relative imports if needed, 
# though this script primarily uses standard libs and pandas.
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs

def load_correlations(input_path: str) -> pd.DataFrame:
    """
    Load the raw correlation results from T020.
    Expected columns: band, r_value, p_value, n
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Ensure T020 (code/06_correlations.py) has completed successfully."
        )
    df = pd.read_csv(input_path)
    required_cols = ['band', 'r_value', 'p_value', 'n']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input file missing required columns: {missing}")
    return df

def apply_bonferroni_correction(df: pd.DataFrame, num_tests: int = 6) -> pd.DataFrame:
    """
    Apply Bonferroni correction to the p-values.
    Alpha = 0.05 / num_tests.
    Flag results as significant if p_value <= corrected_alpha.
    """
    alpha = 0.05
    corrected_alpha = alpha / num_tests
    
    df = df.copy()
    df['corrected_alpha'] = corrected_alpha
    df['significant'] = df['p_value'] <= corrected_alpha
    
    return df

def save_corrected_results(df: pd.DataFrame, output_path: str):
    """
    Save the corrected results to the specified output path.
    Output columns: band, r_value, p_value, n, corrected_alpha, significant
    """
    ensure_dirs(output_path)
    df.to_csv(output_path, index=False)
    print(f"Saved Bonferroni-corrected results to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Apply Bonferroni correction to correlation results.")
    parser.add_argument("--input", type=str, help="Path to raw correlations CSV (default: data/interim/correlations_raw.csv)")
    parser.add_argument("--output", type=str, help="Path to output corrected CSV (default: data/processed/correlations_corrected.csv)")
    args = parser.parse_args()

    # Default paths based on task specification
    input_path = args.input or get_path("interim", "correlations_raw.csv")
    output_path = args.output or get_path("processed", "correlations_corrected.csv")

    print(f"Loading correlations from: {input_path}")
    try:
        df = load_correlations(input_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    print(f"Applying Bonferroni correction (6 bands, alpha=0.05)...")
    df_corrected = apply_bonferroni_correction(df, num_tests=6)

    print(f"Saving results to: {output_path}")
    save_corrected_results(df_corrected, output_path)

    # Summary
    sig_count = df_corrected['significant'].sum()
    print(f"Significant correlations: {sig_count} / {len(df_corrected)}")

if __name__ == "__main__":
    main()
