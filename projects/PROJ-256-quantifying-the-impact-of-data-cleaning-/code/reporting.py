import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(data: Dict[str, Any], filepath: str) -> None:
    """Save data to a JSON file."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_baseline_metrics(filepath: str = None) -> Dict[str, Any]:
    """Load baseline metrics from the default or specified path."""
    from config import get_config
    config = get_config()
    if filepath is None:
        filepath = config.get("PROCESSED_DATA_PATH") + "/baseline_metrics.json"
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str = None) -> Dict[str, Any]:
    """Load cleaned metrics from the default or specified path."""
    from config import get_config
    config = get_config()
    if filepath is None:
        filepath = config.get("PROCESSED_DATA_PATH") + "/cleaned_metrics.json"
    return load_json_file(filepath)

def load_null_fpr_metrics(filepath: str = None) -> Dict[str, Any]:
    """Load null FPR metrics from the default or specified path."""
    from config import get_config
    config = get_config()
    if filepath is None:
        filepath = config.get("PROCESSED_DATA_PATH") + "/null_fpr_metrics.json"
    return load_json_file(filepath)

def calculate_absolute_diff(baseline: float, cleaned: float) -> float:
    """Calculate absolute difference."""
    return abs(cleaned - baseline)

def calculate_relative_diff(baseline: float, cleaned: float) -> float:
    """Calculate relative difference."""
    if baseline == 0:
        return float('inf') if cleaned != 0 else 0
    return (cleaned - baseline) / baseline

def calculate_inconsistency_rate(baseline_results: Dict, cleaned_results: Dict, threshold: float = 0.05) -> float:
    """
    Calculate the proportion of datasets where significance status changes.
    """
    inconsistencies = 0
    total = 0
    
    for dataset, baseline_data in baseline_results.items():
        if dataset in cleaned_results:
            for predictor, baseline_metric in baseline_data.items():
                if predictor in cleaned_results[dataset]:
                    total += 1
                    b_sig = baseline_metric.get("t_test", {}).get("p_value", 1) < threshold
                    c_sig = cleaned_results[dataset][predictor].get("t_test", {}).get("p_value", 1) < threshold
                    if b_sig != c_sig:
                        inconsistencies += 1
    
    return inconsistencies / total if total > 0 else 0

def calculate_fpr(null_metrics: Dict[str, Any]) -> float:
    """Calculate False Positive Rate from null metrics."""
    significant_count = 0
    total_count = 0
    
    for dataset, data in null_metrics.items():
        if isinstance(data, dict):
            for metric in data.values():
                if isinstance(metric, dict):
                    p_val = metric.get("t_test", {}).get("p_value", 1)
                    if p_val < 0.05:
                        significant_count += 1
                    total_count += 1
    
    return significant_count / total_count if total_count > 0 else 0

def generate_comparison_report(baseline_metrics: Dict, cleaned_metrics: Dict) -> Dict[str, Any]:
    """Generate a comparison report between baseline and cleaned metrics."""
    report = {
        "absolute_diffs": {},
        "relative_diffs": {},
        "inconsistency_rate": calculate_inconsistency_rate(baseline_metrics, cleaned_metrics)
    }
    
    for dataset, baseline_data in baseline_metrics.items():
        if dataset in cleaned_metrics:
            report["absolute_diffs"][dataset] = {}
            report["relative_diffs"][dataset] = {}
            
            for predictor, baseline_metric in baseline_data.items():
                if predictor in cleaned_metrics[dataset]:
                    b_p = baseline_metric.get("t_test", {}).get("p_value", 1)
                    c_p = cleaned_metrics[dataset][predictor].get("t_test", {}).get("p_value", 1)
                    
                    report["absolute_diffs"][dataset][predictor] = calculate_absolute_diff(b_p, c_p)
                    report["relative_diffs"][dataset][predictor] = calculate_relative_diff(b_p, c_p)
    
    return report

def generate_fpr_report(null_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Generate FPR report."""
    return {
        "fpr": calculate_fpr(null_metrics),
        "threshold": 0.05
    }

def main():
    """
    Entry point for reporting module.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Load metrics
    try:
        baseline = load_baseline_metrics()
        cleaned = load_cleaned_metrics()
        
        report = generate_comparison_report(baseline, cleaned)
        save_json_file(report, "output/reports/comparison_report.json")
        logger.info("Comparison report generated.")
    except FileNotFoundError as e:
        logger.error(f"Metrics file not found: {e}")

if __name__ == "__main__":
    main()
