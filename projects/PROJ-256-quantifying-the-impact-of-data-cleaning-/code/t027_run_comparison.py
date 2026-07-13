import os
import sys
import json
import logging
from datetime import datetime
from reporting import generate_comparison_report, main as reporting_main

def main():
    """
    Wrapper script for T027 to be invoked by the run-book.
    Ensures the comparison report is generated.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/comparison_report.json"

    logger.info("Executing T027: Metrics Comparison")
    
    if not os.path.exists(baseline_path):
        logger.error(f"Baseline metrics not found at {baseline_path}. Run baseline analysis first.")
        return 1
    
    if not os.path.exists(cleaned_path):
        logger.error(f"Cleaned metrics not found at {cleaned_path}. Run cleaning pipeline first.")
        return 1

    try:
        generate_comparison_report(baseline_path, cleaned_path, output_path)
        logger.info(f"Comparison report successfully written to {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate comparison report: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())