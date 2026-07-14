import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils import setup_logging
from reporting import generate_comparison_report

logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Baseline metrics file not found: {filepath}")
        return {"datasets": [], "total_datasets": 0}
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Ensure consistent structure
    if isinstance(data, list):
        return {"datasets": data, "total_datasets": len(data)}
    return data

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Cleaned metrics file not found: {filepath}")
        return {"datasets": [], "total_datasets": 0}
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Ensure consistent structure
    if isinstance(data, list):
        return {"datasets": data, "total_datasets": len(data)}
    return data

def main():
    """Main entry point for comparison analysis."""
    logger.info("Starting comparison analysis")
    
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/comparison_report.json"
    
    baseline_metrics = load_baseline_metrics(baseline_path)
    cleaned_metrics = load_cleaned_metrics(cleaned_path)
    
    if not baseline_metrics.get("datasets") and not cleaned_metrics.get("datasets"):
        logger.warning("No metrics found for comparison")
        return
    
    try:
        report = generate_comparison_report(baseline_metrics, cleaned_metrics)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Comparison report written to {output_path}")
    except Exception as e:
        logger.error(f"Comparison analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()