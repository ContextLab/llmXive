"""
Task T030: Implement dataset size binning sensitivity analysis.

This script performs sensitivity analysis by binning datasets based on their size
(n < 50, 50 <= n <= 200, n > 200) and analyzing metric shifts within each bin.
It logs warnings if bins contain fewer than 1 dataset and proceeds regardless.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import existing utilities and models
from utils import setup_logging, pin_random_seed
from config import get_config

# Set up logging
logger = setup_logging("INFO")

# Define size bin thresholds
BIN_THRESHOLDS = {
    "small": (0, 49),       # n < 50
    "medium": (50, 200),    # 50 <= n <= 200
    "large": (201, float('inf')) # n > 200
}

def bin_dataset_size(n: int) -> str:
    """
    Assign a dataset size n to a bin label.

    Args:
        n: Dataset size (number of rows).

    Returns:
        Bin label: 'small', 'medium', or 'large'.
    """
    if n < 50:
        return "small"
    elif n <= 200:
        return "medium"
    else:
        return "large"

def load_baseline_metrics(filepath: str) -> List[Dict[str, Any]]:
    """
    Load baseline metrics from a JSON file.

    Args:
        filepath: Path to the baseline metrics JSON file.

    Returns:
        List of metric dictionaries.
    """
    if not os.path.exists(filepath):
        logger.error(f"Baseline metrics file not found: {filepath}")
        return []

    with open(filepath, 'r') as f:
        data = json.load(f)

    # Handle both list and dict with 'results' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'results' in data:
        return data['results']
    else:
        logger.warning(f"Unexpected baseline metrics format in {filepath}")
        return []

def load_cleaned_metrics(filepath: str) -> List[Dict[str, Any]]:
    """
    Load cleaned metrics from a JSON file.

    Args:
        filepath: Path to the cleaned metrics JSON file.

    Returns:
        List of metric dictionaries.
    """
    if not os.path.exists(filepath):
        logger.error(f"Cleaned metrics file not found: {filepath}")
        return []

    with open(filepath, 'r') as f:
        data = json.load(f)

    # Handle both list and dict with 'results' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'results' in data:
        return data['results']
    else:
        logger.warning(f"Unexpected cleaned metrics format in {filepath}")
        return []

def calculate_p_value_shift(p_baseline: float, p_cleaned: float) -> float:
    """
    Calculate absolute p-value shift.

    Args:
        p_baseline: Baseline p-value.
        p_cleaned: Cleaned p-value.

    Returns:
        Absolute difference between p-values.
    """
    return abs(p_cleaned - p_baseline)

def analyze_size_bin(
    bin_label: str,
    datasets: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze a specific size bin.

    Args:
        bin_label: Label of the bin (small, medium, large).
        datasets: List of datasets in this bin with their metrics.

    Returns:
        Analysis results for the bin.
    """
    n_datasets = len(datasets)

    if n_datasets == 0:
        logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_label}' has 0 datasets.")
        return {
            "bin": bin_label,
            "dataset_count": 0,
            "datasets": [],
            "avg_p_value_shift": None,
            "avg_ci_width_change": None,
            "avg_effect_size_delta": None,
            "warning": "CONSTRAINT_VIOLATION: Empty bin"
        }

    if n_datasets < 1:
        logger.warning(f"Warning: Bin '{bin_label}' has fewer than 1 dataset (n={n_datasets}).")

    p_value_shifts = []
    ci_width_changes = []
    effect_size_deltas = []

    for ds in datasets:
        # Extract p-values
        p_baseline = ds.get('p_value_baseline')
        p_cleaned = ds.get('p_value_cleaned')

        # Extract CI widths
        ci_width_baseline = ds.get('ci_width_baseline')
        ci_width_cleaned = ds.get('ci_width_cleaned')

        # Extract effect sizes
        effect_size_baseline = ds.get('effect_size_baseline')
        effect_size_cleaned = ds.get('effect_size_cleaned')

        # Calculate shifts
        if p_baseline is not None and p_cleaned is not None:
            p_value_shifts.append(calculate_p_value_shift(p_baseline, p_cleaned))

        if ci_width_baseline is not None and ci_width_cleaned is not None:
            ci_width_changes.append(ci_width_cleaned - ci_width_baseline)

        if effect_size_baseline is not None and effect_size_cleaned is not None:
            effect_size_deltas.append(effect_size_cleaned - effect_size_baseline)

    # Calculate averages
    avg_p_shift = sum(p_value_shifts) / len(p_value_shifts) if p_value_shifts else None
    avg_ci_change = sum(ci_width_changes) / len(ci_width_changes) if ci_width_changes else None
    avg_es_delta = sum(effect_size_deltas) / len(effect_size_deltas) if effect_size_deltas else None

    return {
        "bin": bin_label,
        "dataset_count": n_datasets,
        "datasets": [ds.get('dataset_name') for ds in datasets],
        "avg_p_value_shift": round(avg_p_shift, 6) if avg_p_shift is not None else None,
        "avg_ci_width_change": round(avg_ci_change, 6) if avg_ci_change is not None else None,
        "avg_effect_size_delta": round(avg_es_delta, 6) if avg_es_delta is not None else None,
        "individual_shifts": [round(s, 6) for s in p_value_shifts]
    }

