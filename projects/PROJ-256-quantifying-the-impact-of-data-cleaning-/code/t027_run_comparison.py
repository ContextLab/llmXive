"""
T027: Run Comparison Script
Executes the metrics comparison logic defined in reporting.py.
"""
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path if running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reporting import generate_comparison_report, load_json_file
from utils import setup_logging

logger = logging.getLogger(__name__)

def load_baseline_metrics(path: str) -> Dict[str, Any]:
    """Helper to load baseline metrics with error handling."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Baseline metrics not found at {path}")
    return load_json_file(path)

def load_cleaned_metrics(path: str) -> Dict[str, Any]:
    """Helper to load cleaned metrics with error handling."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cleaned metrics not found at {path}")
    return load_json_file(path)

def main():
    """
    Main entry point for T027.
    Ensures artifacts exist and generates the comparison report.
    """
    setup_logging(logging.INFO)
    logger.info("Starting T027: Run Comparison Analysis")

    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/comparison_report.json"

    try:
        # Validate inputs exist before processing
        if not os.path.exists(baseline_path):
            logger.error(f"Required artifact missing: {baseline_path}")
            logger.error("Please ensure T012 (baseline analysis) has run successfully.")
            return False

        if not os.path.exists(cleaned_path):
            logger.error(f"Required artifact missing: {cleaned_path}")
            logger.error("Please ensure T023 (cleaned variant analysis) has run successfully.")
            return False

        # Run the comparison logic
        report = generate_comparison_report(baseline_path, cleaned_path, output_path)

        logger.info("T027 completed successfully.")
        logger.info(f"Comparison report written to: {output_path}")
        logger.info(f"Inconsistency Rate: {report['summary']['inconsistency_rate']}")
        return True

    except Exception as e:
        logger.error(f"Error during T027 execution: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
