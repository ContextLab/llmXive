"""
T021: Apply Bonferroni correction for 6 bands (0.05/6 = 0.0083) as per Spec FR-006.
Flags significant results in the output CSV.
"""
import os
import sys
import argparse
import pandas as pd
from pathlib import Path

# Add project root to path to resolve imports if running as script
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs
from utils.stats_helpers import bonferroni_correct


def load_correlations():
    """
    Load the correlations file produced by T020 (08_correlation_analysis.py).
    Expected path: data/processed/correlations.csv
    """
    input_path = get_path("processed", "correlations.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Ensure T020 (correlation analysis) has completed successfully."
        )
    df = pd.read_csv(input_path)
    
    # Validate expected columns
    required_cols = ['band', 'r', 'p_value', 'n', 'method']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Input file missing required columns: {missing_cols}")
        
    return df


def apply_bonferroni_correction(df):
    """
    Apply Bonferroni correction for 6 bands.
    Alpha = 0.05 / 6 = 0.008333...
    
    Updates the dataframe with:
    - 'bonferroni_threshold': The corrected alpha threshold
    - 'is_significant': Boolean flag for p_value < threshold
    - 'significant_after_correction': Boolean flag (alias for clarity)
    """
    num_tests = 6
    alpha = 0.05
    threshold = alpha / num_tests
    
    df['bonferroni_threshold'] = threshold
    df['is_significant'] = df['p_value'] < threshold
    df['significant_after_correction'] = df['is_significant']
    
    return df


def save_corrected_results(df):
    """
    Save the corrected results to data/processed/correlations_bonferroni.csv.
    """
    output_dir = get_path("processed", "")
    ensure_dirs(output_dir)
    
    output_path = os.path.join(output_dir, "correlations_bonferroni.csv")
    df.to_csv(output_path, index=False)
    print(f"Saved Bonferroni-corrected results to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Apply Bonferroni correction to correlation results (T021)."
    )
    parser.parse_args()

    try:
        # 1. Load raw correlations from T020
        df = load_correlations()
        print(f"Loaded {len(df)} correlation results.")

        # 2. Apply correction
        df_corrected = apply_bonferroni_correction(df)
        
        # 3. Log summary
        total_tests = len(df_corrected)
        significant_count = df_corrected['is_significant'].sum()
        print(f"Bonferroni Threshold: {df_corrected['bonferroni_threshold'].iloc[0]:.4f} (0.05/6)")
        print(f"Significant results after correction: {significant_count} / {total_tests}")

        # 4. Save results
        save_corrected_results(df_corrected)

        print("Task T021 completed successfully.")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
