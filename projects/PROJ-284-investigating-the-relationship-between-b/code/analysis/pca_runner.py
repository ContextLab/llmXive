"""
Standalone runner for PCA task (T023a) to ensure it is invoked by the run-book.
This script loads aggregated metrics, runs PCA, and saves outputs.
"""
import os
import sys
import logging
from pathlib import Path

from code.logging_config import get_logger
from code.analysis.correlations import compute_and_save_pca, load_metrics_data

logger = get_logger(__name__)

def main():
    logger.log("pca_runner", operation="start")
    
    # Paths
    input_file = "data/processed/aggregated_metrics.csv"
    output_dir = "data/analysis"
    
    # Resolve input file if not in current dir
    if not os.path.exists(input_file):
        for p in ["../" + input_file, "../../" + input_file, "../../../" + input_file]:
            if os.path.exists(p):
                input_file = p
                break
    
    if not os.path.exists(input_file):
        logger.log("pca_runner", operation="failed", reason="Input file not found", path=input_file)
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    try:
        df = load_metrics_data(input_file)
        
        # Ensure subject_id is index for the PCA function
        if 'subject_id' in df.columns:
            df = df.set_index('subject_id')
        
        # Run PCA
        loadings, scores = compute_and_save_pca(df, output_dir)
        
        logger.log("pca_runner", operation="complete", 
                   loadings_file=f"{output_dir}/pca_loadings.csv",
                   scores_file=f"{output_dir}/factor_scores.csv")
        print(f"PCA completed. Outputs written to {output_dir}")
        
    except Exception as e:
        logger.log("pca_runner", operation="failed", error=str(e))
        print(f"Error running PCA: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
