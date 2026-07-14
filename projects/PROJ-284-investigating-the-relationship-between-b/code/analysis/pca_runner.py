"""
Runner script for PCA analysis step.
Ensures PCA results are written to disk.
"""
import os
import sys
import logging
from pathlib import Path
from code.logging_config import get_logger
from code.analysis.correlations import (
    load_metrics_data, 
    perform_pca_on_metrics, 
    save_pca_results
)

logger = get_logger(__name__)

def main():
    base_dir = Path(os.getenv("PROJECT_ROOT", "."))
    metrics_path = base_dir / "data" / "processed" / "aggregated_metrics.csv"
    output_dir = base_dir / "data" / "analysis"
    
    if not metrics_path.exists():
        logger.error(f"Input file missing: {metrics_path}")
        sys.exit(1)
        
    logger.info(f"Loading metrics from {metrics_path}")
    df = load_metrics_data(str(metrics_path))
    
    logger.info("Running PCA...")
    loadings, scores, model = perform_pca_on_metrics(df)
    
    logger.info(f"Saving PCA results to {output_dir}")
    save_pca_results(loadings, scores, model, df, str(output_dir))
    
    logger.info("PCA step complete.")

if __name__ == "__main__":
    main()
