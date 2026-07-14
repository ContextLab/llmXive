import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils import setup_logging, pin_random_seed
from analysis import load_datasets_from_raw
from reporting import load_json_file, save_json_file

# Configure logging
logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}. Returning empty structure.")
        return {"datasets": []}
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Cleaned metrics file not found: {filepath}. Returning empty structure.")
        return {"datasets": []}
    return load_json_file(filepath)

def bin_dataset_size(n_rows: int) -> str:
    """
    Bin dataset size into categories:
    - 'small': n < 50
    - 'medium': 50 <= n <= 200
    - 'large': n > 200
    """
    if n_rows < 50:
        return "small"
    elif n_rows <= 200:
        return "medium"
    else:
        return "large"

def analyze_size_bin(
    datasets: List[Dict[str, Any]],
    bin_label: str,
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze metrics for a specific dataset size bin.
    Computes average p-value shift, CI width change, and effect size delta for datasets in this bin.
    """
    bin_datasets = [d for d in datasets if d.get('bin') == bin_label]
    
    result = {
        "bin": bin_label,
        "dataset_count": len(bin_datasets),
        "datasets": [],
        "aggregate_stats": {
            "avg_p_value_shift": None,
            "avg_ci_width_change": None,
            "avg_effect_size_delta": None
        }
    }

    if len(bin_datasets) == 0:
        logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_label}' is empty. Proceeding with empty stats.")
        return result

    p_value_shifts = []
    ci_width_changes = []
    effect_size_deltas = []

    baseline_map = {d['dataset_name']: d for d in baseline_metrics.get('datasets', [])}
    cleaned_map = {d['dataset_name']: d for d in cleaned_metrics.get('datasets', [])}

    for d in bin_datasets:
        dataset_name = d['dataset_name']
        n_rows = d['dataset_size']
        
        baseline_entry = baseline_map.get(dataset_name)
        cleaned_entry = cleaned_map.get(dataset_name)

        if not baseline_entry or not cleaned_entry:
            logger.warning(f"Skipping {dataset_name}: missing baseline or cleaned metrics.")
            continue

        # Extract metrics (handling nested structures)
        b_tests = baseline_entry.get('analysis', {}).get('t_test', {})
        c_tests = cleaned_entry.get('analysis', {}).get('t_test', {})
        
        b_p = b_tests.get('p_value')
        c_p = c_tests.get('p_value')
        
        b_ci = b_tests.get('ci')
        c_ci = c_tests.get('ci')
        
        b_eff = b_tests.get('effect_size')
        c_eff = c_tests.get('effect_size')

        # Calculate shifts
        p_shift = abs(c_p - b_p) if (b_p is not None and c_p is not None) else None
        ci_b_width = b_ci[1] - b_ci[0] if (b_ci and len(b_ci) == 2) else None
        ci_c_width = c_ci[1] - c_ci[0] if (c_ci and len(c_ci) == 2) else None
        ci_change = ci_c_width - ci_b_width if (ci_b_width is not None and ci_c_width is not None) else None
        eff_delta = c_eff - b_eff if (b_eff is not None and c_eff is not None) else None

        p_value_shifts.append(p_shift)
        if ci_change is not None:
            ci_width_changes.append(ci_change)
        if eff_delta is not None:
            effect_size_deltas.append(eff_delta)

        result["datasets"].append({
            "dataset_name": dataset_name,
            "size": n_rows,
            "p_value_shift": p_shift,
            "ci_width_change": ci_change,
            "effect_size_delta": eff_delta
        })

    # Calculate aggregates
    import numpy as np
    if p_value_shifts:
        result["aggregate_stats"]["avg_p_value_shift"] = float(np.mean([x for x in p_value_shifts if x is not None]))
    if ci_width_changes:
        result["aggregate_stats"]["avg_ci_width_change"] = float(np.mean(ci_width_changes))
    if effect_size_deltas:
        result["aggregate_stats"]["avg_effect_size_delta"] = float(np.mean(effect_size_deltas))

    return result

def run_sensitivity_analysis(
    baseline_filepath: str = "data/processed/baseline_metrics.json",
    cleaned_filepath: str = "data/processed/cleaned_metrics.json",
    output_filepath: str = "data/processed/sensitivity_analysis_size.json"
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across dataset size bins.
    """
    logger.info("Starting dataset size sensitivity analysis.")
    
    baseline_metrics = load_baseline_metrics(baseline_filepath)
    cleaned_metrics = load_cleaned_metrics(cleaned_filepath)

    # Extract datasets with size info
    # Assuming baseline_metrics has 'datasets' list with 'dataset_size'
    datasets = baseline_metrics.get('datasets', [])
    
    if not datasets:
        logger.warning("No datasets found in baseline metrics. Cannot perform binning.")
        # Create empty result
        output = {
            "analysis_type": "dataset_size_sensitivity",
            "timestamp": datetime.now().isoformat(),
            "bins": {
                "small": {"dataset_count": 0, "stats": {}},
                "medium": {"dataset_count": 0, "stats": {}},
                "large": {"dataset_count": 0, "stats": {}}
            },
            "summary": "No data available for analysis."
        }
        save_json_file(output_filepath, output)
        logger.info(f"Empty sensitivity analysis written to {output_filepath}")
        return output

    # Bin datasets
    for d in datasets:
        d['bin'] = bin_dataset_size(d.get('dataset_size', 0))

    # Analyze each bin
    bins = ["small", "medium", "large"]
    bin_results = {}
    
    for b in bins:
        bin_result = analyze_size_bin(datasets, b, baseline_metrics, cleaned_metrics)
        bin_results[b] = bin_result

        # Log warning if <1 dataset
        if bin_result['dataset_count'] < 1:
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{b}' has fewer than 1 dataset (count: {bin_result['dataset_count']}). Proceeding.")

    # Compile output
    output = {
        "analysis_type": "dataset_size_sensitivity",
        "timestamp": datetime.now().isoformat(),
        "bins": bin_results,
        "summary": {
            "total_datasets": len(datasets),
            "bin_counts": {b: bin_results[b]['dataset_count'] for b in bins}
        }
    }

    save_json_file(output_filepath, output)
    logger.info(f"Sensitivity analysis written to {output_filepath}")
    return output

def main():
    """Main entry point for T030."""
    logger.info("Executing T030: Dataset Size Sensitivity Analysis")
    run_sensitivity_analysis()
    logger.info("T030 completed.")

if __name__ == "__main__":
    main()
