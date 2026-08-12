import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Dict[str, Any]:
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(data: Dict[str, Any], filepath: str) -> None:
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Dict[str, Any]:
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Dict[str, Any]:
    return load_json_file(filepath)

def load_null_fpr_metrics(filepath: str = "data/processed/null_fpr_metrics.json") -> Dict[str, Any]:
    return load_json_file(filepath)

def calculate_absolute_diff(baseline_val: float, cleaned_val: float) -> float:
    if baseline_val is None or cleaned_val is None or (isinstance(baseline_val, float) and (baseline_val != baseline_val)):
        return float('nan')
    return abs(cleaned_val - baseline_val)

def calculate_relative_diff(baseline_val: float, cleaned_val: float) -> float:
    if baseline_val == 0:
        return float('nan')
    return (cleaned_val - baseline_val) / baseline_val

def calculate_inconsistency_rate(baseline_results: Dict, cleaned_results: Dict, threshold: float = 0.05) -> float:
    """
    Proportion of datasets where significance status changes.
    """
    total = 0
    inconsistent = 0
    for key in baseline_results:
        if key in cleaned_results:
            total += 1
            b_p = baseline_results[key].get('t_test', {}).get('p_value')
            c_p = cleaned_results[key].get('t_test', {}).get('p_value')
            
            if b_p is None or c_p is None:
                continue
                
            b_sig = b_p < threshold
            c_sig = c_p < threshold
            if b_sig != c_sig:
                inconsistent += 1
    
    return inconsistent / total if total > 0 else 0.0

def calculate_fpr(null_metrics: Dict, threshold: float = 0.05) -> float:
    """
    Calculate False Positive Rate from null metrics.
    FPR = (Number of significant results in null data) / (Total number of tests)
    """
    total_tests = 0
    significant_count = 0
    
    # null_metrics structure: { dataset_id: { t_test: {p_value: ...}, ... } }
    for dataset_id, metrics in null_metrics.items():
        p_val = metrics.get('t_test', {}).get('p_value')
        if p_val is not None:
            total_tests += 1
            if p_val < threshold:
                significant_count += 1
    
    if total_tests == 0:
        return 0.0
    return significant_count / total_tests

def generate_comparison_report(baseline: Dict, cleaned: Dict) -> Dict[str, Any]:
    report = {
        "baseline_metrics": baseline,
        "cleaned_metrics": cleaned,
        "absolute_diff": {},
        "relative_diff": {},
        "inconsistency_rate": calculate_inconsistency_rate(baseline, cleaned)
    }
    return report

def generate_fpr_report(null_metrics: Dict, thresholds: List[float] = [0.05]) -> Dict[str, Any]:
    report = {
        "null_metrics": null_metrics,
        "fpr_by_threshold": {}
    }
    for t in thresholds:
        report["fpr_by_threshold"][str(t)] = calculate_fpr(null_metrics, t)
    return report

def main():
    pass

if __name__ == "__main__":
    main()
