import os
import sys
import argparse
import pandas as pd
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs
from utils.stats_helpers import bonferroni_correct

def load_correlations():
    """
    Load the correlations output from T020.
    Expected path: data/processed/correlations.csv
    """
    input_path = get_path("data/processed/correlations.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Correlations file not found at {input_path}. "
            "Please ensure T020 (code/08_correlation_analysis.py) has run successfully."
        )
    return pd.read_csv(input_path)

def apply_bonferroni_correction(df):
    """
    Apply Bonferroni correction for 6 bands (0.05 / 6 = 0.008333...).
    
    FR-006 Requirement:
    - Correct p-values for 6 comparisons.
    - Flag significant results based on the corrected threshold.
    
    Args:
        df (pd.DataFrame): DataFrame containing 'band', 'p_value', 'r' columns.
    
    Returns:
        pd.DataFrame: DataFrame with added 'p_corrected', 'significant', 'threshold' columns.
    """
    if df.empty:
        return df

    # Copy to avoid modifying original
    result = df.copy()
    
    # Calculate corrected p-values (FDR or simple Bonferroni multiplication)
    # Standard Bonferroni: p_corrected = p * n_tests
    n_tests = 6
    result['p_corrected'] = result['p_value'] * n_tests
    
    # Cap corrected p-values at 1.0
    result['p_corrected'] = result['p_corrected'].clip(upper=1.0)
    
    # Define the threshold
    alpha = 0.05
    threshold = alpha / n_tests
    result['threshold'] = threshold
    
    # Flag significance based on corrected p-value vs threshold
    # (Equivalent to: p_value < threshold)
    result['significant'] = result['p_corrected'] < threshold
    
    return result

def save_corrected_results(df):
    """
    Save the Bonferroni-corrected results to data/processed/correlations.csv.
    
    This overwrites the original correlations file with the corrected version,
    as per the pipeline flow where T025 will consume this final version.
    """
    output_path = get_path("data/processed/correlations.csv")
    ensure_dirs(output_path)
    
    df.to_csv(output_path, index=False)
    print(f"Saved Bonferroni-corrected correlations to {output_path}")
    
    # Print summary
    sig_count = df['significant'].sum()
    print(f"Summary: {sig_count} of {len(df)} correlations are significant after Bonferroni correction (threshold={df['threshold'].iloc[0]:.4f}).")

def main():
    parser = argparse.ArgumentParser(
        description="Apply Bonferroni correction to correlation results (T021)."
    )
    parser.parse_args()

    print("Loading correlations from T020...")
    df = load_correlations()

    print("Applying Bonferroni correction (6 bands)...")
    corrected_df = apply_bonferroni_correction(df)

    print("Saving results...")
    save_corrected_results(corrected_df)

    print("T021 Complete.")

if __name__ == "__main__":
    main()
