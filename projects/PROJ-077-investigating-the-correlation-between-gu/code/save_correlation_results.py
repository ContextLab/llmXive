import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# Import from existing API surface
from config import ensure_directories, INPUT_PATHS, SAMPLE_LIMIT
from logging_config import get_logger, log_provenance, log_warning
from analysis import load_processed_data, compute_spearman_correlation

logger = get_logger(__name__)

def save_correlation_results(
    r_value: float,
    p_value: float,
    n_obs: int,
    output_path: Path
) -> None:
    """
    Save correlation results to a CSV file.

    Args:
        r_value: Spearman correlation coefficient
        p_value: P-value from the correlation test
        n_obs: Number of observations used in the calculation
        output_path: Path to save the CSV file
    """
    # Ensure output directory exists
    ensure_directories()

    # Create DataFrame with required schema
    results_df = pd.DataFrame([{
        'r_value': float(r_value),
        'p_value': float(p_value),
        'n_obs': int(n_obs)
    }])

    # Save to CSV
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved correlation results to {output_path}")
    log_provenance(
        action="save_correlation_results",
        details=f"Saved r={r_value:.4f}, p={p_value:.4f}, n={n_obs} to {output_path}"
    )

def run_save_correlation_pipeline() -> Tuple[float, float, int]:
    """
    Run the pipeline to compute and save correlation results.

    Returns:
        Tuple of (r_value, p_value, n_obs)
    """
    logger.info("Starting correlation results save pipeline")

    # Load processed data
    data = load_processed_data()

    if data.empty:
        raise ValueError("No data available for correlation analysis.")

    # Compute Spearman correlation between shannon_index and fluid_intelligence
    r_value, p_value, n_obs = compute_spearman_correlation(
        data,
        'shannon_index',
        'fluid_intelligence'
    )

    logger.info(f"Computed correlation: r={r_value:.4f}, p={p_value:.4f}, n={n_obs}")

    # Define output path
    output_path = Path(INPUT_PATHS['processed_output_dir']) / 'correlation_results.csv'

    # Save results
    save_correlation_results(r_value, p_value, n_obs, output_path)

    return r_value, p_value, n_obs

def main():
    """Main entry point for the correlation results save script."""
    try:
        r, p, n = run_save_correlation_pipeline()
        print(f"Successfully saved correlation results: r={r}, p={p}, n={n}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
