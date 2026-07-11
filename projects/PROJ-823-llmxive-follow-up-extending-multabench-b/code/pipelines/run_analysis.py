"""
Orchestrate the full statistical analysis pipeline for User Story 3.

This script executes the following sequence:
1. Validate GPU-Tuned baselines (T032a)
2. Run correlation analysis (T031, T033)
3. Run t-test analysis (T035)
4. Run FDR correction (T034)
5. Generate final correlation report (T036, T038)
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import setup_logging, get_logger, log_info, log_error, log_critical
from config import ensure_directories
from pipelines.validate_baselines import main as validate_baselines_main
from analysis.correlation import main as correlation_main
from analysis.correlation_analysis import main as correlation_analysis_main
from analysis.t_test_analysis import main as t_test_main
from analysis.fdr_correction import main as fdr_main
from pipelines.generate_correlation_report import main as report_main
from pipelines.save_conditioned_metrics import main as save_conditioned_main


def run_pipeline(args):
    """Execute the full analysis pipeline."""
    logger = get_logger(__name__)
    log_info(logger, "Starting full statistical analysis pipeline")

    # Ensure output directories exist
    ensure_directories()

    # Step 1: Validate baselines
    log_info(logger, "Step 1: Validating GPU-Tuned baselines...")
    try:
        # Prepare args for validation
        val_args = argparse.Namespace(
            baseline_csv=args.baseline_csv or str(project_root / "data" / "artifacts" / "gpu_tuned_baselines.csv"),
            gap_report=args.gap_report or str(project_root / "data" / "artifacts" / "data_availability_gap.json"),
            dataset_list=args.dataset_list or str(project_root / "data" / "datasets" / "list.json")
        )
        validate_baselines_main(val_args)
        log_info(logger, "Baseline validation completed successfully")
    except Exception as e:
        log_error(logger, f"Baseline validation failed: {e}")
        log_critical(logger, "Pipeline cannot proceed without valid baselines")
        return False

    # Step 2: Run correlation analysis
    log_info(logger, "Step 2: Running correlation analysis...")
    try:
        corr_args = argparse.Namespace(
            baseline_csv=args.baseline_csv or str(project_root / "data" / "artifacts" / "gpu_tuned_baselines.csv"),
            frozen_agg=args.frozen_agg or str(project_root / "data" / "artifacts" / "frozen_baseline_aggregated_*.json"),
            conditioned=args.conditioned or str(project_root / "data" / "artifacts" / "metrics_conditioned_*.json"),
            metadata=args.metadata or str(project_root / "data" / "processed" / "metadata_stats_summary.csv"),
            output_dir=args.output_dir or str(project_root / "data" / "artifacts")
        )
        correlation_main(corr_args)
        correlation_analysis_main(corr_args)
        log_info(logger, "Correlation analysis completed successfully")
    except Exception as e:
        log_error(logger, f"Correlation analysis failed: {e}")
        return False

    # Step 3: Run t-test analysis
    log_info(logger, "Step 3: Running t-test analysis...")
    try:
        ttest_args = argparse.Namespace(
            baseline_csv=args.baseline_csv or str(project_root / "data" / "artifacts" / "gpu_tuned_baselines.csv"),
            conditioned=args.conditioned or str(project_root / "data" / "artifacts" / "metrics_conditioned_*.json"),
            output_dir=args.output_dir or str(project_root / "data" / "artifacts")
        )
        t_test_main(ttest_args)
        log_info(logger, "T-test analysis completed successfully")
    except Exception as e:
        log_error(logger, f"T-test analysis failed: {e}")
        return False

    # Step 4: Run FDR correction
    log_info(logger, "Step 4: Running FDR correction...")
    try:
        fdr_args = argparse.Namespace(
            correlation_pvals=args.correlation_pvals or str(project_root / "data" / "artifacts" / "correlation_pvalues.json"),
            ttest_pvals=args.ttest_pvals or str(project_root / "data" / "artifacts" / "ttest_pvalues.json"),
            output_dir=args.output_dir or str(project_root / "data" / "artifacts")
        )
        fdr_main(fdr_args)
        log_info(logger, "FDR correction completed successfully")
    except Exception as e:
        log_error(logger, f"FDR correction failed: {e}")
        return False

    # Step 5: Generate final report
    log_info(logger, "Step 5: Generating final correlation report...")
    try:
        report_args = argparse.Namespace(
            fdr_pvals=args.fdr_pvals or str(project_root / "data" / "artifacts" / "fdr_adjusted_pvalues.json"),
            ttest_results=args.ttest_results or str(project_root / "data" / "artifacts" / "ttest_results.json"),
            output_file=args.output_file or str(project_root / "data" / "artifacts" / "correlation_report.json"),
            gap_report=args.gap_report or str(project_root / "data" / "artifacts" / "data_availability_gap.json")
        )
        report_main(report_args)
        log_info(logger, "Final report generation completed successfully")
    except Exception as e:
        log_error(logger, f"Report generation failed: {e}")
        return False

    log_info(logger, "Full statistical analysis pipeline completed successfully")
    return True


def main():
    parser = argparse.ArgumentParser(description="Orchestrate full statistical analysis pipeline")
    parser.add_argument("--baseline-csv", type=str, help="Path to GPU-Tuned baselines CSV")
    parser.add_argument("--gap-report", type=str, help="Path to data availability gap report")
    parser.add_argument("--dataset-list", type=str, help="Path to dataset list JSON")
    parser.add_argument("--frozen-agg", type=str, help="Path to frozen aggregated metrics JSON")
    parser.add_argument("--conditioned", type=str, help="Path to conditioned metrics JSON")
    parser.add_argument("--metadata", type=str, help="Path to metadata stats CSV")
    parser.add_argument("--correlation-pvals", type=str, help="Path to correlation p-values JSON")
    parser.add_argument("--ttest-pvals", type=str, help="Path to t-test p-values JSON")
    parser.add_argument("--fdr-pvals", type=str, help="Path to FDR-adjusted p-values JSON")
    parser.add_argument("--ttest-results", type=str, help="Path to t-test results JSON")
    parser.add_argument("--output-dir", type=str, help="Output directory for artifacts")
    parser.add_argument("--output-file", type=str, help="Path to final correlation report JSON")
    parser.add_argument("--log-file", type=str, default=None, help="Path to log file")

    args = parser.parse_args()

    # Setup logging
    if args.log_file:
        setup_logging(level="INFO", log_file=args.log_file)
    else:
        setup_logging(level="INFO")

    success = run_pipeline(args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()