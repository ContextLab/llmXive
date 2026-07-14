"""
T030: Implement dataset size binning sensitivity analysis.

Bins datasets by size (n<50, 50-200, >200) and analyzes metric shifts per bin.
Logs warnings if bins are empty or have <1 dataset.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils import setup_logging, pin_random_seed

# Setup logging for this module
logger = logging.getLogger(__name__)

def bin_dataset_size(n_rows: int) -> str:
    """
    Assign a dataset size bin based on row count.
    Bins: 'small' (<50), 'medium' (50-200), 'large' (>200).
    """
    if n_rows < 50:
        return 'small'
    elif n_rows <= 200:
        return 'medium'
    else:
        return 'large'

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_p_value_shift(base_p: float, clean_p: float) -> float:
    """Calculate absolute difference between baseline and cleaned p-values."""
    return abs(clean_p - base_p)

def analyze_size_bin(
    datasets: List[Dict[str, Any]],
    bin_name: str,
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze a specific size bin.
    Returns summary stats for the bin.
    """
    results = {
        'bin_name': bin_name,
        'dataset_count': len(datasets),
        'datasets': [],
        'avg_p_value_shift': None,
        'avg_ci_width_change': None,
        'avg_effect_size_delta': None
    }

    if len(datasets) == 0:
        logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' is empty. No datasets to analyze.")
        return results

    p_shifts = []
    ci_changes = []
    effect_deltas = []

    for ds in datasets:
        ds_name = ds.get('dataset_name') or ds.get('name')
        n_rows = ds.get('n_rows', 0)

        # Find corresponding baseline entry
        base_entry = None
        if 'datasets' in baseline_metrics:
            for b in baseline_metrics['datasets']:
                if (b.get('dataset_name') == ds_name or b.get('name') == ds_name):
                    base_entry = b
                    break

        # Find corresponding cleaned entry (assuming first strategy or matching name)
        clean_entry = None
        if 'datasets' in cleaned_metrics:
            for c in cleaned_metrics['datasets']:
                if (c.get('dataset_name') == ds_name or c.get('name') == ds_name):
                    clean_entry = c
                    break

        if not base_entry or not clean_entry:
            logger.warning(f"Skipping {ds_name}: missing baseline or cleaned metrics.")
            continue

        # Calculate shifts
        base_p = base_entry.get('p_value')
        clean_p = clean_entry.get('p_value')
        if base_p is not None and clean_p is not None:
            p_shift = calculate_p_value_shift(base_p, clean_p)
            p_shifts.append(p_shift)

        # CI width change (example: if available in structure)
        # Assuming structure: analysis -> t_test -> ci -> [low, high]
        base_ci = base_entry.get('analysis', {}).get('t_test', {}).get('ci')
        clean_ci = clean_entry.get('analysis', {}).get('t_test', {}).get('ci')
        ci_change = 0.0
        if base_ci and clean_ci and len(base_ci) == 2 and len(clean_ci) == 2:
            base_width = base_ci[1] - base_ci[0]
            clean_width = clean_ci[1] - clean_ci[0]
            ci_change = clean_width - base_width
            ci_changes.append(ci_change)

        # Effect size delta
        base_es = base_entry.get('effect_size')
        clean_es = clean_entry.get('effect_size')
        es_delta = 0.0
        if base_es is not None and clean_es is not None:
            es_delta = clean_es - base_es
            effect_deltas.append(es_delta)

        results['datasets'].append({
            'name': ds_name,
            'n_rows': n_rows,
            'p_value_shift': p_shift if base_p is not None and clean_p is not None else None,
            'ci_width_change': ci_change if base_ci and clean_ci else None,
            'effect_size_delta': es_delta if base_es is not None and clean_es is not None else None
        })

    # Calculate averages
    if p_shifts:
        results['avg_p_value_shift'] = sum(p_shifts) / len(p_shifts)
    if ci_changes:
        results['avg_ci_width_change'] = sum(ci_changes) / len(ci_changes)
    if effect_deltas:
        results['avg_effect_size_delta'] = sum(effect_deltas) / len(effect_deltas)

    return results

def run_sensitivity_analysis(
    baseline_path: str,
    cleaned_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Run the full sensitivity analysis across dataset size bins.
    """
    pin_random_seed(42)  # Reproducibility

    logger.info(f"Loading baseline metrics from {baseline_path}")
    baseline_metrics = load_baseline_metrics(baseline_path)
    logger.info(f"Loading cleaned metrics from {cleaned_path}")
    cleaned_metrics = load_cleaned_metrics(cleaned_path)

    # Extract dataset list from baseline
    datasets = baseline_metrics.get('datasets', [])
    if not datasets:
        logger.error("No datasets found in baseline metrics. Cannot perform sensitivity analysis.")
        return {'error': 'No datasets found'}

    # Bin datasets
    bins: Dict[str, List[Dict[str, Any]]] = {'small': [], 'medium': [], 'large': []}
    for ds in datasets:
        n_rows = ds.get('n_rows', 0)
        bin_name = bin_dataset_size(n_rows)
        bins[bin_name].append(ds)

    # Warn if <1 dataset per bin
    for bin_name, bin_datasets in bins.items():
        if len(bin_datasets) < 1:
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' has <1 dataset (count={len(bin_datasets)}).")

    # Analyze each bin
    analysis_results = {
        'timestamp': datetime.now().isoformat(),
        'bins': {},
        'summary': {}
    }

    for bin_name in bins:
        logger.info(f"Analyzing bin: {bin_name} (count={len(bins[bin_name])})")
        bin_result = analyze_size_bin(bins[bin_name], bin_name, baseline_metrics, cleaned_metrics)
        analysis_results['bins'][bin_name] = bin_result

    # Generate summary
    total_datasets = len(datasets)
    analysis_results['summary'] = {
        'total_datasets': total_datasets,
        'bin_counts': {k: len(v) for k, v in bins.items()},
        'note': "Sensitivity analysis completed. Empty bins logged as CONSTRAINT_VIOLATION."
    }

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)

    logger.info(f"Sensitivity analysis complete. Output written to {output_path}")
    return analysis_results

def main():
    """Entry point for T030."""
    setup_logging(log_level="INFO")

    # Paths
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/sensitivity_analysis_size_bins.json"

    try:
        run_sensitivity_analysis(baseline_path, cleaned_path, output_path)
        logger.info("T030 completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in T030: {e}")
        raise

if __name__ == "__main__":
    main()