"""
T030: Implement dataset size binning sensitivity analysis (n<50, 50-200, >200).

This script analyzes how statistical metric shifts (p-value, CI width, effect size)
vary based on dataset size. It bins datasets into three categories:
- Small: n < 50
- Medium: 50 <= n <= 200
- Large: n > 200

It logs warnings if a bin contains fewer than 1 dataset (empty bin) but proceeds.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils import setup_logging, pin_random_seed

# Configuration for bins
BIN_THRESHOLDS = [50, 200]
BIN_LABELS = ["Small (n<50)", "Medium (50-200)", "Large (n>200)"]

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Optional[Dict[str, Any]]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logging.error(f"Baseline metrics file not found: {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse baseline metrics: {e}")
        return None

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Optional[Dict[str, Any]]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        logging.error(f"Cleaned metrics file not found: {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse cleaned metrics: {e}")
        return None

def bin_dataset_size(n_rows: int) -> str:
    """
    Assign a dataset size bin label based on row count.
    
    Args:
        n_rows: Number of rows in the dataset.
        
    Returns:
        String label for the bin.
    """
    if n_rows < BIN_THRESHOLDS[0]:
        return BIN_LABELS[0]
    elif n_rows <= BIN_THRESHOLDS[1]:
        return BIN_LABELS[1]
    else:
        return BIN_LABELS[2]

def extract_dataset_info(metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract dataset information including name, size, and metrics from loaded JSON.
    
    Args:
        metrics_data: The loaded JSON dictionary containing metrics.
        
    Returns:
        List of dictionaries with dataset info.
    """
    datasets = []
    if not metrics_data or "datasets" not in metrics_data:
        return datasets
        
    for entry in metrics_data.get("datasets", []):
        if not isinstance(entry, dict):
            continue
        
        dataset_name = entry.get("dataset_name") or entry.get("name") or "Unknown"
        
        # Determine size from metadata or analysis
        # Try to find in 'analysis' -> 'dataset_size' or top level
        size = entry.get("dataset_size") or entry.get("n_rows")
        if size is None:
            # Try to infer from analysis block if available
            analysis = entry.get("analysis", {})
            if isinstance(analysis, dict):
                size = analysis.get("dataset_size") or analysis.get("n_rows")
        
        # If still missing, try to get from raw data path if present (optional fallback)
        if size is None:
            logging.warning(f"Could not determine size for dataset: {dataset_name}. Skipping.")
            continue
        
        datasets.append({
            "name": dataset_name,
            "size": size,
            "bin": bin_dataset_size(size),
            "baseline": entry.get("baseline", entry.get("t_test", {})),
            "cleaned": entry.get("cleaned", {}) # Simplified; actual structure depends on T023 output
        })
        
    return datasets

