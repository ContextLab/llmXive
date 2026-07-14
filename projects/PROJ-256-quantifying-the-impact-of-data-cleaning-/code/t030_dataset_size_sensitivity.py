"""
Task T030: Implement dataset size binning sensitivity analysis.

Bins datasets by size (n<50, 50-200, >200) and analyzes metric shifts within each bin.
Logs warnings if bins are empty or have <1 dataset, but proceeds with analysis.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils import setup_logging, pin_random_seed
from config import get_config

logger = None

def load_baseline_metrics(filepath: str = None) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if filepath is None:
        config = get_config()
        filepath = os.path.join(config.PROCESSED_DATA_PATH, "baseline_metrics.json")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str = None) -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if filepath is None:
        config = get_config()
        filepath = os.path.join(config.PROCESSED_DATA_PATH, "cleaned_metrics.json")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned metrics file not found: {filepath}")
    
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

def analyze_size_bin(
    baseline_entries: List[Dict], 
    cleaned_entries: List[Dict], 
    bin_name: str
) -> Dict[str, Any]:
    """
    Analyze metrics for datasets in a specific size bin.
    Returns statistics for p-value shifts, CI width changes, and effect size deltas.
    """
    import numpy as np

    p_value_shifts = []
    ci_width_changes = []
    effect_size_deltas = []
    dataset_names = []

    # Create lookup for cleaned metrics by dataset name
    cleaned_map = {}
    for entry in cleaned_entries:
        ds_name = entry.get('dataset_name') or entry.get('dataset_id')
        if ds_name:
            cleaned_map[ds_name] = entry

    for base_entry in baseline_entries:
        ds_name = base_entry.get('dataset_name') or base_entry.get('dataset_id')
        if not ds_name:
            continue

        # Check if dataset belongs to this bin
        n_rows = base_entry.get('dataset_size', base_entry.get('n_rows', 0))
        if bin_dataset_size(n_rows) != bin_name:
            continue

        dataset_names.append(ds_name)

        # Get p-value shift
        base_p = base_entry.get('p_value')
        clean_entry = cleaned_map.get(ds_name)
        if clean_entry:
            clean_p = clean_entry.get('p_value')
            if base_p is not None and clean_p is not None and base_p > 0 and clean_p > 0:
                shift = abs(clean_p - base_p)
                p_value_shifts.append(shift)

        # Get CI width change
        base_ci = base_entry.get('ci', {})
        clean_ci = clean_entry.get('ci', {}) if clean_entry else {}
        
        base_width = None
        if base_ci and 'lower' in base_ci and 'upper' in base_ci:
            base_width = base_ci['upper'] - base_ci['lower']
        
        clean_width = None
        if clean_ci and 'lower' in clean_ci and 'upper' in clean_ci:
            clean_width = clean_ci['upper'] - clean_ci['lower']

        if base_width is not None and clean_width is not None:
            ci_change = clean_width - base_width
            ci_width_changes.append(ci_change)

        # Get effect size delta
        base_es = base_entry.get('effect_size')
        clean_es = clean_entry.get('effect_size') if clean_entry else None
        if base_es is not None and clean_es is not None:
            delta = clean_es - base_es
            effect_size_deltas.append(delta)

    result = {
        'bin': bin_name,
        'dataset_count': len(dataset_names),
        'datasets': dataset_names,
        'p_value_shifts': {
            'values': p_value_shifts,
            'mean': float(np.mean(p_value_shifts)) if p_value_shifts else None,
            'median': float(np.median(p_value_shifts)) if p_value_shifts else None,
            'std': float(np.std(p_value_shifts)) if p_value_shifts else None
        },
        'ci_width_changes': {
            'values': ci_width_changes,
            'mean': float(np.mean(ci_width_changes)) if ci_width_changes else None,
            'median': float(np.median(ci_width_changes)) if ci_width_changes else None,
            'std': float(np.std(ci_width_changes)) if ci_width_changes else None
        },
        'effect_size_deltas': {
            'values': effect_size_deltas,
            'mean': float(np.mean(effect_size_deltas)) if effect_size_deltas else None,
            'median': float(np.median(effect_size_deltas)) if effect_size_deltas else None,
            'std': float(np.std(effect_size_deltas)) if effect_size_deltas else None
        }
    }

    return result

def run_sensitivity_analysis(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    output_path: str
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across dataset size bins.
    Logs warnings if bins have < 1 dataset.
    """
    global logger
    
    bins = ['small', 'medium', 'large']
    results = []

    baseline_entries = baseline_metrics.get('datasets', [])
    cleaned_entries = cleaned_metrics.get('datasets', [])

    for bin_name in bins:
        analysis = analyze_size_bin(baseline_entries, cleaned_entries, bin_name)
        results.append(analysis)

        if analysis['dataset_count'] < 1:
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' has < 1 dataset. Proceeding with empty bin analysis.")
        elif analysis['dataset_count'] == 1:
            logger.warning(f"STATISTICAL_LIMITATION: Bin '{bin_name}' has only 1 dataset. Statistics may be unstable.")

    report = {
        'analysis_type': 'dataset_size_sensitivity',
        'timestamp': datetime.now().isoformat(),
        'bins_analyzed': bins,
        'results': results
    }

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Sensitivity analysis report written to {output_path}")
    return report

def main():
    global logger
    logger = setup_logging("T030_DATASET_SIZE_SENSITIVITY")
    logger.info("Starting dataset size sensitivity analysis (T030)")

    config = get_config()
    
    try:
        baseline_metrics = load_baseline_metrics()
        logger.info(f"Loaded baseline metrics with {len(baseline_metrics.get('datasets', []))} datasets")
    except FileNotFoundError as e:
        logger.error(f"Cannot run sensitivity analysis: {e}")
        logger.error("Ensure baseline metrics exist by running T012/T013 first.")
        return 1

    try:
        cleaned_metrics = load_cleaned_metrics()
        logger.info(f"Loaded cleaned metrics with {len(cleaned_metrics.get('datasets', []))} datasets")
    except FileNotFoundError as e:
        logger.error(f"Cannot run sensitivity analysis: {e}")
        logger.error("Ensure cleaned metrics exist by running T023 first.")
        return 1

    output_path = os.path.join(config.PROCESSED_DATA_PATH, "size_sensitivity_analysis.json")
    
    try:
        report = run_sensitivity_analysis(baseline_metrics, cleaned_metrics, output_path)
        logger.info("Dataset size sensitivity analysis completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())