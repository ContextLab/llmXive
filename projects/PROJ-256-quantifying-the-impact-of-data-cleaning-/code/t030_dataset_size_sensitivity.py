import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils import setup_logging, pin_random_seed

# Configure logging
logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}")
        return {"datasets": []}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Cleaned metrics file not found: {filepath}")
        return {"datasets": []}
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
    Analyze a specific size bin.
    Returns summary statistics for p-value shifts within the bin.
    """
    if not datasets:
        return {
            "bin": bin_name,
            "count": 0,
            "avg_p_value_shift": None,
            "min_p_value_shift": None,
            "max_p_value_shift": None,
            "datasets_analyzed": []
        }

    shifts = []
    dataset_details = []

    for entry in datasets:
        ds_name = entry.get('dataset_name') or entry.get('dataset_id')
        n_rows = entry.get('n_rows') or entry.get('dataset_size', 0)
        
        # Find corresponding baseline and cleaned entries
        base_entry = None
        clean_entry = None

        if 'datasets' in baseline_metrics:
            for b in baseline_metrics['datasets']:
                if (b.get('dataset_name') == ds_name or b.get('dataset_id') == ds_name):
                    base_entry = b
                    break

        if 'datasets' in cleaned_metrics:
            for c in cleaned_metrics['datasets']:
                if (c.get('dataset_name') == ds_name or c.get('dataset_id') == ds_name):
                    clean_entry = c
                    break

        if not base_entry or not clean_entry:
            logger.warning(f"Could not find matching metrics for {ds_name} in bin {bin_name}")
            continue

        # Extract p-values (assume t-test for simplicity, or aggregate if multiple)
        # Assuming structure: base_entry['analysis']['t_test']['p_value']
        base_p = None
        clean_p = None

        if 'analysis' in base_entry and 't_test' in base_entry['analysis']:
            base_p = base_entry['analysis']['t_test'].get('p_value')
        elif 'p_value' in base_entry:
            base_p = base_entry['p_value']

        if 'analysis' in clean_entry and 't_test' in clean_entry['analysis']:
            clean_p = clean_entry['analysis']['t_test'].get('p_value')
        elif 'p_value' in clean_entry:
            clean_p = clean_entry['p_value']

        if base_p is not None and clean_p is not None:
            shift = calculate_p_value_shift(base_p, clean_p)
            shifts.append(shift)
            dataset_details.append({
                "dataset_name": ds_name,
                "n_rows": n_rows,
                "base_p": base_p,
                "clean_p": clean_p,
                "shift": shift
            })

    if not shifts:
        return {
            "bin": bin_name,
            "count": len(datasets),
            "avg_p_value_shift": None,
            "min_p_value_shift": None,
            "max_p_value_shift": None,
            "datasets_analyzed": dataset_details,
            "note": "No valid p-value pairs found in this bin."
        }

    avg_shift = sum(shifts) / len(shifts)
    return {
        "bin": bin_name,
        "count": len(datasets),
        "avg_p_value_shift": round(avg_shift, 6),
        "min_p_value_shift": round(min(shifts), 6),
        "max_p_value_shift": round(max(shifts), 6),
        "datasets_analyzed": dataset_details
    }

def run_sensitivity_analysis(
    baseline_filepath: str = "data/processed/baseline_metrics.json",
    cleaned_filepath: str = "data/processed/cleaned_metrics.json",
    output_filepath: str = "data/processed/sensitivity_by_size.json"
) -> Dict[str, Any]:
    """
    Run dataset size binning sensitivity analysis.
    Bins: n < 50, 50-200, > 200.
    Logs warnings if bins are empty or have < 1 dataset.
    """
    logger.info("Starting dataset size sensitivity analysis...")
    
    try:
        baseline_data = load_baseline_metrics(baseline_filepath)
        cleaned_data = load_cleaned_metrics(cleaned_filepath)
    except FileNotFoundError as e:
        logger.error(str(e))
        return {"error": str(e)}

    # Aggregate all datasets from baseline and cleaned
    all_datasets = []
    seen_names = set()

    # Process baseline datasets
    if 'datasets' in baseline_data:
        for ds in baseline_data['datasets']:
            name = ds.get('dataset_name') or ds.get('dataset_id')
            if name and name not in seen_names:
                all_datasets.append({
                    "dataset_name": name,
                    "dataset_id": ds.get('dataset_id'),
                    "n_rows": ds.get('n_rows') or ds.get('dataset_size', 0)
                })
                seen_names.add(name)

    # Process cleaned datasets (ensure we don't duplicate if already in baseline)
    if 'datasets' in cleaned_data:
        for ds in cleaned_data['datasets']:
            name = ds.get('dataset_name') or ds.get('dataset_id')
            if name and name not in seen_names:
                all_datasets.append({
                    "dataset_name": name,
                    "dataset_id": ds.get('dataset_id'),
                    "n_rows": ds.get('n_rows') or ds.get('dataset_size', 0)
                })
                seen_names.add(name)

    if not all_datasets:
        logger.warning("No datasets found in baseline or cleaned metrics.")
        return {"error": "No datasets found."}

    # Bin datasets
    bins = {
        "small": [],   # n < 50
        "medium": [],  # 50 <= n <= 200
        "large": []    # n > 200
    }

    for ds in all_datasets:
        bin_name = bin_dataset_size(ds['n_rows'])
        bins[bin_name].append(ds)

    # Log warnings for empty or low-count bins
    for bin_name, ds_list in bins.items():
        if len(ds_list) == 0:
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' is empty (0 datasets).")
        elif len(ds_list) < 1:
            # This case is technically covered by len==0, but keeping for explicit logic
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' has fewer than 1 dataset.")
        else:
            logger.info(f"Bin '{bin_name}' contains {len(ds_list)} datasets.")

    # Analyze each bin
    results = {
        "analysis_type": "dataset_size_sensitivity",
        "generated_at": datetime.now().isoformat(),
        "bins": {},
        "summary": {
            "total_datasets": len(all_datasets),
            "bin_distribution": {k: len(v) for k, v in bins.items()}
        }
    }

    for bin_name, ds_list in bins.items():
        bin_result = analyze_size_bin(bin_name, ds_list, baseline_data, cleaned_data)
        results["bins"][bin_name] = bin_result

    # Write output
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    with open(output_filepath, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Sensitivity analysis complete. Output written to {output_filepath}")
    return results

def main():
    """Main entry point for the script."""
    setup_logging("INFO")
    pin_random_seed(42)
    
    result = run_sensitivity_analysis()
    
    if "error" in result:
        logger.error(f"Analysis failed: {result['error']}")
        return 1
    
    logger.info("Analysis completed successfully.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())