import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import os
from utils import setup_logging

logger = setup_logging("INFO")

def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return None
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(filepath: str, data: Dict[str, Any]):
    output_dir = os.path.dirname(filepath)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved to {filepath}")

def calculate_p_value_shift(p_baseline: float, p_cleaned: float) -> float:
    """Calculate absolute difference in p-values."""
    return abs(p_cleaned - p_baseline)

def compute_ci_width_change(ci_baseline: List[float], ci_cleaned: List[float]) -> float:
    """Calculate change in confidence interval width."""
    if not ci_baseline or not ci_cleaned:
        return 0.0
    width_baseline = ci_baseline[1] - ci_baseline[0]
    width_cleaned = ci_cleaned[1] - ci_cleaned[0]
    return width_cleaned - width_baseline

def compute_effect_size_delta(effect_baseline: float, effect_cleaned: float) -> float:
    """Calculate difference in effect size."""
    return effect_cleaned - effect_baseline

def calculate_inconsistency_rate(baseline_p: float, cleaned_p: float, alpha: float = 0.05) -> int:
    """Determine if significance status changed."""
    sig_baseline = baseline_p < alpha
    sig_cleaned = cleaned_p < alpha
    return 1 if sig_baseline != sig_cleaned else 0

def apply_bonferroni_correction(p_values: List[float]) -> List[float]:
    """Apply Bonferroni correction for multiple comparisons."""
    n = len(p_values)
    if n == 0:
        return []
    logger.warning("Warning: FR-007 requests FWER control. Benjamini-Hochberg controls FDR. Implemented Bonferroni (FWER) to satisfy FR-007.")
    return [min(p * n, 1.0) for p in p_values]

def process_single_comparison(baseline_entry: Dict, cleaned_entry: Dict, alpha: float = 0.05) -> Dict[str, Any]:
    """Process a single dataset comparison."""
    result = {}

    # P-value shift
    bp = baseline_entry.get('p_value')
    cp = cleaned_entry.get('p_value')
    if bp is not None and cp is not None:
        result['p_value_shift'] = calculate_p_value_shift(bp, cp)
        result['inconsistency'] = calculate_inconsistency_rate(bp, cp, alpha)

    # CI width change
    bc = baseline_entry.get('ci')
    cc = cleaned_entry.get('ci')
    if bc and cc:
        result['ci_width_change'] = compute_ci_width_change(bc, cc)

    # Effect size delta
    be = baseline_entry.get('effect_size')
    ce = cleaned_entry.get('effect_size')
    if be is not None and ce is not None:
        result['effect_size_delta'] = compute_effect_size_delta(be, ce)

    return result

def generate_comparison_report(baseline_metrics: Dict[str, Any], cleaned_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a comprehensive comparison report."""
    # Handle cases where metrics might be lists or dicts
    # The error indicated cleaned_metrics was a list, so we handle that
    if isinstance(cleaned_metrics, list):
        # If it's a list, we might need to aggregate or find the right structure
        # For now, assume it's a list of dataset results and we need to wrap it
        logger.warning("cleaned_metrics is a list, attempting to structure it.")
        cleaned_metrics = {"datasets": cleaned_metrics}

    if not baseline_metrics or not cleaned_metrics:
        logger.error("Missing baseline or cleaned metrics.")
        return {}

    baseline_datasets = baseline_metrics.get("datasets", [])
    if isinstance(baseline_datasets, dict):
        baseline_datasets = [baseline_datasets]

    cleaned_datasets = cleaned_metrics.get("datasets", [])
    if isinstance(cleaned_datasets, dict):
        cleaned_datasets = [cleaned_datasets]

    comparisons = []
    total_inconsistency = 0

    # Match datasets by name
    baseline_map = {d.get('dataset_name'): d for d in baseline_datasets}
    cleaned_map = {d.get('dataset_name'): d for d in cleaned_datasets}

    for name in baseline_map:
        if name in cleaned_map:
            b_entry = baseline_map[name]
            c_entry = cleaned_map[name]
            comp = process_single_comparison(b_entry, c_entry)
            comp['dataset_name'] = name
            comparisons.append(comp)
            total_inconsistency += comp.get('inconsistency', 0)

    n_datasets = len(comparisons)
    inconsistency_rate = total_inconsistency / n_datasets if n_datasets > 0 else 0.0

    return {
        "generated_at": datetime.now().isoformat(),
        "n_datasets": n_datasets,
        "inconsistency_rate": inconsistency_rate,
        "comparisons": comparisons
    }

def main():
    # Example usage for testing
    pass

if __name__ == "__main__":
    main()
