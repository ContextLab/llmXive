"""
T030: Implement dataset size binning sensitivity analysis.

Analyzes baseline and cleaned metrics to group datasets by size bins:
- n < 50
- 50 <= n <= 200
- n > 200

Logs warnings if bins have < 1 dataset (CONSTRAINT_VIOLATION).
Produces sensitivity analysis report.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils import setup_logging, pin_random_seed

# Configure logging for this module if not already configured
logger = logging.getLogger(__name__)

# Define size bin thresholds
BIN_THRESHOLDS = {
    "small": 50,
    "medium": 200
}
# Bins: <50, 50-200, >200

def bin_dataset_size(n_rows: int) -> str:
    """
    Assign a dataset to a size bin based on row count.

    Args:
        n_rows (int): Number of rows in the dataset.

    Returns:
        str: Bin label ('small', 'medium', 'large').
    """
    if n_rows < BIN_THRESHOLDS["small"]:
        return "small"
    elif n_rows <= BIN_THRESHOLDS["medium"]:
        return "medium"
    else:
        return "large"

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """
    Load baseline metrics from a JSON file.

    Args:
        filepath (str): Path to the baseline metrics JSON file.

    Returns:
        Dict[str, Any]: Parsed JSON content.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """
    Load cleaned metrics from a JSON file.

    Args:
        filepath (str): Path to the cleaned metrics JSON file.

    Returns:
        Dict[str, Any]: Parsed JSON content.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_p_value_shift(base_p: float, clean_p: float) -> float:
    """
    Calculate the absolute difference between baseline and cleaned p-values.

    Args:
        base_p (float): Baseline p-value.
        clean_p (float): Cleaned p-value.

    Returns:
        float: Absolute difference.
    """
    return abs(clean_p - base_p)

def analyze_size_bin(
    bin_name: str,
    datasets: List[Dict[str, Any]],
    baseline_data: List[Dict[str, Any]],
    cleaned_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze metrics for a specific size bin.

    Args:
        bin_name (str): Name of the bin.
        datasets (List[Dict]): List of dataset metadata.
        baseline_data (List[Dict]): Baseline metrics.
        cleaned_data (List[Dict]): Cleaned metrics.

    Returns:
        Dict[str, Any]: Analysis results for the bin.
    """
    if not datasets:
        return {
            "bin": bin_name,
            "count": 0,
            "datasets": [],
            "avg_p_value_shift": None,
            "avg_ci_width_change": None,
            "inconsistency_rate": None
        }

    shifts = []
    ci_changes = []
    inconsistencies = 0
    bin_datasets = []

    for ds_meta in datasets:
        ds_name = ds_meta.get("dataset_name") or ds_meta.get("name")
        if not ds_name:
            continue

        # Find corresponding baseline and cleaned entries
        base_entry = next((b for b in baseline_data if b.get("dataset_name") == ds_name), None)
        clean_entry = next((c for c in cleaned_data if c.get("dataset_name") == ds_name), None)

        if base_entry and clean_entry:
            # Extract p-values
            base_p = base_entry.get("p_value")
            clean_p = clean_entry.get("p_value")

            if base_p is not None and clean_p is not None:
                shift = calculate_p_value_shift(base_p, clean_p)
                shifts.append(shift)

                # Check for inconsistency (significance change)
                base_sig = base_p < 0.05
                clean_sig = clean_p < 0.05
                if base_sig != clean_sig:
                    inconsistencies += 1

                # CI width change (example logic, assuming structure)
                base_ci = base_entry.get("ci", {}).get("width")
                clean_ci = clean_entry.get("ci", {}).get("width")
                if base_ci and clean_ci:
                    ci_changes.append(clean_ci - base_ci)

            bin_datasets.append({
                "name": ds_name,
                "size": ds_meta.get("size"),
                "p_value_shift": shift if shifts else None,
                "inconsistent": base_sig != clean_sig if base_p is not None and clean_p is not None else None
            })

    avg_shift = sum(shifts) / len(shifts) if shifts else None
    avg_ci_change = sum(ci_changes) / len(ci_changes) if ci_changes else None
    inconsistency_rate = inconsistencies / len(datasets) if datasets else None

    return {
        "bin": bin_name,
        "count": len(datasets),
        "datasets": bin_datasets,
        "avg_p_value_shift": avg_shift,
        "avg_ci_width_change": avg_ci_change,
        "inconsistency_rate": inconsistency_rate,
        "total_inconsistencies": inconsistencies
    }

