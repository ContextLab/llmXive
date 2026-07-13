import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils import setup_logging, pin_random_seed

logger = logging.getLogger(__name__)

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

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_p_value_shift(base_p: float, clean_p: float) -> float:
    """Calculate absolute difference in p-values."""
    return abs(clean_p - base_p)

def analyze_size_bin(
    bin_name: str,
    datasets: List[Dict[str, Any]],
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze p-value shifts for datasets in a specific size bin.
    
    Args:
        bin_name: Name of the bin ('small', 'medium', 'large')
        datasets: List of dataset entries with size info
        baseline_metrics: Baseline analysis results
        cleaned_metrics: Cleaned analysis results
        
    Returns:
        Dictionary with bin analysis results
    """
    if not datasets:
        logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' is empty. No datasets found.")
        return {
            'bin': bin_name,
            'count': 0,
            'datasets': [],
            'avg_p_value_shift': None,
            'median_p_value_shift': None,
            'p_value_shifts': []
        }

    p_value_shifts = []
    bin_datasets = []

    for ds in datasets:
        ds_name = ds.get('dataset_name') or ds.get('name')
        if not ds_name:
            continue

        # Find corresponding baseline and cleaned entries
        base_entry = None
        clean_entry = None

        # Search in baseline metrics
        if 'datasets' in baseline_metrics:
            for b in baseline_metrics['datasets']:
                if b.get('dataset_name') == ds_name or b.get('name') == ds_name:
                    base_entry = b
                    break

        # Search in cleaned metrics
        if 'datasets' in cleaned_metrics:
            for c in cleaned_metrics['datasets']:
                if c.get('dataset_name') == ds_name or c.get('name') == ds_name:
                    clean_entry = c
                    break

        if not base_entry or not clean_entry:
            logger.warning(f"Skipping {ds_name}: Missing baseline or cleaned metrics")
            continue

        # Extract p-values (handle different structures)
        base_p = None
        clean_p = None

        if 't_test' in base_entry:
            base_p = base_entry['t_test'].get('p_value')
        elif 'p_value' in base_entry:
            base_p = base_entry['p_value']

        if 't_test' in clean_entry:
            clean_p = clean_entry['t_test'].get('p_value')
        elif 'p_value' in clean_entry:
            clean_p = clean_entry['p_value']

        if base_p is None or clean_p is None:
            logger.warning(f"Skipping {ds_name}: Missing p-value in results")
            continue

        shift = calculate_p_value_shift(base_p, clean_p)
        p_value_shifts.append(shift)
        bin_datasets.append({
            'dataset_name': ds_name,
            'base_p': base_p,
            'clean_p': clean_p,
            'shift': shift,
            'size': ds.get('dataset_size', ds.get('n_rows', 0))
        })

    if not p_value_shifts:
        logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' has no valid p-value shifts.")
        return {
            'bin': bin_name,
            'count': 0,
            'datasets': [],
            'avg_p_value_shift': None,
            'median_p_value_shift': None,
            'p_value_shifts': []
        }

    import numpy as np
    avg_shift = float(np.mean(p_value_shifts))
    median_shift = float(np.median(p_value_shifts))

    return {
        'bin': bin_name,
        'count': len(bin_datasets),
        'datasets': bin_datasets,
        'avg_p_value_shift': round(avg_shift, 6),
        'median_p_value_shift': round(median_shift, 6),
        'p_value_shifts': [round(s, 6) for s in p_value_shifts]
    }

def run_sensitivity_analysis(
    baseline_metrics_path: str,
    cleaned_metrics_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Run dataset size binning sensitivity analysis.
    
    Args:
        baseline_metrics_path: Path to baseline_metrics.json
        cleaned_metrics_path: Path to cleaned_metrics.json
        output_path: Path to write sensitivity analysis results
        
    Returns:
        Dictionary with full sensitivity analysis results
    """
    logger.info("Loading baseline metrics...")
    baseline_metrics = load_baseline_metrics(baseline_metrics_path)
    
    logger.info("Loading cleaned metrics...")
    cleaned_metrics = load_cleaned_metrics(cleaned_metrics_path)

    # Extract datasets with size information
    all_datasets = []
    if 'datasets' in baseline_metrics:
        all_datasets = baseline_metrics['datasets']
    elif 'datasets' in cleaned_metrics:
        all_datasets = cleaned_metrics['datasets']

    if not all_datasets:
        logger.warning("No datasets found in metrics files.")
        result = {
            'analysis_timestamp': datetime.now().isoformat(),
            'bins': {},
            'summary': {
                'total_datasets': 0,
                'bins_with_data': 0
            }
        }
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        return result

    # Bin datasets by size
    bins = {'small': [], 'medium': [], 'large': []}
    for ds in all_datasets:
        size = ds.get('dataset_size') or ds.get('n_rows') or 0
        bin_name = bin_dataset_size(size)
        bins[bin_name].append(ds)

    # Warn if any bin has < 1 dataset
    for bin_name, ds_list in bins.items():
        if len(ds_list) < 1:
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' has < 1 dataset (count: {len(ds_list)}).")

    # Analyze each bin
    bin_results = {}
    for bin_name, ds_list in bins.items():
        logger.info(f"Analyzing bin '{bin_name}' with {len(ds_list)} datasets...")
        bin_results[bin_name] = analyze_size_bin(
            bin_name,
            ds_list,
            baseline_metrics,
            cleaned_metrics
        )

    # Compile summary
    bins_with_data = sum(1 for b in bin_results.values() if b['count'] > 0)
    total_datasets = sum(b['count'] for b in bin_results.values())

    result = {
        'analysis_timestamp': datetime.now().isoformat(),
        'bins': bin_results,
        'summary': {
            'total_datasets': total_datasets,
            'bins_with_data': bins_with_data,
            'bin_thresholds': {
                'small': '< 50 rows',
                'medium': '50-200 rows',
                'large': '> 200 rows'
            }
        }
    }

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Sensitivity analysis written to {output_path}")
    return result

def main():
    """Main entry point for dataset size sensitivity analysis."""
    setup_logging(log_level="INFO")
    pin_random_seed(42)

    # Paths
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/sensitivity_analysis_by_size.json"

    try:
        result = run_sensitivity_analysis(baseline_path, cleaned_path, output_path)
        logger.info(f"Analysis complete. Bins with data: {result['summary']['bins_with_data']}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
