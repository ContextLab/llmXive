"""
Main entry point for the Solar Wind Geomagnetic Correlation Pipeline.
Orchestrates data fetching, alignment, threshold calculation, correlation analysis,
visualization, and reporting.
"""
import os
import sys
import json
from datetime import datetime
from argparse import ArgumentParser

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.config import (
    TRAIN_START, TRAIN_END, TEST_START, TEST_END,
    ACE_VARS, NOAA_VARS
)
from code import logger
from code.data.fetch import fetch_ace, fetch_noaa
from code.data.validate import validate_ace_raw, validate_noaa_raw
from code.data.align import run_alignment, write_synced_csv
from code.analysis.neff import calculate_neff
from code.analysis.thresholds import calculate_global_thresholds, validate_threshold_schema, write_global_thresholds
from code.analysis.correlation import load_synced_data, compute_correlations_at_lag, run_correlation_analysis
from code.viz.plots import run_viz_pipeline
from code.viz.report_generation import run_report_generation
from code.viz.report import run_validation_report

def parse_args():
    """Parse command line arguments."""
    parser = ArgumentParser(description="Solar Wind Geomagnetic Correlation Pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch raw ACE and NOAA data")
    fetch_parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    fetch_parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")

    # Align command
    align_parser = subparsers.add_parser("align", help="Align data to hourly grid and impute")
    align_parser.add_argument("--ace-path", default="data/raw/ace_raw.csv", help="Path to ACE raw CSV")
    align_parser.add_argument("--noaa-path", default="data/raw/noaa_raw.csv", help="Path to NOAA raw CSV")
    align_parser.add_argument("--output", default="data/processed/synced.csv", help="Output path for synced CSV")

    # Thresholds command
    thresh_parser = subparsers.add_parser("compute-thresholds", help="Calculate global Neff and Bonferroni thresholds")
    thresh_parser.add_argument("--data", default="data/processed/synced.csv", help="Path to synced CSV")
    thresh_parser.add_argument("--output", default="artifacts/thresholds/global_threshold.json", help="Output path for thresholds JSON")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Run lagged correlation analysis")
    analyze_parser.add_argument("--data", default="data/processed/synced.csv", help="Path to synced CSV")
    analyze_parser.add_argument("--lags", default="0,1,2,3,6", help="Comma-separated list of lags in hours")
    analyze_parser.add_argument("--output", default="artifacts/correlations.csv", help="Output path for correlation results")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Run validation on test set")
    validate_parser.add_argument("--data", default="data/processed/synced.csv", help="Path to synced CSV")
    validate_parser.add_argument("--correlations", default="artifacts/correlations.csv", help="Path to correlation results")
    validate_parser.add_argument("--thresholds", default="artifacts/thresholds/global_threshold.json", help="Path to global thresholds")
    validate_parser.add_argument("--test-start", default=f"{TEST_START}-01-01", help="Test start date")
    validate_parser.add_argument("--test-end", default=f"{TEST_END}-12-31", help="Test end date")
    validate_parser.add_argument("--report", default="artifacts/reports/validation_report.md", help="Output path for validation report")

    # Viz command
    viz_parser = subparsers.add_parser("viz", help="Generate visualizations")
    viz_parser.add_argument("--data", default="data/processed/synced.csv", help="Path to synced CSV")
    viz_parser.add_argument("--output-dir", default="artifacts/figures", help="Output directory for figures")

    # Full pipeline command
    full_parser = subparsers.add_parser("full", help="Run the entire pipeline")
    full_parser.add_argument("--start", default=f"{TRAIN_START}-01-01", help="Start date for fetch")
    full_parser.add_argument("--end", default=f"{TEST_END}-12-31", help="End date for fetch")
    full_parser.add_argument("--lags", default="0,1,2,3,6", help="Comma-separated list of lags in hours")

    return parser.parse_args()

def run_fetch(start_date: str, end_date: str):
    """Run the data fetching phase."""
    logger.info("--- Phase 1: Data Acquisition & Synchronization ---")
    logger.info(f"Fetching ACE and NOAA data...")

    try:
        # Fetch ACE data
        logger.info(f"Fetching ACE data from FTP for range {start_date} to {end_date}")
        ace_path = fetch_ace(start_date, end_date)
        logger.info(f"ACE data fetched to: {ace_path}")

        # Fetch NOAA data
        logger.info(f"Fetching NOAA data for range {start_date} to {end_date}")
        noaa_path = fetch_noaa(start_date, end_date)
        logger.info(f"NOAA data fetched to: {noaa_path}")

        # Validate raw files
        validate_ace_raw(ace_path)
        validate_noaa_raw(noaa_path)

    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        raise

