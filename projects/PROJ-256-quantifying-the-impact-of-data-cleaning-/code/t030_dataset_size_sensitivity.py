"""
Task T030: Implement dataset size binning sensitivity analysis.

Bins datasets by size:
  - n < 50
  - 50 <= n <= 200
  - n > 200

Logs warnings if < 1 dataset per bin (CONSTRAINT_VIOLATION).
Depends on baseline metrics (and cleaned metrics for shift analysis).
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Local imports from project API
from utils import setup_logging, pin_random_seed
from reporting import calculate_p_value_shift

# Constants for binning
BIN_THRESHOLDS = [50, 200]
BIN_NAMES = ["small", "medium", "large"]

logger = logging.getLogger(__name__)


def bin_dataset_size(n: int) -> str:
    """
    Assign a dataset size bin based on row count.

    Args:
        n: Number of rows in the dataset.

    Returns:
        One of 'small' (n < 50), 'medium' (50 <= n <= 200), 'large' (n > 200).
    """
    if n < BIN_THRESHOLDS[0]:
        return "small"
    elif n <= BIN_THRESHOLDS[1]:
        return "medium"
    else:
        return "large"


def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics JSON."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)


def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics JSON."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)


def calculate_p_value_shift(base_p: float, clean_p: float) -> float:
    """
    Calculate absolute p-value shift.
    Wrapper for reporting module function to ensure compatibility.
    """
    return calculate_p_value_shift(base_p, clean_p)


def analyze_size_bin(
    bin_name: str,
    datasets: List[Dict[str, Any]],
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze a specific size bin.

    Args:
        bin_name: Name of the bin ('small', 'medium', 'large').
        datasets: List of dataset entries belonging to this bin.
        baseline_metrics: Full baseline metrics structure.
        cleaned_metrics: Full cleaned metrics structure.

    Returns:
        Dictionary with analysis results for this bin.
    """
    if not datasets:
        return {
            "bin_name": bin_name,
            "count": 0,
            "avg_p_value_shift": None,
            "avg_ci_width_change": None,
            "avg_effect_size_delta": None,
            "warning": "CONSTRAINT_VIOLATION: Empty bin"
        }

    shifts = []
    ci_changes = []
    effect_deltas = []

    for ds_entry in datasets:
        ds_name = ds_entry.get('dataset_name') or ds_entry.get('name')
        if not ds_name:
            continue

        # Find corresponding baseline entry
        base_entry = None
        if 'datasets' in baseline_metrics:
            for b in baseline_metrics['datasets']:
                if b.get('dataset_name') == ds_name:
                    base_entry = b
                    break
        
        # Find corresponding cleaned entry (iterate over strategies)
        clean_entry = None
        if 'datasets' in cleaned_metrics:
            for c in cleaned_metrics['datasets']:
                if c.get('dataset_name') == ds_name:
                    clean_entry = c
                    break

        if base_entry and clean_entry:
            # Extract p-values (handle nested structure)
            base_tests = base_entry.get('analysis', {}).get('t_tests', {})
            clean_tests = clean_entry.get('analysis', {}).get('t_tests', {})
            
            # Use first available test or aggregate
            # Simplified: assume first test in dict
            if base_tests and clean_tests:
                test_key = list(base_tests.keys())[0]
                base_p = base_tests[test_key].get('p_value')
                clean_p = clean_tests[test_key].get('p_value')
                
                if base_p is not None and clean_p is not None:
                    shifts.append(calculate_p_value_shift(base_p, clean_p))

            # CI width change
            base_ci = base_entry.get('analysis', {}).get('t_tests', {}).get(test_key, {}).get('ci')
            clean_ci = clean_entry.get('analysis', {}).get('t_tests', {}).get(test_key, {}).get('ci')
            
            if base_ci and clean_ci and len(base_ci) == 2 and len(clean_ci) == 2:
                base_width = abs(base_ci[1] - base_ci[0])
                clean_width = abs(clean_ci[1] - clean_ci[0])
                ci_changes.append(clean_width - base_width)
            
            # Effect size delta
            base_eff = base_entry.get('analysis', {}).get('t_tests', {}).get(test_key, {}).get('effect_size')
            clean_eff = clean_entry.get('analysis', {}).get('t_tests', {}).get(test_key, {}).get('effect_size')
            
            if base_eff is not None and clean_eff is not None:
                effect_deltas.append(clean_eff - base_eff)

    return {
        "bin_name": bin_name,
        "count": len(datasets),
        "avg_p_value_shift": sum(shifts) / len(shifts) if shifts else None,
        "avg_ci_width_change": sum(ci_changes) / len(ci_changes) if ci_changes else None,
        "avg_effect_size_delta": sum(effect_deltas) / len(effect_deltas) if effect_deltas else None,
        "samples_analyzed": len(shifts)
    }


def run_sensitivity_analysis(
    baseline_path: str,
    cleaned_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Run full sensitivity analysis across dataset size bins.

    Args:
        baseline_path: Path to baseline_metrics.json
        cleaned_path: Path to cleaned_metrics.json
        output_path: Path to write the sensitivity analysis report.

    Returns:
        The analysis result dictionary.
    """
    logger.info(f"Loading baseline metrics from {baseline_path}")
    baseline_metrics = load_baseline_metrics(baseline_path)
    
    logger.info(f"Loading cleaned metrics from {cleaned_path}")
    cleaned_metrics = load_cleaned_metrics(cleaned_path)

    # Group datasets by size bin
    bins: Dict[str, List[Dict[str, Any]]] = {name: [] for name in BIN_NAMES}
    
    # Extract datasets from baseline metrics
  #  baseline_datasets = baseline_metrics.get('datasets', [])
    baseline_datasets = []
    if 'datasets' in baseline_metrics:
        baseline_datasets = baseline_metrics['datasets']
    
    # Process each dataset
    for ds in baseline_datasets:
        n_rows = ds.get('dataset_size') or ds.get('n_rows') or 0
        bin_name = bin_dataset_size(n_rows)
        bins[bin_name].append(ds)
        logger.debug(f"Dataset {ds.get('dataset_name')} (n={n_rows}) -> {bin_name}")

    # Check for empty bins and log warnings
    for bin_name, ds_list in bins.items():
        if len(ds_list) < 1:
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' has < 1 dataset (count: {len(ds_list)}). Proceeding with empty analysis.")
        else:
            logger.info(f"Bin '{bin_name}' contains {len(ds_list)} datasets.")

    # Analyze each bin
    results = {}
    for bin_name in BIN_NAMES:
        logger.info(f"Analyzing bin: {bin_name}")
        results[bin_name] = analyze_size_bin(
            bin_name,
            bins[bin_name],
            baseline_metrics,
            cleaned_metrics
        )

    # Aggregate summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "bin_thresholds": BIN_THRESHOLDS,
        "bin_names": BIN_NAMES,
        "bins": results,
        "total_datasets_analyzed": sum(len(bins[b]) for b in BIN_NAMES)
    }

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Sensitivity analysis written to {output_path}")
    return summary


def main():
    """Main entry point for T030 script."""
    setup_logging("INFO")
    pin_random_seed(42)

    # Paths relative to project root
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/sensitivity_analysis_size_bins.json"

    try:
        result = run_sensitivity_analysis(baseline_path, cleaned_path, output_path)
        logger.info("T030 Dataset Size Sensitivity Analysis completed successfully.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        logger.error("Ensure T012 (baseline) and T023 (cleaned) have run successfully.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during sensitivity analysis: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())