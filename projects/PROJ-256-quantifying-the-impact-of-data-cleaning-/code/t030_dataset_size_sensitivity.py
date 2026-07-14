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
from config import Config

# Initialize logging
logger = logging.getLogger(__name__)

def bin_dataset_size(n_rows: int) -> str:
    """
    Assign a dataset size bin based on row count.

    Bins:
    - "small": n < 50
    - "medium": 50 <= n <= 200
    - "large": n > 200

    Args:
        n_rows: Number of rows in the dataset.

    Returns:
        Bin label string.
    """
    if n_rows < 50:
        return "small"
    elif n_rows <= 200:
        return "medium"
    else:
        return "large"

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Cleaned metrics file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_p_value_shift(base_p: float, clean_p: float) -> float:
    """Calculate absolute difference between baseline and cleaned p-values."""
    return abs(clean_p - base_p)

def bin_dataset_size(n_rows: int) -> str:
    """
    Bin dataset size according to thresholds:
    - n < 50: "small"
    - 50 <= n <= 200: "medium"
    - n > 200: "large"
    """
    if n_rows < 50:
        return "small"
    elif n_rows <= 200:
        return "medium"
    else:
        return "large"

def analyze_size_bin(
    bin_name: str,
    datasets: List[Dict[str, Any]],
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze metric shifts for a specific size bin.

    Args:
        bin_label: The bin label (small, medium, large).
        datasets: List of dataset entries in this bin.
        baseline_metrics: Baseline metrics dictionary.
        cleaned_metrics: Cleaned metrics dictionary.

    Returns:
        Analysis results for the bin.
    """
    results = {
        "bin": bin_label,
        "dataset_count": len(datasets),
        "datasets": [],
        "aggregate_metrics": {}
    }

    if len(datasets) == 0:
        logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_label}' is empty. No datasets to analyze.")
        return results

    for ds in datasets:
        ds_name = ds.get('dataset_name') or ds.get('name')
        if not ds_name:
            continue

        # Extract metrics for this dataset
        base_entry = None
        clean_entry = None

        # Search in baseline datasets
        if 'datasets' in baseline_metrics:
            for b in baseline_metrics['datasets']:
                if (b.get('dataset_name') == ds_name or b.get('name') == ds_name):
                    base_entry = b
                    break

        # Search in cleaned datasets
        if 'datasets' in cleaned_metrics:
            for c in cleaned_metrics['datasets']:
                if (c.get('dataset_name') == ds_name or c.get('name') == ds_name):
                    clean_entry = c
                    break

        if not base_entry or not clean_entry:
            logger.warning(f"Skipping {ds_name}: missing baseline or cleaned metrics.")
            continue

        # Calculate p-value shift
        base_p = base_entry.get('p_value')
        clean_p = clean_entry.get('p_value')
        p_shift = None
        if base_p is not None and clean_p is not None:
            p_shift = abs(clean_p - base_p)

        # Calculate CI width change
        base_ci = base_entry.get('ci_width')
        clean_ci = clean_entry.get('ci_width')
        ci_change = None
        if base_ci is not None and clean_ci is not None:
            ci_change = clean_ci - base_ci

        # Calculate effect size delta
        base_es = base_entry.get('effect_size')
        clean_es = clean_entry.get('effect_size')
        es_delta = None
        if base_es is not None and clean_es is not None:
            es_delta = clean_es - base_es

        results['datasets'].append({
            'dataset_name': ds_name,
            'n_rows': ds.get('n_rows', ds.get('dataset_size', 0)),
            'p_value_shift': p_shift,
            'ci_width_change': ci_change,
            'effect_size_delta': es_delta,
            'significance_changed': (base_p is not None and clean_p is not None and
                                     (base_p <= 0.05) != (clean_p <= 0.05))
        })

    # Aggregate metrics for the bin
    if results['datasets']:
        p_shifts = [d['p_value_shift'] for d in results['datasets'] if d['p_value_shift'] is not None]
        ci_changes = [d['ci_width_change'] for d in results['datasets'] if d['ci_width_change'] is not None]
        es_deltas = [d['effect_size_delta'] for d in results['datasets'] if d['effect_size_delta'] is not None]
        sig_changed_count = sum(1 for d in results['datasets'] if d['significance_changed'])

        results['aggregate_metrics'] = {
            'avg_p_value_shift': sum(p_shifts) / len(p_shifts) if p_shifts else None,
            'avg_ci_width_change': sum(ci_changes) / len(ci_changes) if ci_changes else None,
            'avg_effect_size_delta': sum(es_deltas) / len(es_deltas) if es_deltas else None,
            'inconsistency_rate': sig_changed_count / len(results['datasets']) if results['datasets'] else 0.0,
            'n_datasets_analyzed': len(results['datasets'])
        }

    return results

def run_sensitivity_analysis(
    baseline_filepath: str,
    cleaned_filepath: str,
    output_filepath: str,
    config: Optional[Config] = None
) -> bool:
    """
    Run the full dataset size binning sensitivity analysis.

    Args:
        baseline_filepath: Path to baseline metrics JSON.
        cleaned_filepath: Path to cleaned metrics JSON.
        output_filepath: Path to write the sensitivity analysis output.
        config: Configuration object.

    Returns:
        True if successful, False otherwise.
    """
    setup_logging("INFO")
    if config:
        pin_random_seed(config.get("RANDOM_SEED", 42))

    logger.info("Starting dataset size binning sensitivity analysis...")

    # Load metrics
    baseline_metrics = load_baseline_metrics(baseline_filepath)
    cleaned_metrics = load_cleaned_metrics(cleaned_filepath)

    if not baseline_metrics or not cleaned_metrics:
        logger.error("Could not load baseline or cleaned metrics. Aborting analysis.")
        return False

    # Group datasets by size bin
    bins: Dict[str, List[Dict[str, Any]]] = {"small": [], "medium": [], "large": []}

    # Collect datasets from baseline (assuming both have same datasets)
    datasets = baseline_metrics.get('datasets', [])

    for ds in datasets:
        n_rows = ds.get('n_rows') or ds.get('dataset_size') or 0
        if not isinstance(n_rows, (int, float)) or n_rows < 0:
            logger.warning(f"Invalid row count for dataset {ds.get('name')}: {n_rows}")
            continue

        bin_label = bin_dataset_size(int(n_rows))
        bins[bin_label].append({
            'dataset_name': ds.get('dataset_name') or ds.get('name'),
            'n_rows': n_rows
        })

    # Log bin distribution
    for label, data in bins.items():
        logger.info(f"Bin '{label}': {len(data)} datasets")
        if len(data) < 1:
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{label}' has <1 dataset. Proceeding with empty bin.")

    # Analyze each bin
    analysis_results = {
        "analysis_timestamp": datetime.now().isoformat(),
        "bin_thresholds": {
            "small": "n < 50",
            "medium": "50 <= n <= 200",
            "large": "n > 200"
        },
        "bins": {}
    }

    for label, data in bins.items():
        bin_result = analyze_size_bin(label, data, baseline_metrics, cleaned_metrics)
        analysis_results['bins'][label] = bin_result

    # Write output
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    with open(output_filepath, 'w') as f:
        json.dump(analysis_results, f, indent=2)

    logger.info(f"Sensitivity analysis complete. Output written to {output_filepath}")
    return True

def main():
    """Main entry point for the script."""
    config = Config()
    baseline_path = config.get("PROCESSED_DATA_PATH", "data/processed") + "/baseline_metrics.json"
    cleaned_path = config.get("PROCESSED_DATA_PATH", "data/processed") + "/cleaned_metrics.json"
    output_path = config.get("PROCESSED_DATA_PATH", "data/processed") + "/size_bin_sensitivity.json"

    success = run_sensitivity_analysis(baseline_path, cleaned_path, output_path, config)
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
