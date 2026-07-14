"""
T030: Implement dataset size binning sensitivity analysis.

Bins datasets by size (n<50, 50-200, >200) and analyzes p-value shifts
within each bin. Logs warnings if bins are empty or have <1 dataset.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils import setup_logging, pin_random_seed

# Import from reporting module for utility functions
try:
    from reporting import calculate_p_value_shift
except ImportError:
    # Fallback if reporting not fully ready (should not happen in final run)
    def calculate_p_value_shift(base_p: float, clean_p: float) -> float:
        return abs(clean_p - base_p) if base_p and clean_p else 0.0

logger = logging.getLogger(__name__)

# Constants for binning
BIN_THRESHOLDS = [50, 200]  # n < 50, 50 <= n <= 200, n > 200
BIN_LABELS = ["small_n", "medium_n", "large_n"]

def bin_dataset_size(n_rows: int) -> str:
    """
    Assign a dataset to a size bin based on row count.

    Args:
        n_rows: Number of rows in the dataset.

    Returns:
        Bin label: 'small_n' (<50), 'medium_n' (50-200), 'large_n' (>200).
    """
    if n_rows < BIN_THRESHOLDS[0]:
        return BIN_LABELS[0]
    elif n_rows <= BIN_THRESHOLDS[1]:
        return BIN_LABELS[1]
    else:
        return BIN_LABELS[2]

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}")
        return {"datasets": []}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Cleaned metrics file not found: {filepath}")
        return {"datasets": []}
    with open(filepath, 'r') as f:
        return json.load(f)

def analyze_size_bin(
    bin_label: str,
    datasets: List[Dict[str, Any]],
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze p-value shifts for datasets in a specific size bin.

    Args:
        bin_label: The bin label (e.g., 'small_n').
        datasets: List of datasets belonging to this bin.
        baseline_metrics: Full baseline metrics dictionary.
        cleaned_metrics: Full cleaned metrics dictionary.

    Returns:
        Dictionary with bin analysis results.
    """
    if not datasets:
        return {
            "bin": bin_label,
            "count": 0,
            "avg_p_value_shift": None,
            "avg_ci_width_change": None,
            "avg_effect_size_delta": None,
            "datasets": []
        }

    shifts = []
    ci_changes = []
    effect_deltas = []
    dataset_details = []

    baseline_map = {d['dataset_name']: d for d in baseline_metrics.get('datasets', [])}
    cleaned_map = {d['dataset_name']: d for d in cleaned_metrics.get('datasets', [])}

    for ds in datasets:
        ds_name = ds['dataset_name']
        n_rows = ds['n_rows']
        bin_name = ds['bin']

        base_entry = baseline_map.get(ds_name)
        clean_entry = cleaned_map.get(ds_name)

        if not base_entry or not clean_entry:
            logger.warning(f"Missing metrics for {ds_name} in bin {bin_name}")
            continue

        # Extract p-values (handle multiple tests if present)
        base_tests = base_entry.get('analysis', {}).get('t_test', {})
        clean_tests = clean_entry.get('analysis', {}).get('t_test', {})

        # Calculate shifts for available tests
        for test_name in base_tests:
            base_p = base_tests[test_name].get('p_value')
            clean_p = clean_tests.get(test_name, {}).get('p_value')

            if base_p is not None and clean_p is not None:
                shift = calculate_p_value_shift(base_p, clean_p)
                shifts.append(shift)

                # CI width change (if available)
                base_ci = base_tests[test_name].get('ci', [None, None])
                clean_ci = clean_tests.get(test_name, {}).get('ci', [None, None])

                if base_ci[0] is not None and clean_ci[0] is not None:
                    base_width = base_ci[1] - base_ci[0]
                    clean_width = clean_ci[1] - clean_ci[0]
                    ci_changes.append(clean_width - base_width)

                # Effect size delta (if available)
                base_cohen = base_tests[test_name].get('cohen_d')
                clean_cohen = clean_tests.get(test_name, {}).get('cohen_d')

                if base_cohen is not None and clean_cohen is not None:
                    effect_deltas.append(abs(clean_cohen - base_cohen))

        dataset_details.append({
            "dataset_name": ds_name,
            "n_rows": n_rows,
            "p_value_shift": shifts[-1] if shifts else None
        })

    avg_shift = sum(shifts) / len(shifts) if shifts else None
    avg_ci = sum(ci_changes) / len(ci_changes) if ci_changes else None
    avg_effect = sum(effect_deltas) / len(effect_deltas) if effect_deltas else None

    return {
        "bin": bin_label,
        "count": len(datasets),
        "avg_p_value_shift": round(avg_shift, 4) if avg_shift is not None else None,
        "avg_ci_width_change": round(avg_ci, 4) if avg_ci is not None else None,
        "avg_effect_size_delta": round(avg_effect, 4) if avg_effect is not None else None,
        "datasets": dataset_details
    }

