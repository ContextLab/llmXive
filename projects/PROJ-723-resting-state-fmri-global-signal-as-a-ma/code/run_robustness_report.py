"""
Script to generate the robustness report (T031).
Executes alpha sweep, variance metric analysis, and partial correlation analysis,
then aggregates results into data/results/robustness_report.json.
"""
import os
import sys
import logging
from pathlib import Path

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories
from robustness import (
    load_cleaned_data_for_robustness,
    run_alpha_sweep,
    run_variance_metric_analysis,
    run_partial_correlation_analysis,
    generate_robustness_report
)
from utils import get_logger, write_json

def main():
    logger = get_logger("run_robustness_report")
    logger.info("Starting Robustness Report Generation (T031)")

    # Ensure output directories exist
    ensure_directories()

    # Load cleaned data
    logger.info("Loading cleaned data for robustness analysis...")
    data_path = Path("data/processed/cleaned_data.csv")
    if not data_path.exists():
        logger.error(f"Required data file not found: {data_path}")
        logger.error("Please run the ingestion pipeline (T016) first.")
        sys.exit(1)

    df = load_cleaned_data_for_robustness(data_path)
    if df is None or df.empty:
        logger.error("Failed to load valid data for robustness analysis.")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} subjects for analysis.")

    # 1. Alpha Sweep
    logger.info("Running Alpha Sweep (T028)...")
    alpha_sweep_results = run_alpha_sweep(df, logger=logger)
    
    # 2. Variance Metric Analysis
    logger.info("Running Variance Metric Analysis (T029)...")
    variance_results = run_variance_metric_analysis(df, logger=logger)

    # 3. Partial Correlation Analysis
    logger.info("Running Partial Correlation Analysis (T030)...")
    partial_corr_results = run_partial_correlation_analysis(df, logger=logger)

    # 4. Generate Final Report
    logger.info("Aggregating results into robustness_report.json...")
    report = generate_robustness_report(
        alpha_sweep_results,
        variance_results,
        partial_corr_results,
        logger=logger
    )

    # Write output
    output_path = Path("data/results/robustness_report.json")
    write_json(output_path, report)
    logger.info(f"Robustness report successfully written to {output_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
