"""
Task T021: Apply Bonferroni correction to correlation results.

Reads raw correlations from code/06_correlations.py output,
applies Bonferroni correction for 6 bands, flags significant results,
and writes the corrected CSV.
"""
import os
import sys
import argparse
import pandas as pd
from pathlib import Path

# Import from project config
from config import bonferroni_correct, get_path, ensure_dirs


def load_correlations(input_path: str) -> pd.DataFrame:
    """
    Load the raw correlations CSV produced by code/06_correlations.py.

    Expected columns: 'band', 'r_value', 'p_value', 'n'
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Correlations file not found: {input_path}")

    df = pd.read_csv(input_path)

    required_cols = {'band', 'r_value', 'p_value', 'n'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Correlations file missing required columns: {missing}")

    return df


def apply_bonferroni_correction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Bonferroni correction to the p-values.

    The correction is: corrected_p = raw_p * n_tests
    For 6 bands, n_tests = 6.
    Flags results as significant if corrected_p < 0.05.

    Returns a new DataFrame with added columns:
    - 'bonferroni_p': the corrected p-value
    - 'significant': boolean flag
    """
    df = df.copy()

    # Calculate corrected p-value
    # Cap at 1.0 if correction pushes it above
    df['bonferroni_p'] = df['p_value'] * 6.0
    df['bonferroni_p'] = df['bonferroni_p'].clip(upper=1.0)

    # Flag significance at alpha = 0.05
    df['significant'] = df['bonferroni_p'] < 0.05

    return df


def save_corrected_results(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the corrected correlations to a CSV file.
    """
    # Ensure output directory exists
    ensure_dirs(output_path)

    # Write to disk
    df.to_csv(output_path, index=False)
    print(f"Corrected correlations saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Apply Bonferroni correction to correlation results (T021)."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to raw correlations CSV. Defaults to project config path."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output corrected CSV. Defaults to project config path."
    )
    args = parser.parse_args()

    # Determine input path
    if args.input:
        input_path = args.input
    else:
        # Default: read from code/06_correlations.py output location
        # Based on task T020 description: data/interim/correlations_raw.csv
        input_path = get_path("interim", "correlations_raw.csv")

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        # Default: data/processed/correlations_corrected.csv (per task spec)
        output_path = get_path("processed", "correlations_corrected.csv")

    print(f"Loading raw correlations from: {input_path}")
    try:
        df = load_correlations(input_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Make sure code/06_correlations.py has been run successfully.")
        sys.exit(1)

    print(f"Loaded {len(df)} correlation records.")

    print("Applying Bonferroni correction (n_tests=6, alpha=0.05)...")
    df_corrected = apply_bonferroni_correction(df)

    # Count significant results
    n_sig = df_corrected['significant'].sum()
    print(f"Significant results after correction: {n_sig} / {len(df)}")

    print(f"Saving corrected results to: {output_path}")
    save_corrected_results(df_corrected, output_path)

    print("Task T021 completed successfully.")


if __name__ == "__main__":
    main()
