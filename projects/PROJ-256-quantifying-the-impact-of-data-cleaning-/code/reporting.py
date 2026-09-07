"""
Reporting and metrics aggregation.
"""
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
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Dict[str, Any]:
    """Load baseline metrics."""
    if not Path(filepath).exists():
        return {}
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Dict[str, Any]:
    """Load cleaned metrics."""
    if not Path(filepath).exists():
        return {}
    return load_json_file(filepath)

def load_null_fpr_metrics(filepath: str = "data/processed/null_fpr_metrics.json") -> Dict[str, Any]:
    """Load null FPR metrics."""
    if not Path(filepath).exists():
        return {}
    return load_json_file(filepath)

def calculate_absolute_diff(val1: float, val2: float) -> float:
    """Calculate absolute difference."""
    return abs(val1 - val2)

def calculate_relative_diff(val1: float, val2: float) -> float:
    """Calculate relative difference."""
    if val1 == 0:
        return 0.0
    return (val2 - val1) / abs(val1)

def calculate_inconsistency_rate(results: List[Dict[str, Any]]) -> float:
    """Calculate inconsistency rate across results."""
    if not results:
        return 0.0
    significant_count = sum(1 for r in results if r.get("p_value", 1) < 0.05)
    return significant_count / len(results)

def calculate_fpr(p_values: List[float], alpha: float = 0.05) -> float:
    """Calculate False Positive Rate."""
    if not p_values:
        return 0.0
    significant_count = sum(1 for p in p_values if p < alpha)
    return significant_count / len(p_values)

def generate_comparison_report(baseline: Dict[str, Any], cleaned: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a comparison report between baseline and cleaned metrics."""
    report = {
        "datasets": {},
        "summary": {
            "total_datasets": 0,
            "significant_changes": 0
        }
    }
    
    for dataset_name, baseline_metrics in baseline.items():
        if dataset_name not in cleaned:
            continue
        
        report["datasets"][dataset_name] = {
            "baseline": baseline_metrics,
            "cleaning_variants": {}
        }
        
        for strategy, cleaned_metrics in cleaned[dataset_name].items():
            b_p = baseline_metrics.get("p_value", np.nan)
            c_p = cleaned_metrics.get("p_value", np.nan)
            
            diff = calculate_absolute_diff(b_p, c_p)
            rel_diff = calculate_relative_diff(b_p, c_p)
            
            report["datasets"][dataset_name]["cleaning_variants"][strategy] = {
                "baseline_p_value": b_p,
                "cleaned_p_value": c_p,
                "absolute_diff": diff,
                "relative_diff": rel_diff,
                "effect_size_change": calculate_absolute_diff(
                    baseline_metrics.get("effect_size", 0),
                    cleaned_metrics.get("effect_size", 0)
                )
            }
            
            if abs(diff) > 0.05: # Arbitrary threshold for "significant change"
                report["summary"]["significant_changes"] += 1
        
        report["summary"]["total_datasets"] += 1
    
    return report

def generate_fpr_report(null_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Generate FPR report from null metrics."""
    report = {
        "datasets": {},
        "overall_fpr": 0.0
    }
    
    all_fprs = []
    for dataset_name, metrics in null_metrics.items():
        fpr = metrics.get("fpr", 0.0)
        report["datasets"][dataset_name] = {"fpr": fpr}
        all_fprs.append(fpr)
    
    if all_fprs:
        report["overall_fpr"] = np.mean(all_fprs)
    
    return report
