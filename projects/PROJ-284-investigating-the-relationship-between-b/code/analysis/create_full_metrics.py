"""
Standalone runner for merging metrics and PCA scores (T023b) to ensure it is invoked by the run-book.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

from code.logging_config import get_logger
from code.analysis.correlations import load_metrics_data, compute_and_save_pca, merge_metrics_and_pca_scores, save_full_metrics

logger = get_logger(__name__)

def main():
    logger.log("create_full_metrics", operation="start")
    
    input_file = "data/processed/aggregated_metrics.csv"
    output_dir = "data/analysis"
    
    # Resolve input
    if not os.path.exists(input_file):
        for p in ["../" + input_file, "../../" + input_file]:
            if os.path.exists(p):
                input_file = p
                break
    
    if not os.path.exists(input_file):
        logger.log("create_full_metrics", operation="failed", reason="Input file not found")
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    try:
        # Load raw metrics
        df = load_metrics_data(input_file)
        
        # Prepare for PCA (need index as subject_id)
        if 'subject_id' in df.columns:
            df_pca = df.set_index('subject_id')
        else:
            # Assume index is subject_id
            df_pca = df
        
        # Ensure PCA outputs exist (T023a)
        # We call compute_and_save_pca to ensure files are there, even if we just merge existing ones
        # But to be safe and consistent, we re-run the logic or load existing.
        # Given T023a is a dependency, we assume the files might exist or we generate them.
        # To be robust, we generate them here if missing, or load them.
        
        scores_file = Path(output_dir) / "factor_scores.csv"
        if not scores_file.exists():
            logger.log("create_full_metrics", operation="generating_pca", reason="Scores file missing")
            # Run PCA first
            compute_and_save_pca(df_pca, output_dir)
        
        # Load scores
        scores_df = pd.read_csv(scores_file, index_col=0)
        
        # Merge
        merged = merge_metrics_and_pca_scores(df, scores_df)
        
        # Save
        output_path = Path(output_dir) / "full_metrics.csv"
        save_full_metrics(merged, str(output_path))
        
        logger.log("create_full_metrics", operation="complete", path=str(output_path))
        print(f"Full metrics created: {output_path}")
        
    except Exception as e:
        logger.log("create_full_metrics", operation="failed", error=str(e))
        print(f"Error creating full metrics: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