def run_align(ace_path: str, noaa_path: str, output_path: str):
    """Run the data alignment phase."""
    logger.info("--- Phase 2: Data Alignment ---")
    try:
        aligned_df = run_alignment(ace_path, noaa_path)
        write_synced_csv(aligned_df, output_path)
        logger.info(f"Synced data written to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to align data: {e}")
        raise

def run_thresholds(data_path: str, output_path: str):
    """Run the global threshold calculation phase."""
    logger.info("--- Phase 3: Global Threshold Calculation ---")
    try:
        # Load synced data
        df = load_synced_data(data_path)

        # Calculate global Neff and Bonferroni thresholds
        thresholds = calculate_global_thresholds(df)

        # Validate against schema
        validate_threshold_schema(thresholds)

        # Write thresholds to file
        write_global_thresholds(thresholds, output_path)
        logger.info(f"Global thresholds written to: {output_path}")

    except Exception as e:
        logger.error(f"Failed to calculate thresholds: {e}")
        raise

def run_analyze(data_path: str, lags: list, output_path: str):
    """Run the correlation analysis phase."""
    logger.info("--- Phase 4: Lagged Correlation Analysis ---")
    try:
        # Load synced data
        df = load_synced_data(data_path)

        # Run correlation analysis
        results = run_correlation_analysis(df, lags)

        # Write results to file
        with open(output_path, 'w') as f:
            import pandas as pd
            pd.DataFrame(results).to_csv(f, index=False)
        logger.info(f"Correlation results written to: {output_path}")

    except Exception as e:
        logger.error(f"Failed to run correlation analysis: {e}")
        raise

def run_validate(data_path: str, correlations_path: str, thresholds_path: str, test_start: str, test_end: str, report_path: str):
    """Run the validation phase."""
    logger.info("--- Phase 5: Validation & Reporting ---")
    try:
        # Run validation report generation
        run_validation_report(
            data_path=data_path,
            correlations_path=correlations_path,
            thresholds_path=thresholds_path,
            test_start=test_start,
            test_end=test_end,
            report_path=report_path
        )
        logger.info(f"Validation report written to: {report_path}")

    except Exception as e:
        logger.error(f"Failed to run validation: {e}")
        raise

def run_viz(data_path: str, output_dir: str):
    """Run the visualization phase."""
    logger.info("--- Phase 6: Visualization ---")
    try:
        run_viz_pipeline(data_path, output_dir)
        logger.info(f"Visualizations written to: {output_dir}")

    except Exception as e:
        logger.error(f"Failed to run visualization: {e}")
        raise

def run_full_pipeline(start_date: str, end_date: str, lags: list):
    """Run the entire pipeline end-to-end."""
    logger.info("Pipeline started at " + datetime.now().isoformat())
    logger.info(f"Configuration: Train={TRAIN_START}-{TRAIN_END}, Test={TEST_START}-{TEST_END}")

    # Phase 1: Fetch
    run_fetch(start_date, end_date)

    # Phase 2: Align
    run_align(
        ace_path="data/raw/ace_raw.csv",
        noaa_path="data/raw/noaa_raw.csv",
        output_path="data/processed/synced.csv"
    )

    # Phase 3: Thresholds
    run_thresholds(
        data_path="data/processed/synced.csv",
        output_path="artifacts/thresholds/global_threshold.json"
    )

    # Phase 4: Analyze
    run_analyze(
        data_path="data/processed/synced.csv",
        lags=lags,
        output_path="artifacts/correlations.csv"
    )

    # Phase 5: Validate
    run_validate(
        data_path="data/processed/synced.csv",
        correlations_path="artifacts/correlations.csv",
        thresholds_path="artifacts/thresholds/global_threshold.json",
        test_start=f"{TEST_START}-01-01",
        test_end=f"{TEST_END}-12-31",
        report_path="artifacts/reports/validation_report.md"
    )

    # Phase 6: Viz
    run_viz(
        data_path="data/processed/synced.csv",
        output_dir="artifacts/figures"
    )

    logger.info("Pipeline completed successfully.")

def main():
    """Main entry point."""
    args = parse_args()

    if args.command == "fetch":
        run_fetch(args.start, args.end)
    elif args.command == "align":
        run_align(args.ace_path, args.noaa_path, args.output)
    elif args.command == "compute-thresholds":
        run_thresholds(args.data, args.output)
    elif args.command == "analyze":
        lags = [int(x) for x in args.lags.split(",")]
        run_analyze(args.data, lags, args.output)
    elif args.command == "validate":
        run_validate(args.data, args.correlations, args.thresholds, args.test_start, args.test_end, args.report)
    elif args.command == "viz":
        run_viz(args.data, args.output_dir)
    elif args.command == "full":
        lags = [int(x) for x in args.lags.split(",")]
        run_full_pipeline(args.start, args.end, lags)
    else:
        print("Please specify a command. Use --help for more information.")
        sys.exit(1)

if __name__ == "__main__":
    main()