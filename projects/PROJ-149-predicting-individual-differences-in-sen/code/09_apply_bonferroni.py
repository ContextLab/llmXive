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

# Import config utilities if available, otherwise define basic path handling
try:
    from config import get_path, ensure_dirs
except ImportError:
    # Fallback if config is not in path or missing specific functions
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    def get_path(*subdirs, filename=None):
        p = PROJECT_ROOT
        for d in subdirs:
            p = p / d
        if filename:
            p = p / filename
        return p

    def ensure_dirs(path):
        if isinstance(path, str):
            path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

def load_correlations(input_path=None):
    """
    Load the raw correlations from T020.
    Expected columns: band, r_value, p_value, n
    """
    if input_path is None:
        input_path = get_path("interim", "correlations_raw.csv")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Required input file not found: {input_path}. "
                              "Please ensure T020 (code/06_correlations.py) has completed successfully.")
    
    df = pd.read_csv(input_path)
    required_cols = {'band', 'p_value'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Input file missing required columns: {missing}")
    
    return df

def apply_bonferroni_correction(df, num_tests=6):
    """
    Apply Bonferroni correction.
    Corrected alpha = 0.05 / 6 ≈ 0.008333...
    Flags results as significant if p_value <= corrected_alpha.
    """
    alpha = 0.05
    corrected_alpha = alpha / num_tests
    
    # Calculate adjusted p-values (min(p * num_tests, 1.0))
    df['p_value_corrected'] = df['p_value'].apply(lambda p: min(p * num_tests, 1.0))
    
    # Flag significance based on the corrected threshold
    df['significant_bonferroni'] = df['p_value'] <= corrected_alpha
    
    # Add the threshold value for reference
    df['bonferroni_threshold'] = corrected_alpha
    
    return df

def save_corrected_results(df, output_path=None):
    """
    Save the corrected correlations to data/processed/correlations_corrected.csv.
    """
    if output_path is None:
        output_path = get_path("processed", "correlations_corrected.csv")
    
    # Ensure output directory exists
    ensure_dirs(Path(output_path).parent)
    
    df.to_csv(output_path, index=False)
    print(f"Corrected correlations saved to: {output_path}")
    
    # Print summary
    n_sig = df['significant_bonferroni'].sum()
    print(f"Significant results (p <= {df['bonferroni_threshold'].iloc[0]:.4f}): {n_sig} / {len(df)}")

def main():
    parser = argparse.ArgumentParser(description="Apply Bonferroni correction to correlation results.")
    parser.add_argument("--input", type=str, default=None, help="Path to input correlations CSV (default: data/interim/correlations_raw.csv)")
    parser.add_argument("--output", type=str, default=None, help="Path to output corrected CSV (default: data/processed/correlations_corrected.csv)")
    parser.add_argument("--num-tests", type=int, default=6, help="Number of hypothesis tests for correction (default: 6 bands)")
    args = parser.parse_args()

    try:
        # Load raw correlations
        df = load_correlations(args.input)
        
        # Apply correction
        df_corrected = apply_bonferroni_correction(df, num_tests=args.num_tests)
        
        # Save results
        save_corrected_results(df_corrected, args.output)
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
