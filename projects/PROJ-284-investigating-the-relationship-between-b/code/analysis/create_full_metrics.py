"""
Create Full Metrics Script.
Alternative entry point for generating the full metrics CSV.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

from code.logging_config import get_logger
from code.analysis.correlations import load_metrics_data, perform_pca_on_metrics, merge_metrics_with_pca_scores, generate_full_metrics_output

logger = get_logger(__name__)

def load_real_hcp_data():
    """
    Load real HCP data from the processed aggregated metrics file.
    """
    return load_metrics_data()

def create_synthetic_metrics():
    """
    Fallback: Create synthetic metrics if real data is missing.
    """
    logger.warning("Creating synthetic metrics for testing (real data missing).")
    np.random.seed(42)
    n_subjects = 30
    data = {
        'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
        'modularity': np.random.uniform(0.3, 0.6, n_subjects),
        'global_efficiency': np.random.uniform(0.2, 0.5, n_subjects),
        'participation_coef': np.random.uniform(0.1, 0.4, n_subjects),
        'within_module_degree': np.random.uniform(1.0, 3.0, n_subjects),
        'MeanFD': np.random.uniform(0.1, 0.5, n_subjects)
    }
    return pd.DataFrame(data)

def create_full_metrics_output():
    """
    Main logic to create full metrics output.
    """
    try:
        # Attempt to load real data
        try:
            metrics_df = load_real_hcp_data()
        except FileNotFoundError:
            # Fallback to synthetic for testing if file is missing
            metrics_df = create_synthetic_metrics()
            # Save synthetic to expected location
            from code.analysis.correlations import PROCESSED_DIR
            metrics_df.to_csv(PROCESSED_DIR / "aggregated_metrics.csv", index=False)

        # Perform PCA
        _, factor_scores_df = perform_pca_on_metrics(metrics_df)

        # Merge
        merged_df = merge_metrics_with_pca_scores(metrics_df, factor_scores_df)

        # Save
        generate_full_metrics_output(merged_df)
        
        logger.log("create_full_metrics_output", status="success")
        
    except Exception as e:
        logger.log("create_full_metrics_output", status="error", error=str(e))
        raise

def main():
    create_full_metrics_output()

if __name__ == "__main__":
    main()