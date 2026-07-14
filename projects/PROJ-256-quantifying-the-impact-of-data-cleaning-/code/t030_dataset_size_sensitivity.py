import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils import setup_logging, pin_random_seed
from analysis import load_datasets_from_raw

logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from a JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Baseline metrics file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics from a JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Cleaned metrics file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def bin_dataset_size(n_rows: int) -> str:
    """
    Bin dataset size into categories:
    - 'small': n < 50
    - 'medium': 50 <= n <= 200
    - 'large': n > 200
    """
    if n_rows < 50:
        return 'small'
    elif n_rows <= 200:
        return 'medium'
    else:
        return 'large'

def extract_dataset_info(metrics_entry: Dict[str, Any]) -> Tuple[str, int, str]:
    """
    Extract dataset name, row count, and size bin from a metrics entry.
    Returns (dataset_name, n_rows, size_bin).
    """
    dataset_name = metrics_entry.get('dataset_name', 'Unknown')
    n_rows = metrics_entry.get('n_rows', 0)
    size_bin = bin_dataset_size(n_rows)
    return dataset_name, n_rows, size_bin

def analyze_size_bin(
    bin_name: str,
    datasets: List[Dict[str, Any]],
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze metrics for datasets in a specific size bin.
    Computes average p-value shift, CI width change, and effect size delta.
    """
    bin_datasets = [d for d in datasets if d[2] == bin_name]
    result = {
        'bin_name': bin_name,
        'dataset_count': len(bin_datasets),
        'datasets': [],
        'aggregated_metrics': {
            'avg_p_value_shift': None,
            'avg_ci_width_change': None,
            'avg_effect_size_delta': None
        }
    }

    if len(bin_datasets) == 0:
        logger.warning(f"CONSTRAINT_VIOLATION: No datasets found in size bin '{bin_name}'.")
        return result

    p_shifts = []
    ci_changes = []
    es_deltas = []

    for dataset_name, n_rows, size_bin in bin_datasets:
        # Find corresponding baseline and cleaned entries
        baseline_entry = None
        cleaned_entry = None

        # Search in baseline metrics
        if 'datasets' in baseline_metrics:
            for entry in baseline_metrics['datasets']:
                if entry.get('dataset_name') == dataset_name:
                    baseline_entry = entry
                    break

        # Search in cleaned metrics (might be nested under strategies)
        if cleaned_metrics and 'datasets' in cleaned_metrics:
            for entry in cleaned_metrics['datasets']:
                if entry.get('dataset_name') == dataset_name:
                    cleaned_entry = entry
                    break

        if not baseline_entry:
            logger.warning(f"Missing baseline entry for dataset: {dataset_name}")
            continue

        # Calculate metrics
        baseline_p = baseline_entry.get('t_test', {}).get('p_value', 0.0)
        cleaned_p = cleaned_entry.get('t_test', {}).get('p_value', 0.0) if cleaned_entry else 0.0
        p_shift = abs(cleaned_p - baseline_p) if baseline_p and cleaned_p else 0.0

        baseline_ci_width = baseline_entry.get('t_test', {}).get('ci_width', 0.0)
        cleaned_ci_width = cleaned_entry.get('t_test', {}).get('ci_width', 0.0) if cleaned_entry else 0.0
        ci_change = abs(cleaned_ci_width - baseline_ci_width) if baseline_ci_width and cleaned_ci_width else 0.0

        baseline_es = baseline_entry.get('effect_size', {}).get('cohen_d', 0.0)
        cleaned_es = cleaned_entry.get('effect_size', {}).get('cohen_d', 0.0) if cleaned_entry else 0.0
        es_delta = abs(cleaned_es - baseline_es) if baseline_es is not None and cleaned_es is not None else 0.0

        p_shifts.append(p_shift)
        ci_changes.append(ci_change)
        es_deltas.append(es_delta)

        result['datasets'].append({
            'dataset_name': dataset_name,
            'n_rows': n_rows,
            'p_value_shift': p_shift,
            'ci_width_change': ci_change,
            'effect_size_delta': es_delta
        })

    if p_shifts:
        result['aggregated_metrics']['avg_p_value_shift'] = sum(p_shifts) / len(p_shifts)
    if ci_changes:
        result['aggregated_metrics']['avg_ci_width_change'] = sum(ci_changes) / len(ci_changes)
    if es_deltas:
        result['aggregated_metrics']['avg_effect_size_delta'] = sum(es_deltas) / len(es_deltas)

    return result

def run_sensitivity_analysis(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    output_path: str
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across dataset size bins.
    """
    logger.info("Starting dataset size binning sensitivity analysis...")
    
    all_datasets = []
    
    # Process baseline metrics
    if 'datasets' in baseline_metrics:
        for entry in baseline_metrics['datasets']:
            dataset_name, n_rows, size_bin = extract_dataset_info(entry)
            all_datasets.append((dataset_name, n_rows, size_bin))
    
    # Process cleaned metrics if available to ensure completeness
    if 'datasets' in cleaned_metrics:
        for entry in cleaned_metrics['datasets']:
            dataset_name, n_rows, size_bin = extract_dataset_info(entry)
            # Avoid duplicates
            if not any(d[0] == dataset_name for d in all_datasets):
                all_datasets.append((dataset_name, n_rows, size_bin))

    bins = ['small', 'medium', 'large']
    analysis_results = {
        'timestamp': datetime.now().isoformat(),
        'bins': {},
        'summary': {
            'total_datasets': len(all_datasets),
            'bin_distribution': {}
        }
    }

    for bin_name in bins:
        bin_result = analyze_size_bin(bin_name, all_datasets, baseline_metrics, cleaned_metrics)
        analysis_results['bins'][bin_name] = bin_result
        analysis_results['summary']['bin_distribution'][bin_name] = bin_result['dataset_count']

        # Log warning if <1 dataset per bin
        if bin_result['dataset_count'] < 1:
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' has fewer than 1 dataset.")

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    logger.info(f"Sensitivity analysis complete. Output written to: {output_path}")
    return analysis_results

def main():
    """Main entry point for T030."""
    logger = setup_logging("INFO")
    pin_random_seed(42)

    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/sensitivity_size_analysis.json"

    # Load metrics
    baseline_metrics = load_baseline_metrics(baseline_path)
    cleaned_metrics = load_cleaned_metrics(cleaned_path)

    if not baseline_metrics:
        logger.error("Cannot proceed: baseline_metrics.json is missing or empty.")
        return 1

    # Run analysis
    run_sensitivity_analysis(baseline_metrics, cleaned_metrics, output_path)

    return 0

if __name__ == "__main__":
    exit(main())