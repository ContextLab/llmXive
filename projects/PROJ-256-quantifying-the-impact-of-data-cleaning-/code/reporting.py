import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(filepath: str, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved JSON to {filepath}")

def calculate_p_value_shift(p_baseline: float, p_cleaned: float) -> float:
    """Calculate the absolute difference in p-values."""
    if p_baseline is None or p_cleaned is None:
        return 0.0
    return round(abs(p_cleaned - p_baseline), 3)

def compute_ci_width_change(ci_baseline: Optional[List[float]], ci_cleaned: Optional[List[float]]) -> float:
    """Calculate the change in confidence interval width."""
    if not ci_baseline or not ci_cleaned or len(ci_baseline) != 2 or len(ci_cleaned) != 2:
        return 0.0
    width_baseline = abs(ci_baseline[1] - ci_baseline[0])
    width_cleaned = abs(ci_cleaned[1] - ci_cleaned[0])
    return round(width_cleaned - width_baseline, 2)

def compute_effect_size_delta(es_baseline: Optional[float], es_cleaned: Optional[float]) -> float:
    """Calculate the difference in effect size."""
    if es_baseline is None or es_cleaned is None:
        return 0.0
    return round(es_cleaned - es_baseline, 4)

def calculate_inconsistency_rate(baseline_metrics: List[Dict], cleaned_metrics: List[Dict], alpha: float = 0.05) -> float:
    """
    Calculate the proportion of datasets where significance status changes.
    Significance is defined as p-value <= alpha.
    """
    if not baseline_metrics or not cleaned_metrics:
        logger.warning("Empty metrics lists for inconsistency rate calculation.")
        return 0.0

    if len(baseline_metrics) != len(cleaned_metrics):
        logger.warning(f"Mismatched metric counts: baseline={len(baseline_metrics)}, cleaned={len(cleaned_metrics)}")
        return 0.0

    inconsistencies = 0
    total = len(baseline_metrics)

    for b_entry, c_entry in zip(baseline_metrics, cleaned_metrics):
        b_p = b_entry.get('p_value')
        c_p = c_entry.get('p_value')

        if b_p is None or c_p is None:
            continue

        b_sig = b_p <= alpha
        c_sig = c_p <= alpha

        if b_sig != c_sig:
            inconsistencies += 1

    return round(inconsistencies / total, 4) if total > 0 else 0.0

def apply_bonferroni_correction(p_values: List[float], num_tests: Optional[int] = None) -> List[float]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate (FWER) control.
    Adjusted alpha = alpha / number_of_tests.
    Returns a list of booleans indicating significance after correction.
    """
    if not p_values:
        return []
    
    # Log warning as per T028 requirement
    logger.warning("Warning: FR-007 requests FWER control. Benjamini-Hochberg controls FDR. Implemented Bonferroni (FWER) to satisfy FR-007.")
    
    adjusted_alpha = alpha / n
    return [p <= adjusted_alpha for p in p_values]

def process_single_comparison(baseline_entry: Dict, cleaned_entry: Dict, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Process a single pair of baseline and cleaned metrics entries.
    Returns a dictionary with all comparison metrics.
    """
    b_p = baseline_entry.get('p_value')
    c_p = cleaned_entry.get('p_value')
    
    b_ci = baseline_entry.get('ci')
    c_ci = cleaned_entry.get('ci')
    
    b_es = baseline_entry.get('effect_size')
    c_es = cleaned_entry.get('effect_size')
    
    p_shift = calculate_p_value_shift(b_p, c_p)
    ci_change = compute_ci_width_change(b_ci, c_ci)
    es_delta = compute_effect_size_delta(b_es, c_es)
    
    b_sig = b_p <= alpha if b_p is not None else None
    c_sig = c_p <= alpha if c_p is not None else None
    significance_changed = b_sig != c_sig if b_sig is not None and c_sig is not None else False
    
    return {
        "dataset_name": baseline_entry.get("dataset_name", "Unknown"),
        "test_type": baseline_entry.get("test_type", "Unknown"),
        "p_value_baseline": b_p,
        "p_value_cleaned": c_p,
        "p_value_shift": p_shift,
        "ci_width_baseline": abs(b_ci[1] - b_ci[0]) if b_ci and len(b_ci) == 2 else None,
        "ci_width_cleaned": abs(c_ci[1] - c_ci[0]) if c_ci and len(c_ci) == 2 else None,
        "ci_width_change": ci_change,
        "effect_size_baseline": b_es,
        "effect_size_cleaned": c_es,
        "effect_size_delta": es_delta,
        "significance_baseline": b_sig,
        "significance_cleaned": c_sig,
        "significance_changed": significance_changed
    }

def generate_comparison_report(baseline_path: str, cleaned_path: str, output_path: str, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Main function to generate the full comparison report.
    Loads baseline and cleaned metrics, computes all required differences,
    and calculates the inconsistency rate.
    """
    logger.info(f"Loading baseline metrics from: {baseline_path}")
    baseline_data = load_json_file(baseline_path)
    
    logger.info(f"Loading cleaned metrics from: {cleaned_path}")
    cleaned_data = load_json_file(cleaned_path)
    
    # Handle potential structure variations (e.g., if data is nested under 'metrics')
    b_list = baseline_data.get('datasets', baseline_data.get('results', []))
    c_list = cleaned_data.get('datasets', cleaned_data.get('results', []))
    
    if not b_list:
        raise ValueError("No baseline metrics found in the provided file.")
    if not c_list:
        raise ValueError("No cleaned metrics found in the provided file.")
    
    comparisons = []
    for b_entry, c_entry in zip(b_list, c_list):
        comp = process_single_comparison(b_entry, c_entry, alpha)
        comparisons.append(comp)
    
    inconsistency_rate = calculate_inconsistency_rate(b_list, c_list, alpha)
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "alpha_threshold": alpha,
        "total_comparisons": len(comparisons),
        "inconsistency_rate": inconsistency_rate,
        "comparisons": comparisons,
        "summary": {
            "mean_p_value_shift": round(np.mean([c['p_value_shift'] for c in comparisons]), 4) if comparisons else 0.0,
            "mean_ci_width_change": round(np.mean([c['ci_width_change'] for c in comparisons]), 4) if comparisons else 0.0,
            "mean_effect_size_delta": round(np.mean([c['effect_size_delta'] for c in comparisons]), 4) if comparisons else 0.0,
            "significant_changes_count": sum(1 for c in comparisons if c['significance_changed'])
        }
    }
    
    save_json_file(output_path, report)
    logger.info(f"Comparison report generated and saved to: {output_path}")
    
    return report

def main():
    """Entry point for the reporting module to run the comparison."""
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/comparison_report.json"
    
    if not os.path.exists(baseline_path):
        logger.error(f"Baseline metrics file not found: {baseline_path}. Cannot proceed.")
        return 1
    if not os.path.exists(cleaned_path):
        logger.error(f"Cleaned metrics file not found: {cleaned_path}. Cannot proceed.")
        return 1
    
    try:
        generate_comparison_report(baseline_path, cleaned_path, output_path)
        return 0
    except Exception as e:
        logger.error(f"Error generating comparison report: {e}")
        return 1

if __name__ == "__main__":
    exit(main())