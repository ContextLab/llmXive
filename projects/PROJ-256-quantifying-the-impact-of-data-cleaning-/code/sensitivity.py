import json
import logging
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
import numpy as np
from utils import setup_logging, pin_random_seed
from config import get_config

logger = logging.getLogger(__name__)

def run_outlier_threshold_sweep(baseline_metrics: Dict, cleaned_metrics: Dict, thresholds: List[float] = [1.0, 1.5, 2.0]) -> Dict[str, Any]:
    """
    Sweep outlier thresholds and compute FPR and inconsistency rates.
    """
    results = {
        "thresholds": thresholds,
        "fpr": [],
        "inconsistency_rate": []
    }

    for k in thresholds:
        # Mock FPR calculation for now (requires permutation null which is T032)
        # In a real run, this would load null_fpr_metrics.json
        fpr = 0.05 # Placeholder
        inc_rate = 0.1 # Placeholder
        
        results["fpr"].append({"k": k, "fpr": fpr})
        results["inconsistency_rate"].append({"k": k, "rate": inc_rate})

    return results

def run_size_binning_sensitivity(metrics: Dict) -> Dict[str, Any]:
    """
    Bin datasets by size and analyze sensitivity.
    """
    bins = {
        "small": [],
        "medium": [],
        "large": []
    }
    
    for name, data in metrics.items():
        n = data.get('dataset_info', {}).get('n_rows', 0)
        if n < 50:
            bins['small'].append(name)
        elif n <= 200:
            bins['medium'].append(name)
        else:
            bins['large'].append(name)
    
    report = {
        "bins": bins,
        "analysis": {}
    }
    
    for bin_name, names in bins.items():
        if not names:
            logger.warning(f"Missingness bin empty: bin {bin_name} has no datasets")
            continue
        # Analyze metrics for this bin
        report["analysis"][bin_name] = {"count": len(names), "datasets": names}
    
    return report

def main():
    config = get_config()
    pin_random_seed(42)
    logger = setup_logging("INFO")
    
    # Load metrics
    baseline = load_json_file("data/processed/baseline_metrics.json")
    cleaned = load_json_file("data/processed/cleaned_metrics.json")
    
    # Sweep
    sweep_report = run_outlier_threshold_sweep(baseline, cleaned)
    save_json_file(sweep_report, "data/processed/outlier_threshold_sweep_report.json")
    
    # Size binning
    size_report = run_size_binning_sensitivity(baseline)
    save_json_file(size_report, "data/processed/dataset_size_binning_report.json")

if __name__ == "__main__":
    main()