def run_sensitivity_analysis(
    baseline_path: str,
    cleaned_path: str,
    output_path: str
) -> bool:
    """
    Run the full dataset size sensitivity analysis.

    Args:
        baseline_path: Path to baseline_metrics.json.
        cleaned_path: Path to cleaned_metrics.json.
        output_path: Path to write sensitivity_analysis.json.

    Returns:
        True if successful, False otherwise.
    """
    logger.info("Starting dataset size sensitivity analysis (T030)...")
    logger.info(f"Input: {baseline_path}, {cleaned_path}")
    logger.info(f"Output: {output_path}")

    # Load metrics
    baseline_metrics = load_baseline_metrics(baseline_path)
    cleaned_metrics = load_cleaned_metrics(cleaned_path)

    if not baseline_metrics.get('datasets'):
        logger.error("No baseline datasets found. Cannot run sensitivity analysis.")
        return False

    # Bin datasets by size
    bins: Dict[str, List[Dict[str, Any]]] = {label: [] for label in BIN_LABELS}

    for ds in baseline_metrics.get('datasets', []):
        n_rows = ds.get('dataset_size', ds.get('n_rows', 0))
        bin_label = bin_dataset_size(n_rows)
        bins[bin_label].append({
            "dataset_name": ds['dataset_name'],
            "n_rows": n_rows,
            "bin": bin_label
        })

    # Log warnings for empty bins or bins with <1 dataset
    for label in BIN_LABELS:
        count = len(bins[label])
        if count == 0:
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{label}' is empty (0 datasets).")
        elif count < 1:
            # This case is logically impossible if count == 0 check exists,
            # but kept for explicit requirement satisfaction.
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{label}' has fewer than 1 dataset ({count}).")
        else:
            logger.info(f"Bin '{label}' contains {count} dataset(s).")

    # Analyze each bin
    results = []
    for label in BIN_LABELS:
        bin_result = analyze_size_bin(
            label,
            bins[label],
            baseline_metrics,
            cleaned_metrics
        )
        results.append(bin_result)
        logger.info(f"Bin {label}: n={bin_result['count']}, avg_shift={bin_result['avg_p_value_shift']}")

    # Compile final report
    report = {
        "analysis_type": "dataset_size_sensitivity",
        "timestamp": datetime.now().isoformat(),
        "bin_thresholds": BIN_THRESHOLDS,
        "bin_labels": BIN_LABELS,
        "results": results,
        "summary": {
            "total_datasets": len(baseline_metrics.get('datasets', [])),
            "bins_with_data": sum(1 for r in results if r['count'] > 0)
        }
    }

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Sensitivity analysis complete. Output written to {output_path}")
    return True

def main():
    """Main entry point for T030."""
    setup_logging("INFO")
    pin_random_seed(42)

    # Paths
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/sensitivity_analysis.json"

    success = run_sensitivity_analysis(baseline_path, cleaned_path, output_path)

    if not success:
        logger.error("T030 failed.")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())