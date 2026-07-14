"""
Script to generate and save full_metrics.csv.
This is a standalone runner to ensure the file is produced.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.logging_config import get_logger
from code.analysis.correlations import (
    generate_full_metrics,
    save_full_metrics,
    perform_pca_on_metrics,
    AGGREGATED_METRICS_PATH,
    FULL_METRICS_PATH,
    METRIC_COLUMNS
)

logger = get_logger(__name__)

def main():
    """Main entry point for creating full metrics file."""
    logger.log("create_full_metrics_start", {})

    # Load aggregated metrics
    if not AGGREGATED_METRICS_PATH.exists():
        logger.log("aggregated_metrics_not_found", {"path": str(AGGREGATED_METRICS_PATH)})
        # Create empty file with expected schema
        df = pd.DataFrame(columns=['subject_id'] + METRIC_COLUMNS + ['motor_score', 'MeanFD'])
        df.set_index('subject_id', inplace=True)
        save_full_metrics(df)
        return

    df = pd.read_csv(AGGREGATED_METRICS_PATH)
    if 'subject_id' in df.columns:
        df.set_index('subject_id', inplace=True)

    # Perform PCA if possible
    factor_scores = None
    if len(df) > 5:
        try:
            _, factor_scores = perform_pca_on_metrics(df, METRIC_COLUMNS)
        except Exception as e:
            logger.log("pca_error", {"error": str(e)})

    # Generate full metrics
    full_df = generate_full_metrics(df, factor_scores)

    # Save to disk
    save_full_metrics(full_df)

    logger.log("create_full_metrics_complete", {
        "output_path": str(FULL_METRICS_PATH),
        "n_subjects": len(full_df),
        "n_columns": len(full_df.columns)
    })

if __name__ == "__main__":
    main()
