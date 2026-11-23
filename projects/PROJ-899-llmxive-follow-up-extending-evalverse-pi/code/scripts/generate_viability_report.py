import os
import sys
import logging
from pathlib import Path
import pandas as pd
from src.config import get_processed_data_dir, get_data_root
from src.utils import setup_logging, write_csv
from src.reports.generate import classify_dimension_status, load_correlation_results, load_adjusted_p_values, load_baseline_results, generate_dimension_viability_report

def load_correlation_results():
    """Load correlation results from T016c output."""
    processed_dir = get_processed_data_dir()
    path = processed_dir / "correlations.csv"
    if not path.exists():
        raise FileNotFoundError(f"Correlation results not found at {path}")
    return pd.read_csv(path)

def load_adjusted_p_values():
    """Load adjusted p-values from T020c output."""
    data_root = get_data_root()
    path = data_root / "permutation_results.csv"
    if not path.exists():
        raise FileNotFoundError(f"Permutation results not found at {path}")
    return pd.read_csv(path)

def load_status_from_reports():
    """Load dimension status from T017 output (if available) or recompute."""
    # T017 generates the status classification logic, but the final CSV is T018's job.
    # We rely on load_correlation_results to get the stats needed for classification.
    return None

def classify_dimension_status(pearson_r: float, lower_ci: float, upper_ci: float) -> str:
    """
    Classify dimension based on correlation stats.
    - feature-sufficient: lower_95ci >= 0.85
    - VLM-required: lower_95ci < 0.70
    - gray_zone: otherwise
    """
    if lower_ci >= 0.85:
        return "feature-sufficient"
    elif lower_ci < 0.70:
        return "VLM-required"
    else:
        return "gray_zone"

def main():
    """
    Generate final dimension viability report T018.
    Output: data/dimension_viability.csv
    Columns: [dimension, pearson_r, lower_ci, upper_ci, status, adjusted_p]
    """
    logger = setup_logging("T018")
    logger.info("Starting T018: Generate dimension viability report")

    try:
        # Load data from prerequisites
        corr_df = load_correlation_results()
        pval_df = load_adjusted_p_values()

        # Merge on dimension
        if 'dimension' not in corr_df.columns or 'dimension' not in pval_df.columns:
            raise ValueError("Missing 'dimension' column in input data")

        # Ensure column names match for merge
        corr_df = corr_df.rename(columns={'dimension': 'dimension'})
        pval_df = pval_df.rename(columns={'dimension': 'dimension'})

        merged = pd.merge(corr_df, pval_df[['dimension', 'adjusted_p']], on='dimension', how='left')

        # Classify status
        merged['status'] = merged.apply(
            lambda row: classify_dimension_status(row['pearson_r'], row['lower_ci'], row['upper_ci']),
            axis=1
        )

        # Select and order final columns
        final_cols = ['dimension', 'pearson_r', 'lower_ci', 'upper_ci', 'status', 'adjusted_p']
        # Handle missing adjusted_p if merge failed for some rows
        if 'adjusted_p' not in merged.columns:
            merged['adjusted_p'] = None
        
        output_df = merged[final_cols]

        # Write output
        data_root = get_data_root()
        output_path = data_root / "dimension_viability.csv"
        write_csv(output_df, output_path)

        logger.info(f"Successfully wrote {output_path}")
        logger.info(f"Dimensions classified: {output_df['status'].value_counts().to_dict()}")

        return 0

    except Exception as e:
        logger.error(f"Error generating viability report: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
