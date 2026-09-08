import pandas as pd
import numpy as np
from pathlib import Path
import sys
import logging

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from analysis.metrics import process_metrics_for_discharges, detect_outliers, validate_metric_ranges
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """
    Load the unified dataset from data/processed/unified_analysis.csv,
    calculate resonant_surface_density for each discharge, handle outliers,
    and save the results to data/processed/metrics.csv.
    """
    input_path = Path("data/processed/unified_analysis.csv")
    output_path = Path("data/processed/metrics.csv")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run the data retrieval pipeline (T016) first to generate unified_analysis.csv.")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    # Check for required columns
    required_cols = ['q_profile', 'rho_tor_profile', 'island_width', 'minor_radius']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns in input data: {missing}")
        logger.error("Ensure the input file contains q_profile and rho_tor_profile arrays (as lists or JSON strings).")
        sys.exit(1)

    # Parse q_profile and rho_tor_profile if they are stored as strings (e.g., JSON-like lists)
    # Assuming they are stored as string representations of lists like "[1.0, 1.1, ...]"
    def parse_array(s):
        if isinstance(s, str):
            s = s.replace('[', '').replace(']', '').replace(' ', '')
            if not s:
                return np.array([])
            return np.array([float(x) for x in s.split(',')])
        return np.array(s)

    df['q_profile'] = df['q_profile'].apply(parse_array)
    df['rho_tor_profile'] = df['rho_tor_profile'].apply(parse_array)

    logger.info(f"Processing {len(df)} discharges for metrics calculation.")

    # Calculate resonant_surface_density
    df = process_metrics_for_discharges(
        df,
        q_profile_col='q_profile',
        rho_tor_col='rho_tor_profile'
    )

    # Detect outliers (island_width > minor_radius)
    df = detect_outliers(df)
    outlier_count = df['is_outlier'].sum()
    if outlier_count > 0:
        logger.warning(f"{outlier_count} discharges flagged as outliers (island_width > minor_radius).")
        logger.warning("These will be included in the output but flagged. Consider filtering for analysis.")

    # Validate metric ranges
    is_valid, errors = validate_metric_ranges(df)
    if not is_valid:
        logger.warning("Validation errors found in metrics:")
        for err in errors:
            logger.warning(f"  - {err}")

    # Prepare output DataFrame
    # Convert arrays back to string format for CSV storage if necessary, or keep as is if pandas handles it
    # For CSV, we need to flatten or stringify arrays. We'll stringify for safety.
    output_df = df.copy()
    output_df['q_profile'] = output_df['q_profile'].apply(lambda x: str(x.tolist()))
    output_df['rho_tor_profile'] = output_df['rho_tor_profile'].apply(lambda x: str(x.tolist()))

    # Select columns for output
    output_columns = [
        'discharge_id',
        'island_width',
        'minor_radius',
        'resonant_surface_density',
        'is_outlier',
        'q_profile',
        'rho_tor_profile'
    ]
    # Ensure all columns exist
    output_columns = [c for c in output_columns if c in output_df.columns]
    final_df = output_df[output_columns]

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving metrics to {output_path}")
    final_df.to_csv(output_path, index=False)

    logger.info(f"Successfully saved metrics for {len(final_df)} discharges to {output_path}")
    logger.info(f"Output includes: resonant_surface_density, outlier flags, and profile data.")

if __name__ == "__main__":
    main()
