import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from reporting import generate_comparison_report
from config import get_config

logger = logging.getLogger(__name__)

def load_baseline_metrics(file_path: str) -> List[Dict[str, Any]]:
    """Load baseline metrics from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(file_path: str) -> List[Dict[str, Any]]:
    """Load cleaned metrics from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    """Run comparison between baseline and cleaned metrics."""
    logger.info("Starting metrics comparison")
    
    config = get_config()
    baseline_file = config.get("BASELINE_OUTPUT_PATH", "data/processed/baseline_metrics.json")
    cleaned_file = config.get("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json")
    output_file = config.get("COMPARISON_OUTPUT_PATH", "data/processed/comparison_report.json")
    
    if not os.path.exists(baseline_file):
        logger.error(f"Baseline metrics file not found: {baseline_file}")
        sys.exit(1)
    
    if not os.path.exists(cleaned_file):
        logger.error(f"Cleaned metrics file not found: {cleaned_file}")
        sys.exit(1)
    
    baseline_metrics = load_baseline_metrics(baseline_file)
    cleaned_metrics = load_cleaned_metrics(cleaned_file)
    
    # Generate comparison report
    report = generate_comparison_report(baseline_metrics, cleaned_metrics)
    
    # Write report
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Wrote comparison report to {output_file}")

if __name__ == "__main__":
    main()
