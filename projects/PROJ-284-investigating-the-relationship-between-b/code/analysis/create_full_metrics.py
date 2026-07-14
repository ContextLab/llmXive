import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

from code.logging_config import get_logger

logger = get_logger(__name__)

def load_real_hcp_data(filepath: str) -> pd.DataFrame:
    """Load real HCP data from a CSV file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    return pd.read_csv(path)

def create_synthetic_metrics(n_subjects: int = 50) -> pd.DataFrame:
    """Create synthetic metrics for testing when real data is unavailable."""
    logger.log("create_synthetic_metrics", n_subjects=n_subjects)
    data = {
        'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
        'modularity': np.random.uniform(0.3, 0.8, n_subjects),
        'global_efficiency': np.random.uniform(0.1, 0.5, n_subjects),
        'participation_coef': np.random.uniform(0.1, 0.6, n_subjects),
        'within_module_degree': np.random.uniform(0.2, 0.7, n_subjects),
        'MeanFD': np.random.uniform(0.1, 0.5, n_subjects),
        'motor_score': np.random.uniform(0, 100, n_subjects)
    }
    return pd.DataFrame(data)

def create_full_metrics_output(df: pd.DataFrame, output_path: str):
    """Save the full metrics DataFrame to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.log("create_full_metrics_output", path=str(path), rows=len(df))

def main():
    logger.log("create_full_metrics_main_start")
    try:
        # Try to load real data first
        data_path = "data/processed/aggregated_metrics.csv"
        if Path(data_path).exists():
            df = load_real_hcp_data(data_path)
        else:
            logger.log("create_full_metrics_fallback", message="Real data not found, generating synthetic.")
            df = create_synthetic_metrics()
        
        create_full_metrics_output(df, "data/analysis/full_metrics.csv")
    except Exception as e:
        logger.log("create_full_metrics_error", message=str(e))
        raise

if __name__ == "__main__":
    main()