def run_sensitivity_analysis(
    baseline_metrics_path: str,
    cleaned_metrics_path: str
) -> Dict[str, Any]:
    """
    Run the full sensitivity analysis across dataset size bins.

    Args:
        baseline_metrics_path: Path to baseline metrics JSON.
        cleaned_metrics_path: Path to cleaned metrics JSON.

    Returns:
        Complete sensitivity analysis report.
    """
    logger.info("Starting dataset size binning sensitivity analysis (T030)...")

    # Load metrics
    baseline_data = load_baseline_metrics(baseline_metrics_path)
    cleaned_data = load_cleaned_metrics(cleaned_metrics_path)

    if not baseline_data:
        logger.error("No baseline metrics found. Cannot proceed.")
        return {"error": "No baseline metrics found"}

    if not cleaned_data:
        logger.error("No cleaned metrics found. Cannot proceed.")
        return {"error": "No cleaned metrics found"}

    # Create a lookup for cleaned metrics by dataset name
    cleaned_lookup = {}
    for item in cleaned_data:
        name = item.get('dataset_name')
        if name:
            cleaned_lookup[name] = item

    # Bin datasets by size
    bins: Dict[str, List[Dict[str, Any]]] = {
        "small": [],
        "medium": [],
        "large": []
    }

    for item in baseline_data:
        dataset_name = item.get('dataset_name')
        n_rows = item.get('n_rows')

        if n_rows is None:
            logger.warning(f"Dataset {dataset_name} missing n_rows, skipping binning.")
            continue

        bin_label = bin_dataset_size(n_rows)
        bins[bin_label].append(item)

    # Log bin counts
    logger.info(f"Binning results: small={len(bins['small'])}, medium={len(bins['medium'])}, large={len(bins['large'])}")

    # Analyze each bin
    bin_results = {}
    for label in ["small", "medium", "large"]:
        logger.info(f"Analyzing bin: {label} (n={len(bins[label])})")
        
        # Merge with cleaned metrics for each dataset in the bin
        enriched_datasets = []
        for ds in bins[label]:
            ds_name = ds.get('dataset_name')
            cleaned_item = cleaned_lookup.get(ds_name, {})
            
            merged = {
                **ds,
                'p_value_cleaned': cleaned_item.get('p_value'),
                'ci_width_cleaned': cleaned_item.get('ci_width'),
                'effect_size_cleaned': cleaned_item.get('effect_size')
            }
            enriched_datasets.append(merged)

        bin_results[label] = analyze_size_bin(label, enriched_datasets)

    # Generate summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "analysis_type": "dataset_size_sensitivity",
        "bin_thresholds": {
            "small": "n < 50",
            "medium": "50 <= n <= 200",
            "large": "n > 200"
        },
        "bins": bin_results,
        "total_datasets_analyzed": sum(len(bins[label]) for label in bins)
    }

    logger.info("Sensitivity analysis completed successfully.")
    return summary

def main():
    """Main entry point for T030."""
    config = get_config()
    
    # Paths
    baseline_path = config.get('OUTPUT_PATH', 'data/processed') + '/baseline_metrics.json'
    cleaned_path = config.get('OUTPUT_PATH', 'data/processed') + '/cleaned_metrics.json'
    output_path = config.get('OUTPUT_PATH', 'data/processed') + '/sensitivity_size_analysis.json'

    logger.info(f"Loading baseline metrics from: {baseline_path}")
    logger.info(f"Loading cleaned metrics from: {cleaned_path}")

    # Run analysis
    result = run_sensitivity_analysis(baseline_path, cleaned_path)

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Sensitivity analysis report written to: {output_path}")

    # Print summary
    print(f"\n=== T030 Sensitivity Analysis Summary ===")
    print(f"Total datasets: {result.get('total_datasets_analyzed', 0)}")
    for label in ["small", "medium", "large"]:
        bin_info = result.get('bins', {}).get(label, {})
        count = bin_info.get('dataset_count', 0)
        avg_shift = bin_info.get('avg_p_value_shift')
        print(f"  {label.capitalize()} (n={count}): Avg p-shift = {avg_shift}")

    return result

if __name__ == "__main__":
    main()