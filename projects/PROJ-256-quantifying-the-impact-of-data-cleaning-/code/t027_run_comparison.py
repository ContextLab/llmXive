"""
T027: Run metrics comparison and generate the comparison report.

This script loads baseline_metrics.json and cleaned_metrics.json, computes
absolute and relative differences, calculates inconsistency rates, and writes
the final comparison report to data/processed/comparison_report.json.

It relies on the functions in code/reporting.py.
"""
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reporting import (
    load_json_file,
    calculate_p_value_shift,
    compute_ci_width_change,
    compute_effect_size_delta,
    calculate_inconsistency_rate,
    generate_comparison_report
)
from config import get_config
from utils import setup_logging

# Setup logging
logger = setup_logging("T027")
logger.info("Starting T027: Metrics Comparison and Report Generation")

def load_baseline_metrics(output_path: str) -> Optional[Dict[str, Any]]:
    """Load baseline metrics from the processed directory."""
    baseline_path = os.path.join(output_path, "baseline_metrics.json")
    if not os.path.exists(baseline_path):
        logger.warning(f"Baseline metrics not found at {baseline_path}")
        return None
    return load_json_file(baseline_path)

def load_cleaned_metrics(output_path: str) -> Optional[Dict[str, Any]]:
    """Load cleaned metrics from the processed directory."""
    cleaned_path = os.path.join(output_path, "cleaned_metrics.json")
    if not os.path.exists(cleaned_path):
        logger.warning(f"Cleaned metrics not found at {cleaned_path}")
        return None
    return load_json_file(cleaned_path)

def main():
    config = get_config()
    output_path = config.get("PROCESSED_DATA_PATH", "data/processed")
    
    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)

    # Load artifacts
    logger.info(f"Loading baseline metrics from {output_path}/baseline_metrics.json")
    baseline_metrics = load_baseline_metrics(output_path)
    
    logger.info(f"Loading cleaned metrics from {output_path}/cleaned_metrics.json")
    cleaned_metrics = load_cleaned_metrics(output_path)

    if baseline_metrics is None or cleaned_metrics is None:
        logger.error("Missing required input artifacts. Cannot proceed with comparison.")
        # Create a minimal error report to satisfy the "write real output" constraint
        error_report = {
            "status": "failed",
            "reason": "Missing input artifacts (baseline_metrics.json or cleaned_metrics.json)",
            "timestamp": datetime.now().isoformat()
        }
        output_file = os.path.join(output_path, "comparison_report.json")
        with open(output_file, 'w') as f:
            json.dump(error_report, f, indent=2)
        logger.info(f"Wrote error report to {output_file}")
        return 1

    # Perform comparison
    logger.info("Calculating p-value shifts, CI width changes, and effect size deltas...")
    
    # Generate the full comparison report using the helper in reporting.py
    comparison_report = generate_comparison_report(
        baseline_metrics,
        cleaned_metrics,
        logger=logger
    )

    # Add metadata
    comparison_report["generated_at"] = datetime.now().isoformat()
    comparison_report["status"] = "completed"

    # Write output
    output_file = os.path.join(output_path, "comparison_report.json")
    logger.info(f"Writing comparison report to {output_file}")
    with open(output_file, 'w') as f:
        json.dump(comparison_report, f, indent=2)

    logger.info("T027 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
