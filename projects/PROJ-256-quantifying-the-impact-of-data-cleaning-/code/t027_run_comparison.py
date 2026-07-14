import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from reporting import load_json_file, save_json_file, generate_comparison_report

logger = logging.getLogger('llmXive')

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    logger.info(f"Loading baseline metrics from {filepath}")
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    logger.info(f"Loading cleaned metrics from {filepath}")
    return load_json_file(filepath)

def main():
    """
    Main entry point for T027: Metrics Comparison.
    Reads baseline and cleaned metrics, computes differences, and writes comparison report.
    """
    # Ensure logging is set up (in case this script is run standalone)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/comparison_report.json"

    # Check dependencies
    if not os.path.exists(baseline_path):
        logger.error(f"Dependency missing: {baseline_path}. Please run baseline analysis first.")
        sys.exit(1)
    
    if not os.path.exists(cleaned_path):
        logger.error(f"Dependency missing: {cleaned_path}. Please run cleaning and re-analysis first.")
        sys.exit(1)

    # Load data
    baseline_metrics = load_baseline_metrics(baseline_path)
    cleaned_metrics = load_cleaned_metrics(cleaned_path)

    if not baseline_metrics or not cleaned_metrics:
        logger.error("One or both metric files are empty or invalid.")
        sys.exit(1)

    # Generate report
    logger.info("Generating comparison report...")
    report = generate_comparison_report(baseline_metrics, cleaned_metrics)

    # Save report
    logger.info(f"Saving comparison report to {output_path}")
    if save_json_file(report, output_path):
        logger.info("Comparison report generated successfully.")
    else:
        logger.error("Failed to save comparison report.")
        sys.exit(1)

    # Log summary
    logger.info(f"Total comparisons: {report['metadata']['num_comparisons']}")
    logger.info(f"Median p-value shift: {report['aggregate']['median_p_shift']}")
    logger.info(f"Inconsistency rate: {report['aggregate']['inconsistency_rate']}")

if __name__ == "__main__":
    main()
