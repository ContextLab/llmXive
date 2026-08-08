"""
Script to generate the final summary report (T028c).
Executes aggregation and templating logic to produce results/final_report.md.
"""
import logging
import os
import sys
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.report_generator import (
    load_stability_metrics,
    load_correlation_results,
    load_permutation_results,
    aggregate_for_report,
    run_full_report_aggregation
)
from code.results_writer import write_final_report
from code.config import RESULTS_DIR
from code.utils import setup_logging

def main():
    """
    Main entry point for T028c: Generate final summary report.
    """
    # Setup logging
    logger = setup_logging("generate_final_report")
    logger.info("Starting final report generation (T028c)...")

    # Ensure results directory exists
    results_path = Path(RESULTS_DIR)
    results_path.mkdir(parents=True, exist_ok=True)

    try:
        # Load data
        logger.info("Loading stability metrics...")
        stability_df = load_stability_metrics()
        
        logger.info("Loading correlation results...")
        corr_df = load_correlation_results()
        
        logger.info("Loading permutation results...")
        perm_df = load_permutation_results()

        # Aggregate data for report
        logger.info("Aggregating data for report...")
        report_data = aggregate_for_report(stability_df, corr_df, perm_df)
        
        # Run full aggregation logic to ensure all derived metrics are present
        # This includes calculating "Achieved FDR" and ranking models
        full_report_data = run_full_report_aggregation(report_data)

        # Generate and write the report
        logger.info("Writing final report to results/final_report.md...")
        write_final_report(full_report_data, results_path / "final_report.md")

        logger.info("Final report generation completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Required data file not found: {e}")
        logger.error("Ensure previous tasks (T014, T021, T027) have been executed.")
        return 1
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
