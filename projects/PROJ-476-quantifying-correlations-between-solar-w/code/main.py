"""
Main entry point for the Solar Wind - Geomagnetic Correlation Pipeline.

Orchestrates the full workflow:
1. Data Acquisition & Synchronization (US1)
2. Lagged Correlation & Significance Testing (US2)
3. Visualization, Reporting & Validation (US3)
"""
import os
import sys
import json
from datetime import datetime

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.config import TRAIN_START, TRAIN_END, TEST_START, TEST_END, ACE_VARS, NOAA_VARS
from code import logger
from code.data.fetch import fetch_ace, fetch_noaa
from code.data.validate import validate_ace_raw, validate_noaa_raw
from code.data.align import run_alignment
from code.analysis.thresholds import calculate_global_thresholds, write_global_thresholds
from code.analysis.correlation import run_correlation_analysis
from code.viz.plots import run_viz_pipeline
from code.viz.report import run_validation_report


def main():
    """Execute the full research pipeline."""
    start_time = datetime.now()
    logger.info(f"Pipeline started at {start_time.isoformat()}")
    logger.info(f"Configuration: Train={TRAIN_START}-{TRAIN_END}, Test={TEST_START}-{TEST_END}")

    # ------------------------------------------------------------------
    # PHASE 1: Data Acquisition & Synchronization (US1)
    # ------------------------------------------------------------------
    logger.info("--- Phase 1: Data Acquisition & Synchronization ---")

    # 1.1 Fetch raw data
    logger.info("Fetching ACE and NOAA data...")
    try:
        ace_path = fetch_ace(TRAIN_START, TEST_END)
        noaa_path = fetch_noaa(TRAIN_START, TEST_END)
        logger.info(f"Fetched ACE data: {ace_path}")
        logger.info(f"Fetched NOAA data: {noaa_path}")
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        sys.exit(1)

    # 1.2 Validate raw data
    logger.info("Validating raw data headers...")
    try:
        validate_ace_raw(ace_path)
        validate_noaa_raw(noaa_path)
        logger.info("Raw data validation passed.")
    except ValueError as e:
        logger.error(f"Data validation failed: {e}")
        sys.exit(1)

    # 1.3 Align and synchronize
    logger.info("Aligning data to 1-hour UTC grid...")
    try:
        synced_path = run_alignment()
        logger.info(f"Alignment complete. Output: {synced_path}")
    except Exception as e:
        logger.error(f"Alignment failed: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # PHASE 2: Lagged Correlation & Significance (US2)
    # ------------------------------------------------------------------
    logger.info("--- Phase 2: Correlation Analysis & Significance ---")

    # 2.1 Calculate global thresholds (Neff, Bonferroni)
    logger.info("Calculating global significance thresholds...")
    try:
        thresholds = calculate_global_thresholds()
        threshold_path = write_global_thresholds(thresholds)
        logger.info(f"Global thresholds written to {threshold_path}")
    except Exception as e:
        logger.error(f"Threshold calculation failed: {e}")
        sys.exit(1)

    # 2.2 Run correlation analysis on full dataset
    logger.info("Running lagged correlation analysis...")
    try:
        results_path = run_correlation_analysis()
        logger.info(f"Correlation analysis complete. Output: {results_path}")
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # PHASE 3: Visualization & Validation (US3)
    # ------------------------------------------------------------------
    logger.info("--- Phase 3: Visualization & Validation Report ---")

    # 3.1 Generate visualizations
    logger.info("Generating visualizations...")
    try:
        viz_dir = run_viz_pipeline()
        logger.info(f"Visualizations generated in {viz_dir}")
    except Exception as e:
        logger.error(f"Visualization generation failed: {e}")
        sys.exit(1)

    # 3.2 Run validation report
    logger.info("Running validation report on held-out test set...")
    try:
        report_path = run_validation_report()
        logger.info(f"Validation report generated: {report_path}")
    except Exception as e:
        logger.error(f"Validation report generation failed: {e}")
        sys.exit(1)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Pipeline completed successfully in {duration:.2f} seconds.")
    logger.info(f"Start: {start_time.isoformat()}, End: {end_time.isoformat()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())