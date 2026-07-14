"""
Runner script for PCA analysis.
Invoked by quickstart.md to produce PCA outputs.
"""
import os
import sys
import logging
from pathlib import Path

from code.analysis.correlations import load_metrics_data, run_pca_on_metrics, generate_full_metrics
from code.logging_config import get_logger
from code.analysis.correlations import load_metrics_data, run_pca_on_metrics, save_pca_results

logger = get_logger(__name__)

def main():
    """Run PCA and generate outputs."""
    logger.log("pca_runner_start")

    try:
        # Load metrics
        metrics_path = "data/processed/aggregated_metrics.csv"
        if not Path(metrics_path).exists():
            logger.log("pca_runner_error", error=f"Input file not found: {metrics_path}")
            print(f"Error: Input file not found: {metrics_path}")
            sys.exit(1)

        df = load_metrics_data(metrics_path)

        if df.empty:
            logger.log("pca_runner_error", error="No data loaded")
            sys.exit(1)

        # Run PCA
        loadings, scores = run_pca_on_metrics(df, n_components=2)

        if scores.empty:
            logger.log("pca_runner_warning", message="No PCA scores generated")
            sys.exit(0)

        # Generate full metrics
        output_path = "data/analysis/full_metrics.csv"
        merged = generate_full_metrics(df, scores, output_path)

        logger.log("pca_runner_complete", output_files=["pca_loadings.csv", "factor_scores.csv", "full_metrics.csv"])
        print(f"PCA complete. Outputs written to data/analysis/")

    except Exception as e:
        logger.log("pca_runner_error", error=str(e))
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
