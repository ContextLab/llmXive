"""
T030: Calculate Type II error delta (1 - power) relative to 30m baseline.

This script reads the power analysis results from data/results/power_analysis.csv,
identifies the baseline (30m resolution) power, and calculates the Type II error
delta for all other resolutions relative to that baseline.

Output:
  - data/results/type2_error_delta.csv: Contains resolution, power, baseline_power,
    type2_error (1-power), and type2_error_delta (relative to baseline).
"""

import os
import logging
import pandas as pd
from pathlib import Path
from utils import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
POWER_CSV_PATH = RESULTS_DIR / "power_analysis.csv"
OUTPUT_CSV_PATH = RESULTS_DIR / "type2_error_delta.csv"

def calculate_type2_error_delta(power_csv_path: Path, output_path: Path) -> None:
    """
    Calculate Type II error delta relative to 30m baseline.

    Type II error (beta) = 1 - Power
    Type II error delta = beta_current - beta_baseline

    Args:
        power_csv_path: Path to the input power analysis CSV.
        output_path: Path to save the output Type II error delta CSV.
    """
    if not power_csv_path.exists():
        raise FileNotFoundError(f"Power analysis file not found: {power_csv_path}")

    logger.info(f"Reading power analysis from {power_csv_path}")
    df = pd.read_csv(power_csv_path)

    # Ensure required columns exist
    required_cols = ['resolution', 'power']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {power_csv_path}: {missing_cols}")

    # Identify baseline (30m) power
    # Assuming 'resolution' is stored as string like '30m', '60m', etc.
    baseline_row = df[df['resolution'] == '30m']
    if baseline_row.empty:
        raise ValueError("No 30m baseline row found in power analysis data.")

    baseline_power = baseline_row['power'].iloc[0]
    logger.info(f"Baseline (30m) power: {baseline_power:.4f}")

    # Calculate Type II error (beta = 1 - power)
    df['type2_error'] = 1.0 - df['power']

    # Calculate Type II error delta relative to baseline
    # delta = beta_current - beta_baseline
    baseline_beta = 1.0 - baseline_power
    df['type2_error_delta'] = df['type2_error'] - baseline_beta

    # Select and order columns for output
    output_cols = ['resolution', 'power', 'type2_error', 'type2_error_delta']
    output_df = df[output_cols].copy()

    # Sort by resolution order (assuming numeric part extraction)
    def get_resolution_order(res_str):
        try:
            return int(''.join(filter(str.isdigit, res_str)))
        except ValueError:
            return 999999

    output_df['res_order'] = output_df['resolution'].apply(get_resolution_order)
    output_df = output_df.sort_values('res_order').drop(columns=['res_order'])

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    output_df.to_csv(output_path, index=False)
    logger.info(f"Type II error delta results saved to {output_path}")

    # Log summary
    logger.info("Summary of Type II error delta:")
    for _, row in output_df.iterrows():
        logger.info(f"  {row['resolution']}: Power={row['power']:.4f}, "
                    f"Type II Error={row['type2_error']:.4f}, "
                    f"Delta={row['type2_error_delta']:.4f}")

def main():
    """Main entry point for T030."""
    try:
        calculate_type2_error_delta(POWER_CSV_PATH, OUTPUT_CSV_PATH)
        logger.info("T030 completed successfully.")
    except Exception as e:
        logger.error(f"T030 failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()