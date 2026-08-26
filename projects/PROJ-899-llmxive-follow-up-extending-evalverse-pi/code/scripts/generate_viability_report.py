import os
import sys
import logging
from pathlib import Path
import pandas as pd
from src.config import get_processed_data_dir, get_data_root
from src.utils import get_logger, ensure_directories, write_csv

def load_correlation_results():
    """Load correlation results from T016."""
    csv_path = get_processed_data_dir() / "correlations.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Correlation results not found at {csv_path}")
    df = pd.read_csv(csv_path)
    required_cols = ['dimension', 'pearson_r', 'lower_ci', 'upper_ci']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in correlations.csv: {col}")
    return df

def load_adjusted_p_values():
    """Load adjusted p-values from T020 (optional)."""
    csv_path = get_processed_data_dir() / "permutation_results.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        required_cols = ['dimension', 'adjusted_p']
        if all(col in df.columns for col in required_cols):
            return df[['dimension', 'adjusted_p']].set_index('dimension')['adjusted_p'].to_dict()
    # If file doesn't exist or is missing columns, return None to indicate missing data
    return None

def load_status_from_reports():
    """Load status from T017 reports if available, otherwise compute here."""
    # T017 logic is embedded in classify_dimension_status, so we don't need a separate load here
    return None

def classify_dimension_status(pearson_r, lower_ci, upper_ci):
    """
    Classify dimension status based on T017 logic.
    - 'feature-sufficient': r >= 0.85
    - 'VLM-required': lower 95% CI < 0.70
    - 'ambiguous': otherwise
    """
    if pearson_r >= 0.85:
        return 'feature-sufficient'
    elif lower_ci < 0.70:
        return 'VLM-required'
    else:
        return 'ambiguous'

def main():
    """
    T018: Generate final dimension viability report.
    Output: data/dimension_viability.csv with columns:
    [dimension, pearson_r, lower_ci, upper_ci, status, adjusted_p]
    """
    logger = get_logger("T018_Viability_Report")
    logger.info("Starting dimension viability report generation (T018)...")

    # Ensure output directory exists
    data_root = get_data_root()
    output_path = data_root / "dimension_viability.csv"
    ensure_directories(output_path)

    # Load correlation results (from T016)
    try:
        corr_df = load_correlation_results()
        logger.info(f"Loaded {len(corr_df)} correlation results.")
    except Exception as e:
        logger.error(f"Failed to load correlation results: {e}")
        sys.exit(1)

    # Load adjusted p-values (from T020, optional)
    adjusted_p_map = load_adjusted_p_values()

    # Process each dimension
    results = []
    for _, row in corr_df.iterrows():
        dimension = row['dimension']
        pearson_r = row['pearson_r']
        lower_ci = row['lower_ci']
        upper_ci = row['upper_ci']

        # Classify status (T017 logic)
        status = classify_dimension_status(pearson_r, lower_ci, upper_ci)

        # Get adjusted p-value if available
        adjusted_p = adjusted_p_map.get(dimension, None) if adjusted_p_map else None

        results.append({
            'dimension': dimension,
            'pearson_r': pearson_r,
            'lower_ci': lower_ci,
            'upper_ci': upper_ci,
            'status': status,
            'adjusted_p': adjusted_p
        })

    # Create output DataFrame
    output_df = pd.DataFrame(results)

    # Write to CSV
    write_csv(output_df, output_path)
    logger.info(f"Successfully wrote viability report to {output_path}")
    logger.info(f"Dimensions classified: {len(output_df)}")

    # Log summary
    status_counts = output_df['status'].value_counts()
    logger.info("Status summary:")
    for status, count in status_counts.items():
        logger.info(f"  {status}: {count}")

    return 0

if __name__ == "__main__":
    sys.exit(main())