def run_sensitivity_analysis(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run the full sensitivity analysis across dataset size bins.

    Args:
        baseline_metrics (Dict): Baseline metrics data.
        cleaned_metrics (Dict): Cleaned metrics data.

    Returns:
        Dict[str, Any]: Full sensitivity analysis report.
    """
    # Extract dataset metadata (assuming structure from baseline/cleaned)
    # We need to infer size from the metrics or dataset list if available.
    # If not explicitly stored, we might need to load from data files, but for this task
    # we assume the metrics contain enough info or we iterate the available datasets.
    
    # Let's assume baseline_metrics has a 'datasets' key or similar list structure
    baseline_list = baseline_metrics.get("datasets", [])
    cleaned_list = cleaned_metrics.get("datasets", [])

    # If the structure is flat, we might need to adapt. 
    # For robustness, we'll try to extract dataset names and sizes.
    # If size is not in metrics, we cannot bin. We assume 'size' or 'n_rows' is present.
    
    # Collect all unique dataset names present in both
    all_names = set()
    for entry in baseline_list:
        name = entry.get("dataset_name") or entry.get("name")
        if name:
            all_names.add(name)

    size_bins = {"small": [], "medium": [], "large": []}

    for name in all_names:
        # Find size from baseline entry
        base_entry = next((b for b in baseline_list if b.get("dataset_name") == name), None)
        if not base_entry:
            continue
        
        # Try to find size
        size = base_entry.get("dataset_size") or base_entry.get("n_rows") or base_entry.get("size")
        
        if size is None:
            logger.warning(f"Dataset {name} has no size info, skipping binning.")
            continue

        bin_label = bin_dataset_size(size)
        size_bins[bin_label].append({
            "dataset_name": name,
            "size": size
        })

    # Log constraint violations if bins are empty
    for bin_name, ds_list in size_bins.items():
        if len(ds_list) < 1:
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' has 0 datasets. Proceeding with empty bin.")
        elif len(ds_list) < 1: # Redundant check but safe
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' has < 1 dataset.")

    results = {
        "timestamp": datetime.now().isoformat(),
        "bins": {}
    }

    for bin_name, ds_list in size_bins.items():
        bin_result = analyze_size_bin(
            bin_name,
            ds_list,
            baseline_list,
            cleaned_list
        )
        results["bins"][bin_name] = bin_result

    return results

def main():
    """
    Main entry point for T030.
    Loads metrics, runs sensitivity analysis, and saves output.
    """
    setup_logging()
    pin_random_seed(42)

    logger.info("Starting dataset size binning sensitivity analysis (T030).")

    # Define paths
    base_path = os.path.join("data", "processed", "baseline_metrics.json")
    clean_path = os.path.join("data", "processed", "cleaned_metrics.json")
    output_path = os.path.join("data", "processed", "sensitivity_analysis_size_bins.json")

    # Check if input files exist
    if not os.path.exists(base_path):
        logger.error(f"Baseline metrics not found at {base_path}. Cannot run T030.")
        return

    if not os.path.exists(clean_path):
        logger.error(f"Cleaned metrics not found at {clean_path}. Cannot run T030.")
        return

    try:
        baseline_metrics = load_baseline_metrics(base_path)
        cleaned_metrics = load_cleaned_metrics(clean_path)
    except Exception as e:
        logger.error(f"Failed to load metrics: {e}")
        return

    # Run analysis
    sensitivity_report = run_sensitivity_analysis(baseline_metrics, cleaned_metrics)

    # Write output
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(sensitivity_report, f, indent=2)
        logger.info(f"Sensitivity analysis report written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write output: {e}")
        return

    logger.info("T030 completed successfully.")

if __name__ == "__main__":
    main()