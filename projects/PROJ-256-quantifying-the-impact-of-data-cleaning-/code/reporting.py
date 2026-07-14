import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import os

logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(filepath: str, data: Dict[str, Any]) -> None:
    """Save data to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def calculate_p_value_shift(p_baseline: float, p_cleaned: float) -> float:
    """Calculate absolute difference in p-values."""
    return abs(p_cleaned - p_baseline)

def compute_ci_width_change(ci_baseline: Tuple[float, float], ci_cleaned: Tuple[float, float]) -> float:
    """Calculate change in CI width."""
    width_baseline = ci_baseline[1] - ci_baseline[0]
    width_cleaned = ci_cleaned[1] - ci_cleaned[0]
    return width_cleaned - width_baseline

def compute_effect_size_delta(effect_baseline: float, effect_cleaned: float) -> float:
    """Calculate difference in effect size."""
    return effect_cleaned - effect_baseline

def calculate_inconsistency_rate(
    baseline_results: List[Dict[str, Any]],
    cleaned_results: List[Dict[str, Any]],
    significance_threshold: float = 0.05
) -> float:
    """
    Calculate the proportion of datasets where significance status changes.
    """
    if not baseline_results or not cleaned_results:
        return 0.0

    if len(baseline_results) != len(cleaned_results):
        logger.warning("Baseline and cleaned result counts differ. Aligning by index.")
        min_len = min(len(baseline_results), len(cleaned_results))
        baseline_results = baseline_results[:min_len]
        cleaned_results = cleaned_results[:min_len]

    inconsistencies = 0
    total = len(baseline_results)

    for b, c in zip(baseline_results, cleaned_results):
        b_sig = b.get('p_value', 1.0) < significance_threshold
        c_sig = c.get('p_value', 1.0) < significance_threshold
        if b_sig != c_sig:
            inconsistencies += 1

    return inconsistencies / total if total > 0 else 0.0

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate (FWER).
    """
    n = len(p_values)
    if n == 0:
        return []
    
    corrected_alpha = alpha / n
    logger.warning("Warning: FR-007 requests FWER control. Benjamini-Hochberg controls FDR. Implemented Bonferroni (FWER) to satisfy FR-007.")
    return [min(p * n, 1.0) for p in p_values]

def process_single_comparison(
    baseline_entry: Dict[str, Any],
    cleaned_entry: Dict[str, Any]
) -> Dict[str, Any]:
    """Process a single dataset comparison."""
    b_tests = baseline_entry.get('analysis', {}).get('t_test', {})
    c_tests = cleaned_entry.get('analysis', {}).get('t_test', {})

    b_p = b_tests.get('p_value')
    c_p = c_tests.get('p_value')
    b_ci = b_tests.get('ci')
    c_ci = c_tests.get('ci')
    b_eff = b_tests.get('effect_size')
    c_eff = c_tests.get('effect_size')

    result = {
        "dataset_name": baseline_entry.get('dataset_name'),
        "p_value_shift": None,
        "ci_width_change": None,
        "effect_size_delta": None
    }

    if b_p is not None and c_p is not None:
        result["p_value_shift"] = calculate_p_value_shift(b_p, c_p)

    if b_ci and c_ci and len(b_ci) == 2 and len(c_ci) == 2:
        result["ci_width_change"] = compute_ci_width_change(b_ci, c_ci)

    if b_eff is not None and c_eff is not None:
        result["effect_size_delta"] = compute_effect_size_delta(b_eff, c_eff)

    return result

def generate_comparison_report(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    output_path: str = "data/processed/comparison_report.json"
) -> Dict[str, Any]:
    """Generate full comparison report."""
    baseline_datasets = baseline_metrics.get('datasets', [])
    cleaned_datasets = cleaned_metrics.get('datasets', [])

    # Map by name
    cleaned_map = {d['dataset_name']: d for d in cleaned_datasets}

    comparisons = []
    for b in baseline_datasets:
        name = b.get('dataset_name')
        c = cleaned_map.get(name)
        if c:
            comparisons.append(process_single_comparison(b, c))

    # Aggregate stats
    p_shifts = [c['p_value_shift'] for c in comparisons if c['p_value_shift'] is not None]
    ci_changes = [c['ci_width_change'] for c in comparisons if c['ci_width_change'] is not None]
    eff_deltas = [c['effect_size_delta'] for c in comparisons if c['effect_size_delta'] is not None]

    report = {
        "timestamp": datetime.now().isoformat(),
        "dataset_count": len(comparisons),
        "comparisons": comparisons,
        "summary": {
            "avg_p_value_shift": float(np.mean(p_shifts)) if p_shifts else None,
            "avg_ci_width_change": float(np.mean(ci_changes)) if ci_changes else None,
            "avg_effect_size_delta": float(np.mean(eff_deltas)) if eff_deltas else None,
            "inconsistency_rate": calculate_inconsistency_rate(
                [c for c in comparisons if c['p_value_shift'] is not None],
                [c for c in comparisons if c['p_value_shift'] is not None]
            )
        }
    }

    save_json_file(output_path, report)
    return report

def main():
    """Main entry point for reporting module."""
    logger.info("Reporting module loaded.")

if __name__ == "__main__":
    main()
