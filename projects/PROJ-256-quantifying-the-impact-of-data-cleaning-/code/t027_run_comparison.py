import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from utils import setup_logging
from reporting import generate_comparison_report, save_json_file

logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Baseline metrics file not found: {filepath}")
        return {"datasets": []}
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            # Ensure consistent structure
            if not isinstance(data, dict):
                logger.warning("Baseline metrics format unexpected, wrapping in dict")
                return {"datasets": data if isinstance(data, list) else []}
            if "datasets" not in data:
                data["datasets"] = []
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing baseline metrics: {e}")
        return {"datasets": []}

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Cleaned metrics file not found: {filepath}")
        return {"datasets": []}
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            # Ensure consistent structure
            if not isinstance(data, dict):
                logger.warning("Cleaned metrics format unexpected, wrapping in dict")
                return {"datasets": data if isinstance(data, list) else []}
            if "datasets" not in data:
                data["datasets"] = []
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing cleaned metrics: {e}")
        return {"datasets": []}

def main():
    """Run comparison analysis between baseline and cleaned metrics."""
    logger.info("Starting comparison analysis")
    
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/comparison_report.json"
    
    baseline_metrics = load_baseline_metrics(baseline_path)
    cleaned_metrics = load_cleaned_metrics(cleaned_path)
    
    if not baseline_metrics.get("datasets") and not cleaned_metrics.get("datasets"):
        logger.warning("No metrics found to compare. Generating empty report.")
        report = {
            "generated_at": datetime.now().isoformat(),
            "baseline_datasets": 0,
            "cleaned_datasets": 0,
            "comparisons": [],
            "summary": "No data available for comparison."
        }
        save_json_file(report, output_path)
        return
    
    try:
        report = generate_comparison_report(baseline_metrics, cleaned_metrics)
        save_json_file(report, output_path)
        logger.info(f"Comparison report saved to {output_path}")
    except Exception as e:
        logger.error(f"Comparison analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
