"""
Task T037: Implement per-dataset CI width change reporting.

Calculates Median and IQR of CI width changes across datasets.
Logs a STATISTICAL_LIMITATION warning if n=2.
Outputs per-dataset CI width change report to data/processed/ci_width_change_report.json.
"""
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

def load_json(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_ci_width_change(baseline_ci: List[float], cleaned_ci: List[float]) -> float:
    """
    Calculate the absolute change in CI width.
    CI Width = Upper Bound - Lower Bound.
    Change = Cleaned Width - Baseline Width.
    """
    if not baseline_ci or not cleaned_ci:
        return 0.0
    baseline_width = baseline_ci[1] - baseline_ci[0]
    cleaned_width = cleaned_ci[1] - cleaned_ci[0]
    return cleaned_width - baseline_width

def calculate_median_and_iqr(values: List[float]) -> Dict[str, float]:
    """
    Calculate Median and Interquartile Range (IQR) for a list of values.
    Returns a dict with 'median' and 'iqr'.
    """
    if not values:
        return {'median': 0.0, 'iqr': 0.0}
    arr = np.array(values)
    median = float(np.median(arr))
    q75 = np.percentile(arr, 75)
    q25 = np.percentile(arr, 25)
    iqr = float(q75 - q25)
    return {'median': median, 'iqr': iqr}

def load_metrics() -> Dict[str, Any]:
    """
    Load baseline and cleaned metrics from the processed data directory.
    Returns a combined structure for analysis.
    """
    config = get_config()
    baseline_path = os.path.join(config.output_path, 'baseline_metrics.json')
    cleaned_path = os.path.join(config.output_path, 'cleaned_metrics.json')

    try:
        baseline_metrics = load_json(baseline_path)
    except FileNotFoundError:
        logger.error(f"Baseline metrics not found at {baseline_path}. Run T012 first.")
        return {}

    try:
        cleaned_metrics = load_json(cleaned_path)
    except FileNotFoundError:
        logger.error(f"Cleaned metrics not found at {cleaned_path}. Run T023 first.")
        return {}

    return {
        'baseline': baseline_metrics,
        'cleaned': cleaned_metrics
    }

def generate_per_dataset_ci_width_report(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate per-dataset CI width change report.
    Calculates Median and IQR of CI width changes.
    Logs STATISTICAL_LIMITATION if n=2.
    """
    if not metrics.get('baseline') or not metrics.get('cleaned'):
        logger.warning("Insufficient metrics to generate CI width report.")
        return {}

    baseline_data = metrics['baseline'].get('datasets', [])
    cleaned_data = metrics['cleaned'].get('datasets', [])

    # Create a map for cleaned metrics by dataset name
    cleaned_map = {d['dataset_name']: d for d in cleaned_data}

    ci_width_changes = []
    per_dataset_details = []

    for b_entry in baseline_data:
        dataset_name = b_entry.get('dataset_name')
        if dataset_name not in cleaned_map:
            logger.warning(f"Dataset {dataset_name} found in baseline but not in cleaned metrics. Skipping.")
            continue

        c_entry = cleaned_map[dataset_name]

        # Extract CI values. Assuming structure: {'t_test': {'ci': [low, high]}, ...}
        # We need to aggregate CI widths across all tests in the dataset or focus on a specific one.
        # Based on T036 pattern, we aggregate across all tests for the dataset.
        
        # Helper to extract all CI widths from an analysis entry
        def get_all_ci_widths(entry: Dict) -> List[float]:
            widths = []
            # Check for t-test results
            if 't_test' in entry and isinstance(entry['t_test'], dict):
                ci = entry['t_test'].get('ci')
                if ci and len(ci) == 2:
                    width = abs(ci[1] - ci[0])
                    if np.isfinite(width):
                        widths.append(width)
            
            # Check for regression results (often has CI for coefficients)
            if 'regression' in entry and isinstance(entry['regression'], dict):
                coefs = entry['regression'].get('coefficients', [])
                if isinstance(coefs, list):
                    for coef in coefs:
                        if isinstance(coef, dict) and 'ci' in coef:
                            ci = coef['ci']
                            if ci and len(ci) == 2:
                                width = abs(ci[1] - ci[0])
                                if np.isfinite(width):
                                    widths.append(width)
            return widths

        baseline_cis = get_all_ci_widths(b_entry.get('analysis', {}))
        cleaned_cis = get_all_ci_widths(c_entry.get('analysis', {}))

        if not baseline_cis or not cleaned_cis:
            logger.warning(f"No valid CI widths found for {dataset_name}. Skipping.")
            continue

        # Calculate change for each test
        # If multiple tests, we compare the list of widths? 
        # Usually, we compare the average width or sum of widths if the number of tests matches.
        # Let's assume we calculate the change in the *average* CI width for the dataset.
        
        avg_baseline = np.mean(baseline_cis)
        avg_cleaned = np.mean(cleaned_cis)
        change = avg_cleaned - avg_baseline

        ci_width_changes.append(change)

        per_dataset_details.append({
            'dataset_name': dataset_name,
            'baseline_avg_ci_width': float(avg_baseline),
            'cleaned_avg_ci_width': float(avg_cleaned),
            'change': float(change)
        })

    if not ci_width_changes:
        logger.warning("No CI width changes calculated. Report will be empty.")
        return {
            'summary': {
                'median_change': 0.0,
                'iqr_change': 0.0,
                'n_datasets': 0
            },
            'per_dataset': []
        }

    n_datasets = len(ci_width_changes)
    stats = calculate_median_and_iqr(ci_width_changes)

    # Log statistical limitation if n=2
    if n_datasets == 2:
        logger.warning("STATISTICAL_LIMITATION: Median/IQR calculated on n=2, results are unstable.")

    return {
        'summary': {
            'median_change': stats['median'],
            'iqr_change': stats['iqr'],
            'n_datasets': n_datasets,
            'calculation_time': datetime.now().isoformat()
        },
        'per_dataset': per_dataset_details
    }

def main():
    """Main entry point for T037."""
    setup_logging(log_level='INFO')
    pin_random_seed(get_config().random_seed)

    logger.info("Starting T037: Per-dataset CI width change reporting.")

    try:
        metrics = load_metrics()
        if not metrics:
            logger.error("Failed to load metrics. Aborting.")
            return 1

        report = generate_per_dataset_ci_width_report(metrics)
        
        config = get_config()
        output_path = os.path.join(config.output_path, 'ci_width_change_report.json')
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"CI width change report saved to {output_path}")
        logger.info(f"Summary: Median Change = {report['summary']['median_change']:.4f}, IQR = {report['summary']['iqr_change']:.4f}, N = {report['summary']['n_datasets']}")
        
        return 0

    except Exception as e:
        logger.exception(f"Error during T037 execution: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
