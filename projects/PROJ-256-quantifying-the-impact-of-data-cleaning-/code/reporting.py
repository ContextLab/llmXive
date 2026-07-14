import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import os

logger = logging.getLogger('llmXive')

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(data: Dict[str, Any], filepath: str) -> bool:
    """Save data to a JSON file."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {filepath}: {e}")
        return False

def calculate_p_value_shift(baseline_p: float, cleaned_p: float) -> float:
    """Calculate absolute difference between baseline and cleaned p-values."""
    return round(abs(cleaned_p - baseline_p), 4)

def compute_ci_width_change(baseline_ci: Tuple[float, float], cleaned_ci: Tuple[float, float]) -> float:
    """Calculate change in confidence interval width."""
    if not baseline_ci or not cleaned_ci:
        return 0.0
    baseline_width = abs(baseline_ci[1] - baseline_ci[0])
    cleaned_width = abs(cleaned_ci[1] - cleaned_ci[0])
    return round(cleaned_width - baseline_width, 4)

def compute_effect_size_delta(baseline_es: float, cleaned_es: float) -> float:
    """Calculate difference in effect size."""
    return round(cleaned_es - baseline_es, 4)

def calculate_inconsistency_rate(baseline_results: List[Dict], cleaned_results: List[Dict], threshold: float = 0.05) -> float:
    """
    Calculate the proportion of datasets where significance status changes.
    
    Significance is determined by p_value <= threshold.
    """
    if not baseline_results or not cleaned_results:
        return 0.0
    
    # Create lookup maps
    baseline_map = {r.get("dataset_name"): r for r in baseline_results}
    cleaned_map = {r.get("dataset_name"): r for r in cleaned_results}
    
    inconsistencies = 0
    total = 0
    
    for name, b_entry in baseline_map.items():
        if name not in cleaned_map:
            continue
        
        c_entry = cleaned_map[name]
        
        b_p = b_entry.get("analysis", {}).get("t_test", {}).get("p_value", 1.0)
        c_p = c_entry.get("analysis", {}).get("t_test", {}).get("p_value", 1.0)
        
        b_sig = b_p <= threshold
        c_sig = c_p <= threshold
        
        if b_sig != c_sig:
            inconsistencies += 1
        
        total += 1
    
    return inconsistencies / total if total > 0 else 0.0

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Bonferroni correction for Family-Wise Error Rate (FWER)."""
    n = len(p_values)
    if n == 0:
        return []
    
    logger.warning("Warning: FR-007 requests FWER control. Benjamini-Hochberg controls FDR. Implemented Bonferroni (FWER) to satisfy FR-007.")
    
    corrected_alpha = alpha / n
    return [min(p * n, 1.0) for p in p_values]

def process_single_comparison(baseline_entry: Dict, cleaned_entry: Dict) -> Dict[str, Any]:
    """Process a single dataset comparison."""
    b_p = baseline_entry.get("analysis", {}).get("t_test", {}).get("p_value", 1.0)
    c_p = cleaned_entry.get("analysis", {}).get("t_test", {}).get("p_value", 1.0)
    
    b_ci = baseline_entry.get("analysis", {}).get("t_test", {}).get("ci", [0, 0])
    c_ci = cleaned_entry.get("analysis", {}).get("t_test", {}).get("ci", [0, 0])
    
    b_es = baseline_entry.get("analysis", {}).get("t_test", {}).get("effect_size", 0.0)
    c_es = cleaned_entry.get("analysis", {}).get("t_test", {}).get("effect_size", 0.0)
    
    return {
        "dataset_name": baseline_entry.get("dataset_name"),
        "p_value_shift": calculate_p_value_shift(b_p, c_p),
        "ci_width_change": compute_ci_width_change(b_ci, c_ci),
        "effect_size_delta": compute_effect_size_delta(b_es, c_es),
        "baseline_p": b_p,
        "cleaned_p": c_p,
        "baseline_sig": b_p <= 0.05,
        "cleaned_sig": c_p <= 0.05
    }

def generate_comparison_report(baseline_metrics: Dict, cleaned_metrics: Dict) -> Dict[str, Any]:
    """Generate a comprehensive comparison report."""
    baseline_datasets = baseline_metrics.get("datasets", [])
    cleaned_datasets = cleaned_metrics.get("datasets", [])
    
    comparisons = []
    for b_entry in baseline_datasets:
        name = b_entry.get("dataset_name")
        c_entry = next((c for c in cleaned_datasets if c.get("dataset_name") == name), None)
        if c_entry:
            comparisons.append(process_single_comparison(b_entry, c_entry))
    
    # Calculate aggregate statistics
    p_shifts = [c["p_value_shift"] for c in comparisons]
    ci_changes = [c["ci_width_change"] for c in comparisons]
    es_deltas = [c["effect_size_delta"] for c in comparisons]
    
    inconsistency_rate = calculate_inconsistency_rate(baseline_datasets, cleaned_datasets)
    
    return {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "num_comparisons": len(comparisons)
        },
        "comparisons": comparisons,
        "aggregate": {
            "median_p_shift": float(np.median(p_shifts)) if p_shifts else 0.0,
            "median_ci_change": float(np.median(ci_changes)) if ci_changes else 0.0,
            "median_es_delta": float(np.median(es_deltas)) if es_deltas else 0.0,
            "inconsistency_rate": inconsistency_rate
        }
    }

def main():
    """Main entry point for reporting module."""
    logger.info("Reporting module loaded")
