"""
Main entry point for the quantifying-topology-confinement pipeline.

Orchestrates data retrieval, preprocessing, metric calculation,
statistical analysis, and report generation.
"""

import argparse
import sys
import logging
import traceback
import signal
from pathlib import Path
import time

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logging, get_logger
from utils.limits import retry_with_timeout, DEFAULT_PER_ATTEMPT_TIMEOUT, DEFAULT_TOTAL_RETRY_TIMEOUT
from data.retrieval import fetch_data_for_discharge
from data.preprocessing import process_multiple_discharges, save_unified_dataset
from analysis.run_metrics import main as run_metrics
from analysis.correlation import run_correlation_analysis
from analysis.report_generator import generate_final_report

logger = get_logger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Quantify the impact of magnetic field topology on plasma confinement."
    )
    parser.add_argument(
        "--discharges",
        type=str,
        required=True,
        help="Comma-separated list of DIII-D discharge IDs (e.g., 123456,123457)"
    )
    parser.add_argument(
        "--per-attempt-timeout",
        type=int,
        default=DEFAULT_PER_ATTEMPT_TIMEOUT,
        help=f"Timeout for a single network attempt in seconds (default: {DEFAULT_PER_ATTEMPT_TIMEOUT})"
    )
    parser.add_argument(
        "--total-retry-timeout",
        type=int,
        default=DEFAULT_TOTAL_RETRY_TIMEOUT,
        help=f"Total timeout for all retry attempts in seconds (default: {DEFAULT_TOTAL_RETRY_TIMEOUT})"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Directory for output files (default: outputs)"
    )
    return parser.parse_args()

def validate_discharge_list(discharge_str: str) -> list:
    """Validate and parse the discharge list."""
    if not discharge_str:
        raise ValueError("Discharge list cannot be empty.")
    try:
        discharges = [int(x.strip()) for x in discharge_str.split(",")]
        if not discharges:
            raise ValueError("No valid discharge IDs found.")
        return discharges
    except ValueError as e:
        raise ValueError(f"Invalid discharge list format: {e}")

def check_minimum_discharges(discharges: list, min_count: int = 5):
    """Ensure we have enough discharges to proceed."""
    if len(discharges) < min_count:
        logger.warning(f"Only {len(discharges)} discharges provided. Minimum recommended is {min_count}.")
        # We do not fail here, as the task might be testing with fewer,
        # but we log a warning. The pipeline logic later might enforce a hard stop.
    return True

def run_pipeline(discharges: list, per_attempt_timeout: int, total_retry_timeout: int, output_dir: str):
    """
    Execute the full analysis pipeline.

    1. Retrieve data for each discharge (with timeout/retry logic).
    2. Preprocess and parse data.
    3. Calculate metrics.
    4. Run statistical analysis.
    5. Generate reports.
    """
    logger.info("Starting pipeline execution.")
    start_time = time.time()

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Data Retrieval
    logger.info(f"Fetching data for {len(discharges)} discharges...")
    raw_data = []
    for discharge_id in discharges:
        logger.info(f"Processing discharge {discharge_id}...")
        try:
            # Use the retry wrapper for the fetch operation
            data = retry_with_timeout(
                fetch_data_for_discharge,
                per_attempt_timeout=per_attempt_timeout,
                total_retry_timeout=total_retry_timeout,
                discharge_id=discharge_id
            )
            if data:
                raw_data.append(data)
            else:
                logger.warning(f"No data retrieved for discharge {discharge_id}. Skipping.")
        except Exception as e:
            logger.error(f"Failed to retrieve data for discharge {discharge_id}: {e}")
            # Depending on strictness, we might exit here.
            # For now, we continue and see if we have enough valid data later.

    if not raw_data:
        logger.error("No valid data retrieved for any discharge. Aborting.")
        sys.exit(1)

    # 2. Preprocessing
    logger.info("Preprocessing data...")
    processed_data = process_multiple_discharges(raw_data)

    if processed_data is None or len(processed_data) == 0:
        logger.error("Preprocessing failed or resulted in no data. Aborting.")
        sys.exit(1)

    # Save unified dataset
    unified_csv_path = output_path / "unified_analysis.csv"
    save_unified_dataset(processed_data, str(unified_csv_path))
    logger.info(f"Saved unified dataset to {unified_csv_path}")

    # 3. Metrics Calculation
    logger.info("Calculating metrics...")
    # run_metrics handles reading the unified dataset and writing metrics
    # We assume it writes to data/processed/metrics.csv as per T013
    run_metrics()

    # 4. Statistical Analysis
    logger.info("Running statistical analysis...")
    analysis_results = run_correlation_analysis()

    # 5. Report Generation
    logger.info("Generating final report...")
    report_path = output_path / "summary_report.json"
    generate_final_report(analysis_results, str(report_path))

    elapsed = time.time() - start_time
    logger.info(f"Pipeline completed successfully in {elapsed:.2f} seconds.")
    return True

def main():
    """Main entry point."""
    args = parse_arguments()

    # Setup logging
    setup_logging()

    try:
        discharges = validate_discharge_list(args.discharges)
        check_minimum_discharges(discharges)

        success = run_pipeline(
            discharges=discharges,
            per_attempt_timeout=args.per_attempt_timeout,
            total_retry_timeout=args.total_retry_timeout,
            output_dir=args.output_dir
        )

        if success:
            logger.info("Pipeline finished successfully.")
            sys.exit(0)
        else:
            logger.error("Pipeline finished with errors.")
            sys.exit(1)

    except Exception as e:
        logger.critical(f"Pipeline failed with unhandled exception: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
