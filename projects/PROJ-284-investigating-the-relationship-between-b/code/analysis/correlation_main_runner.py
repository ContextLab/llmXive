"""
Main runner for correlation analysis pipeline.
Orchestrates the full workflow: load -> PCA -> merge -> correlate -> FDR.
"""
import logging
from pathlib import Path
from code.analysis.correlations import main as _correlations_main
from code.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """
    Entry point for correlation analysis.
    """
    logger.log("correlation_main_runner_start")
    
    # Run the full correlation pipeline
    _correlations_main(
        metrics_path="data/processed/aggregated_metrics.csv",
        output_correlations="data/analysis/correlation_results.csv",
        output_fdr="data/analysis/fdr_corrected_results.csv",
        output_full_metrics="data/analysis/full_metrics.csv"
    )
    
    logger.log("correlation_main_runner_complete")

if __name__ == "__main__":
    main()