def analyze_size_bin(bin_label: str, datasets_in_bin: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze a specific size bin.
    
    Args:
        bin_label: The label of the bin.
        datasets_in_bin: List of dataset dictionaries in this bin.
        
    Returns:
        Dictionary containing analysis results for the bin.
    """
    result = {
        "bin": bin_label,
        "count": len(datasets_in_bin),
        "datasets": [d["name"] for d in datasets_in_bin],
        "metrics": {}
    }
    
    if not datasets_in_bin:
        result["metrics"] = {
            "p_value_shift": {"mean": None, "median": None, "std": None},
            "ci_width_shift": {"mean": None, "median": None, "std": None},
            "effect_size_shift": {"mean": None, "median": None, "std": None}
        }
        return result

    # Calculate shifts for each dataset in the bin
    p_shifts = []
    ci_shifts = []
    es_shifts = []

    for d in datasets_in_bin:
        baseline = d.get("baseline", {})
        cleaned = d.get("cleaned", {})
        
        # Extract p-values
        # Note: Structure depends on T012/T023 output. Assuming 'p_value' exists.
        p_base = baseline.get("p_value") if isinstance(baseline, dict) else None
        p_clean = cleaned.get("p_value") if isinstance(cleaned, dict) else None
        
        if p_base is not None and p_clean is not None and isinstance(p_base, (int, float)) and isinstance(p_clean, (int, float)):
            p_shifts.append(abs(p_clean - p_base))
        
        # Extract CI widths (assuming 'ci' is a tuple/list [lower, upper])
        ci_base = baseline.get("ci")
        ci_clean = cleaned.get("ci")
        
        if ci_base and ci_clean and len(ci_base) == 2 and len(ci_clean) == 2:
            try:
                width_base = abs(ci_base[1] - ci_base[0])
                width_clean = abs(ci_clean[1] - ci_clean[0])
                if width_base > 0 and width_clean > 0:
                    ci_shifts.append(width_clean - width_base)
            except (TypeError, IndexError):
                pass
        
        # Extract effect sizes
        es_base = baseline.get("effect_size")
        es_clean = cleaned.get("effect_size")
        
        if es_base is not None and es_clean is not None:
            try:
                es_shifts.append(abs(es_clean - es_base))
            except (TypeError, ValueError):
                pass

    # Compute statistics
    import numpy as np
    
    def safe_stats(values):
        if not values:
            return {"mean": None, "median": None, "std": None}
        arr = np.array(values)
        return {
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "std": float(np.std(arr))
        }

    result["metrics"] = {
        "p_value_shift": safe_stats(p_shifts),
        "ci_width_shift": safe_stats(ci_shifts),
        "effect_size_shift": safe_stats(es_shifts)
    }
    
    return result

def run_sensitivity_analysis(baseline_path: str, cleaned_path: str, output_path: str) -> bool:
    """
    Run the full sensitivity analysis across dataset sizes.
    
    Args:
        baseline_path: Path to baseline metrics JSON.
        cleaned_path: Path to cleaned metrics JSON.
        output_path: Path to save the sensitivity report.
        
    Returns:
        True if successful, False otherwise.
    """
    logging.info("Starting dataset size sensitivity analysis...")
    
    baseline_data = load_baseline_metrics(baseline_path)
    if not baseline_data:
        logging.error("Failed to load baseline metrics. Cannot proceed.")
        return False
        
    cleaned_data = load_cleaned_metrics(cleaned_path)
    # Cleaned data might be empty or missing if T023 failed, but we proceed with what we have
    if not cleaned_data:
        logging.warning("Cleaned metrics not found or empty. Proceeding with baseline only (shifts will be null).")
        cleaned_data = {"datasets": []}

    # Combine info. We assume baseline and cleaned have matching dataset names.
    # In a real scenario, we'd merge by name. Here we iterate baseline and lookup cleaned.
    baseline_map = {d["name"]: d for d in extract_dataset_info(baseline_data)}
    cleaned_map = {d["name"]: d for d in extract_dataset_info(cleaned_data)}
    
    combined_datasets = []
    for name, b_info in baseline_map.items():
        c_info = cleaned_map.get(name, {})
        combined_datasets.append({
            "name": name,
            "size": b_info["size"],
            "bin": b_info["bin"],
            "baseline": b_info.get("baseline", {}),
            "cleaned": c_info.get("cleaned", {})
        })
    
    # Bin the datasets
    bins = {label: [] for label in BIN_LABELS}
    for d in combined_datasets:
        bins[d["bin"]].append(d)
    
    # Check constraints and log warnings
    for label, items in bins.items():
        if len(items) < 1:
            logging.warning(f"CONSTRAINT_VIOLATION: Bin '{label}' is empty (<1 dataset). Proceeding with empty bin analysis.")
        else:
            logging.info(f"Bin '{label}' contains {len(items)} dataset(s).")
    
    # Analyze each bin
    analysis_results = []
    for label in BIN_LABELS:
        bin_result = analyze_size_bin(label, bins[label])
        analysis_results.append(bin_result)
    
    # Prepare final report
    report = {
        "timestamp": datetime.now().isoformat(),
        "bin_labels": BIN_LABELS,
        "bin_thresholds": BIN_THRESHOLDS,
        "analysis": analysis_results,
        "summary": {
            "total_datasets": len(combined_datasets),
            "bins_with_data": sum(1 for b in analysis_results if b["count"] > 0),
            "bins_empty": sum(1 for b in analysis_results if b["count"] == 0)
        }
    }
    
    # Write output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    try:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logging.info(f"Sensitivity analysis report saved to: {output_path}")
        return True
    except IOError as e:
        logging.error(f"Failed to write sensitivity report: {e}")
        return False

def main():
    """Main entry point for T030."""
    logger = setup_logging("INFO")
    pin_random_seed(42)
    
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/sensitivity_analysis_by_size.json"
    
    success = run_sensitivity_analysis(baseline_path, cleaned_path, output_path)
    
    if not success:
        logging.error("Sensitivity analysis failed.")
        return 1
    
    logging.info("Sensitivity analysis completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
