"""
Execution script for sensitivity analysis (T023b).
Runs the sensitivity sweep on the stratified dataset and saves the report.
"""
import sys
import argparse
import json
import logging
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.analysis.sensitivity import run_sensitivity_analysis, save_sensitivity_report
from src.analysis.stratify import stratify_dataframe
from src.utils.validation import setup_logger

def main():
    parser = argparse.ArgumentParser(description="Execute sensitivity analysis sweep.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/cleaned/merged_perovskite.csv",
        help="Path to the merged dataset (output of T015)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/sensitivity_analysis.json",
        help="Path to save the sensitivity analysis JSON report."
    )
    parser.add_argument(
        "--p-values",
        type=float,
        nargs="+",
        default=[0.01, 0.05, 0.1],
        help="List of p-value thresholds to test."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level."
    )
    args = parser.parse_args()

    # Setup logging
    logger = setup_logger("sensitivity_exec", level=args.log_level)
    logger.info(f"Starting sensitivity analysis execution for task T023b.")

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Ensure T015 (clean_merge) has completed and generated data/cleaned/merged_perovskite.csv")
        sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load and Stratify Data
        # T022 (stratify) is a prerequisite. We load the merged data and stratify it here
        # to ensure we are running the analysis on the correct stratified views.
        logger.info(f"Loading data from {input_path}...")
        df = stratify_dataframe(input_path)
        
        if df is None or df.empty:
            logger.error("Failed to load or stratify data. Exiting.")
            sys.exit(1)

        logger.info(f"Data loaded. Shape: {df.shape}. Unique chemistry classes: {df['chemistry_class'].unique().tolist()}")

        # 2. Run Sensitivity Analysis
        # The sensitivity module calculates rates based on correlation significance across p-value thresholds
        logger.info(f"Running sensitivity sweep with p-values: {args.p_values}")
        results = run_sensitivity_analysis(df, p_thresholds=args.p_values)

        # 3. Save Report
        logger.info(f"Saving results to {output_path}")
        save_sensitivity_report(results, output_path)

        logger.info("Sensitivity analysis execution completed successfully.")
        sys.exit(0)

    except Exception as e:
        logger.exception(f"An error occurred during sensitivity analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()