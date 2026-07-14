import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from reporting import generate_comparison_report, load_json_file, save_json_file
from utils import setup_logging

logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned metrics file not found: {filepath}")
    return load_json_file(filepath)

def main():
    """
    Execute the metrics comparison task (T027).
    Reads baseline and cleaned metrics, computes shifts, and saves the comparison report.
    """
    logger.info("Starting T027: Metrics Comparison")
    
    base_path = "data/processed/baseline_metrics.json"
    clean_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/comparison_report.json"
    
    # Check dependencies
    if not os.path.exists(base_path):
        logger.error(f"Missing baseline metrics: {base_path}. Ensure T012/T013 have run.")
        sys.exit(1)
    
    if not os.path.exists(clean_path):
        logger.error(f"Missing cleaned metrics: {clean_path}. Ensure T023 has run.")
        sys.exit(1)
    
    try:
        # Generate the full comparison report
        report = generate_comparison_report(base_path, clean_path, output_path)
        
        logger.info(f"Comparison completed. Results saved to {output_path}")
        logger.info(f"Datasets compared: {report['datasets_compared']}")
        logger.info(f"Inconsistency Rate: {report['metrics']['inconsistency_rate']}")
        
        # Also write a simplified summary if needed, but the full report covers requirements
        
    except Exception as e:
        logger.exception(f"Error during comparison: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()