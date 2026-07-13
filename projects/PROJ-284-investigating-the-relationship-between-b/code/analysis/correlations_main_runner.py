import os
import sys
import logging
import pandas as pd
from pathlib import Path
from config import get_config
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def main():
    """
    Runner script to execute the analysis step (PCA and Correlation) as part of the pipeline.
    This ensures the artifacts are generated when the run-book executes.
    """
    setup_logging()
    config = get_config()
    
    project_root = Path(__file__).resolve().parent.parent
    data_processed_dir = project_root / 'data' / 'processed'
    data_analysis_dir = project_root / 'data' / 'analysis'
    
    # Ensure output directory exists
    data_analysis_dir.mkdir(parents=True, exist_ok=True)
    
    # Load metrics from processed data
    # The upstream task T022 should produce a file with aggregated metrics.
    # We look for 'aggregated_metrics.csv' or similar.
    input_file = data_processed_dir / 'aggregated_metrics.csv'
    
    if not input_file.exists():
        logger.error(f"Input file {input_file} not found. Please run T021/T022 first.")
        sys.exit(1)
    
    df = pd.read_csv(input_file)
    
    # Ensure subject_id column exists
    if 'subject_id' not in df.columns:
        # Try to infer or rename
        if 'Subject' in df.columns:
            df = df.rename(columns={'Subject': 'subject_id'})
        elif 'id' in df.columns:
            df = df.rename(columns={'id': 'subject_id'})
        else:
            # If no ID, use index
            df = df.reset_index()
            df = df.rename(columns={'index': 'subject_id'})
    
    # Define metrics
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    available_cols = [c for c in metric_cols if c in df.columns]
    
    if not available_cols:
        logger.error("No metric columns found for analysis.")
        sys.exit(1)
    
    # Import and run PCA
    from analysis.correlations import run_pca_analysis, merge_metrics_and_pca_scores
    
    logger.info(f"Running PCA on columns: {available_cols}")
    loadings_df, scores_df = run_pca_analysis(
        input_df=df,
        metric_columns=available_cols,
        output_dir=data_analysis_dir,
        n_components=2
    )
    
    # Merge and save full metrics
    full_metrics_path = data_analysis_dir / 'full_metrics.csv'
    merge_metrics_and_pca_scores(df, scores_df, full_metrics_path)
    
    logger.info("Analysis complete. Artifacts saved.")

if __name__ == "__main__":
    main()