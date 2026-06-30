import os
import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

from utils import setup_logging, pin_random_seed
from config import get_config

# Configure logging
logger = logging.getLogger(__name__)

def load_metrics(filepath: str) -> Dict[str, Any]:
    """Load metrics from a JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_p_value_shifts(baseline_metrics: Dict[str, Any], cleaned_metrics: Dict[str, Any]) -> List[float]:
    """
    Calculate p-value shifts between baseline and cleaned metrics.
    Returns a list of absolute differences |p_cleaned - p_baseline|.
    """
    shifts = []
    
    # Ensure both metrics have the same keys (datasets)
    baseline_datasets = set(baseline_metrics.keys())
    cleaned_datasets = set(cleaned_metrics.keys())
    
    common_datasets = baseline_datasets.intersection(cleaned_datasets)
    if not common_datasets:
        logger.warning("No common datasets between baseline and cleaned metrics.")
        return shifts
    
    for dataset_id in common_datasets:
        base_entry = baseline_metrics[dataset_id]
        clean_entry = cleaned_metrics[dataset_id]
        
        # Handle both single test results and list of test results
        base_p = base_entry.get('p_value')
        clean_p = clean_entry.get('p_value')
        
        if base_p is not None and clean_p is not None:
            shift = abs(clean_p - base_p)
            shifts.append(shift)
            logger.debug(f"Dataset {dataset_id}: p-value shift = {shift:.6f}")
        elif 'tests' in base_entry and 'tests' in clean_entry:
            # Multiple tests case
            base_tests = base_entry['tests']
            clean_tests = clean_entry['tests']
            
            for test_name in base_tests:
                if test_name in clean_tests:
                    base_p = base_tests[test_name].get('p_value')
                    clean_p = clean_tests[test_name].get('p_value')
                    if base_p is not None and clean_p is not None:
                        shift = abs(clean_p - base_p)
                        shifts.append(shift)
                        logger.debug(f"Dataset {dataset_id}, Test {test_name}: p-value shift = {shift:.6f}")
    
    return shifts

def calculate_median_and_iqr(values: List[float]) -> Dict[str, float]:
    """
    Calculate median and interquartile range (IQR) of a list of values.
    """
    if not values:
        return {"median": 0.0, "iqr": 0.0, "count": 0}
    
    arr = np.array(values)
    median = float(np.median(arr))
    q1 = float(np.percentile(arr, 25))
    q3 = float(np.percentile(arr, 75))
    iqr = q3 - q1
    
    return {
        "median": round(median, 6),
        "iqr": round(iqr, 6),
        "count": len(values),
        "min": round(float(np.min(arr)), 6),
        "max": round(float(np.max(arr)), 6)
    }

def generate_per_dataset_pvalue_shift_report(baseline_metrics_path: str, 
                                             cleaned_metrics_path: str, 
                                             output_path: str) -> Dict[str, Any]:
    """
    Generate a report with per-dataset p-value shift statistics.
    Calculates Median and IQR of p-value shifts.
    Logs a warning if n=2 (STATISTICAL_LIMITATION).
    """
    logger.info(f"Loading baseline metrics from {baseline_metrics_path}")
    baseline_metrics = load_metrics(baseline_metrics_path)
    
    logger.info(f"Loading cleaned metrics from {cleaned_metrics_path}")
    cleaned_metrics = load_metrics(cleaned_metrics_path)
    
    # Calculate all p-value shifts
    all_shifts = calculate_p_value_shifts(baseline_metrics, cleaned_metrics)
    
    # Calculate statistics
    stats = calculate_median_and_iqr(all_shifts)
    
    # Log statistical limitation warning if n=2
    if stats["count"] == 2:
        logger.warning("STATISTICAL_LIMITATION: Median/IQR calculated on n=2, results are unstable.")
    elif stats["count"] < 5:
        logger.warning(f"STATISTICAL_LIMITATION: Small sample size (n={stats['count']}) for robust median/IQR estimation.")
    
    # Build report
    report = {
        "generated_at": datetime.now().isoformat(),
        "description": "Per-dataset p-value shift reporting with Median and IQR",
        "statistics": stats,
        "raw_shifts": [round(s, 6) for s in all_shifts],
        "datasets_analyzed": stats["count"]
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write report to file
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"P-value shift report written to {output_path}")
    logger.info(f"Summary: Median={stats['median']:.6f}, IQR={stats['iqr']:.6f}, n={stats['count']}")
    
    return report

def main():
    """Main entry point for T036."""
    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(log_level)
    
    # Pin random seed for reproducibility
    seed = int(os.getenv("RANDOM_SEED", "42"))
    pin_random_seed(seed)
    
    # Get config
    config = get_config()
    
    # Define paths
    baseline_path = os.path.join("data", "processed", "baseline_metrics.json")
    cleaned_path = os.path.join("data", "processed", "cleaned_metrics.json")
    output_path = os.path.join("data", "processed", "pvalue_shift_report.json")
    
    logger.info("Starting T036: Per-dataset p-value shift reporting")
    
    try:
        report = generate_per_dataset_pvalue_shift_report(
            baseline_path, 
            cleaned_path, 
            output_path
        )
        
        logger.info("T036 completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        logger.error("Ensure baseline_metrics.json and cleaned_metrics.json exist in data/processed/")
        return 1
    except Exception as e:
        logger.exception(f"Error during p-value shift reporting: {e}")
        return 1

if __name__ == "__main__":
    exit(main())