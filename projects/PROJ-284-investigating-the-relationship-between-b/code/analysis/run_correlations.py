"""
Runner script for correlation analysis step.
"""
import os
import sys
import logging
from pathlib import Path
from code.logging_config import get_logger
from code.analysis.correlations import (
    load_metrics_data, 
    run_correlations_with_fd_covariate, 
    apply_fdr_correction, 
    save_correlation_results
)

logger = get_logger(__name__)

def main():
    base_dir = Path(os.getenv("PROJECT_ROOT", "."))
    full_metrics_path = base_dir / "data" / "analysis" / "full_metrics.csv"
    output_path = base_dir / "data" / "analysis" / "correlation_results.csv"
    
    if not full_metrics_path.exists():
        logger.error(f"Input full_metrics.csv missing: {full_metrics_path}")
        sys.exit(1)
        
    logger.info(f"Loading full metrics from {full_metrics_path}")
    df = pd.read_csv(full_metrics_path)
    
    logger.info("Running correlations with FD covariate...")
    corr_df = run_correlations_with_fd_covariate(df)
    
    if not corr_df.empty:
        logger.info("Applying FDR correction...")
        corr_df = apply_fdr_correction(corr_df)
        logger.info(f"Saving results to {output_path}")
        save_correlation_results(corr_df, str(output_path))
    else:
        logger.warning("No correlation results to save.")

if __name__ == "__main__":
    import pandas as pd
    main()