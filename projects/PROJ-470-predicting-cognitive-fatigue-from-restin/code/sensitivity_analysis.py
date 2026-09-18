"""
Sensitivity Analysis for Cognitive Fatigue Study.

Implements FR-006: Sensitivity analysis at p<=0.05 and p<=0.01 thresholds.
Reads Benjamini-Hochberg corrected p-values and generates a summary table
of significant electrodes at both thresholds.
"""
import os
import sys
import csv
from pathlib import Path
import pandas as pd
import numpy as np

# Import from project modules
from code.utils.logging import get_logger, log_operation
from code.config import load_config

# Constants
ANALYSIS_DIR = Path("data/analysis")
INPUT_FILE = ANALYSIS_DIR / "bh_corrected_pvalues.csv"
OUTPUT_FILE = ANALYSIS_DIR / "sensitivity_table.csv"


def load_analysis_results():
    """Load the Benjamini-Hochberg corrected p-values."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Required input file not found: {INPUT_FILE}. "
            "Run code/benjamini_hochberg.py first."
        )
    return pd.read_csv(INPUT_FILE)


def run_sensitivity_analysis(df):
    """
    Perform sensitivity analysis on BH-corrected p-values.

    Counts the number of significant electrodes at:
    - p <= 0.05
    - p <= 0.01

    Args:
        df: DataFrame containing 'channel' and 'p_value_bh' (corrected p-values).

    Returns:
        DataFrame with counts of significant electrodes at each threshold.
    """
    if 'p_value_bh' not in df.columns:
        # Fallback if column name varies, but spec says 'p_value_bh'
        valid_cols = [c for c in df.columns if 'p_value' in c.lower()]
        if not valid_cols:
            raise ValueError(
                f"Could not find p-value column in {INPUT_FILE}. "
                f"Available columns: {list(df.columns)}"
            )
        p_col = valid_cols[0]
    else:
        p_col = 'p_value_bh'

    # Ensure numeric
    df[p_col] = pd.to_numeric(df[p_col], errors='coerce')

    # Count significant at 0.05
    sig_05 = (df[p_col] <= 0.05).sum()
    # Count significant at 0.01
    sig_01 = (df[p_col] <= 0.01).sum()

    # Create result table
    result = pd.DataFrame({
        'threshold': [0.05, 0.01],
        'significant_electrodes': [sig_05, sig_01],
        'total_electrodes': [len(df), len(df)]
    })

    return result


def generate_sensitivity_table(df):
    """
    Generate the sensitivity analysis table and write to CSV.

    Args:
        df: DataFrame with corrected p-values.
    """
    result = run_sensitivity_analysis(df)
    result.to_csv(OUTPUT_FILE, index=False)
    return result


def main():
    """Main entry point for sensitivity analysis."""
    logger = get_logger("sensitivity_analysis", log_file=str(ANALYSIS_DIR / "sensitivity_analysis.log"))
    logger.log("Starting sensitivity analysis pipeline")

    try:
        # Load data
        logger.log("Loading BH-corrected p-values", input_file=str(INPUT_FILE))
        df = load_analysis_results()
        logger.log("Loaded data", rows=len(df), columns=list(df.columns))

        # Run analysis
        logger.log("Running sensitivity analysis", thresholds=[0.05, 0.01])
        result = generate_sensitivity_table(df)

        # Log results
        logger.log("Sensitivity analysis complete", output_file=str(OUTPUT_FILE))
        logger.log("Results summary", 
                   sig_05=int(result[result['threshold']==0.05]['significant_electrodes'].iloc[0]),
                   sig_01=int(result[result['threshold']==0.01]['significant_electrodes'].iloc[0]))

        print(f"Sensitivity analysis complete. Results written to {OUTPUT_FILE}")
        return 0

    except FileNotFoundError as e:
        logger.log("Error: File not found", error=str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.log("Error: Pipeline failed", error=str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
