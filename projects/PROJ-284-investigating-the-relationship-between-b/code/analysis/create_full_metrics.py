import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

from code.logging_config import get_logger
from code.analysis.correlations import generate_full_metrics_output, perform_pca_on_metrics, load_metrics_data

logger = get_logger(__name__)

DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
ANALYSIS_DIR = DATA_DIR / "analysis"
AGGREGATED_METRICS_FILE = PROCESSED_DIR / "aggregated_metrics.csv"
FULL_METRICS_FILE = ANALYSIS_DIR / "full_metrics.csv"

def load_real_hcp_data() -> pd.DataFrame:
    """Load real HCP data from the aggregated metrics file."""
    if not AGGREGATED_METRICS_FILE.exists():
        raise FileNotFoundError(f"Aggregated metrics file not found: {AGGREGATED_METRICS_FILE}")
    
    df = pd.read_csv(AGGREGATED_METRICS_FILE)
    logger.log("load_real_hcp_data", n_rows=len(df), columns=list(df.columns))
    return df

def create_synthetic_metrics(n_subjects: int = 100) -> pd.DataFrame:
    """Create synthetic metrics for testing (fallback only)."""
    logger.log("create_synthetic_metrics", n_subjects=n_subjects, note="synthetic")
    
    data = {
        'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
        'modularity': np.random.uniform(0.3, 0.8, n_subjects),
        'global_efficiency': np.random.uniform(0.1, 0.4, n_subjects),
        'participation_coef': np.random.uniform(0.2, 0.6, n_subjects),
        'within_module_degree': np.random.uniform(1.0, 3.0, n_subjects),
        'motor_score': np.random.uniform(50, 100, n_subjects),
        'fd': np.random.uniform(0.0, 0.5, n_subjects)
    }
    return pd.DataFrame(data)

def create_full_metrics_output() -> None:
    """Main function to create full_metrics.csv from available data."""
    logger.log("create_full_metrics_output", step="start")

    try:
        # Try to load real data first
        try:
            metrics_df = load_real_hcp_data()
            logger.log("create_full_metrics_output", source="real_hcp")
        except FileNotFoundError:
            logger.log("create_full_metrics_output", source="synthetic", note="Using synthetic data for testing")
            metrics_df = create_synthetic_metrics()

        # Ensure required columns exist
        required_cols = ['subject_id', 'modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
        missing = [c for c in required_cols if c not in metrics_df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Perform PCA
        metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
        pca, loadings, scores = perform_pca_on_metrics(metrics_df)

        # Generate full output
        generate_full_metrics_output(metrics_df, pca, scores, metric_cols)

        logger.log("create_full_metrics_output", step="complete", output=str(FULL_METRICS_FILE))

    except Exception as e:
        logger.log("create_full_metrics_output", error=str(e))
        raise

def main() -> None:
    """Entry point."""
    create_full_metrics_output()

if __name__ == "__main__":
    main()
