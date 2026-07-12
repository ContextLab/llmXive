"""
T029: Generate sensitivity_report.json comparing results across exclusion scenarios and threshold sweeps.

Input:
  - data/processed/sensitivity_exclusion_results.csv
  - data/processed/sensitivity_threshold_results.csv
Output:
  - data/processed/sensitivity_report.json

Required fields in JSON: scenario, r_value, p_value, n_excluded.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Add project root to path to allow imports from utils
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import setup_general_logger

def load_sensitivity_data(filepath: Path) -> pd.DataFrame:
    """Load a CSV file and return as DataFrame."""
    if not filepath.exists():
        raise FileNotFoundError(f"Required input file not found: {filepath}")
    return pd.read_csv(filepath)

def build_report(exclusion_df: pd.DataFrame, threshold_df: pd.DataFrame) -> list:
    """
    Combine exclusion and threshold results into the required report format.
    
    Expected columns in exclusion_df: scenario, r_value, p_value, n_excluded (and others)
    Expected columns in threshold_df: scenario, r_value, p_value, n_excluded (and others)
    
    Returns a list of dictionaries, each representing one row of results.
    """
    report_data = []

    # Process exclusion results
    if not exclusion_df.empty:
        # Ensure required columns exist, fill with 0 or NaN if missing
        for col in ['scenario', 'r_value', 'p_value', 'n_excluded']:
            if col not in exclusion_df.columns:
                exclusion_df[col] = 0 if col == 'n_excluded' else None
        
        for _, row in exclusion_df.iterrows():
          report_data.append({
              "scenario": str(row.get('scenario', 'unknown')),
              "r_value": float(row['r_value']) if pd.notna(row['r_value']) else None,
              "p_value": float(row['p_value']) if pd.notna(row['p_value']) else None,
              "n_excluded": int(row['n_excluded']) if pd.notna(row['n_excluded']) else 0
          })

    # Process threshold results
    if not threshold_df.empty:
        for col in ['scenario', 'r_value', 'p_value', 'n_excluded']:
            if col not in threshold_df.columns:
                threshold_df[col] = 0 if col == 'n_excluded' else None

        for _, row in threshold_df.iterrows():
          report_data.append({
              "scenario": str(row.get('scenario', 'unknown')),
              "r_value": float(row['r_value']) if pd.notna(row['r_value']) else None,
              "p_value": float(row['p_value']) if pd.notna(row['p_value']) else None,
              "n_excluded": int(row['n_excluded']) if pd.notna(row['n_excluded']) else 0
          })

    return report_data

def main():
    logger = setup_general_logger("generate_sensitivity_report")
    logger.info("Starting sensitivity report generation (T029).")

    # Define paths relative to project root
    data_dir = project_root / "data" / "processed"
    exclusion_input = data_dir / "sensitivity_exclusion_results.csv"
    threshold_input = data_dir / "sensitivity_threshold_results.csv"
    output_file = data_dir / "sensitivity_report.json"

    # Verify inputs exist
    if not exclusion_input.exists():
        logger.error(f"Input file missing: {exclusion_input}")
        sys.exit(1)
    if not threshold_input.exists():
        logger.error(f"Input file missing: {threshold_input}")
        sys.exit(1)

    try:
        # Load data
        logger.info(f"Loading {exclusion_input}")
        exclusion_df = load_sensitivity_data(exclusion_input)
        logger.info(f"Loaded {len(exclusion_df)} rows from exclusion results.")

        logger.info(f"Loading {threshold_input}")
        threshold_df = load_sensitivity_data(threshold_input)
        logger.info(f"Loaded {len(threshold_df)} rows from threshold results.")

        # Build report
        report_data = build_report(exclusion_df, threshold_df)

        # Write output
        logger.info(f"Writing report to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"Sensitivity report successfully generated: {output_file}")
        logger.info(f"Total records in report: {len(report_data)}")

    except Exception as e:
        logger.error(f"Error generating sensitivity report: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()