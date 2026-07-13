import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import os

logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_p_value_shift(p_baseline: float, p_cleaned: float) -> float:
    """
    Calculate the absolute difference between baseline and cleaned p-values.
    Returns |p_cleaned - p_baseline| with 3 decimal precision.
    """
    if p_baseline is None or p_cleaned is None:
        logger.warning("Cannot calculate p-value shift: missing p-values.")
        return 0.0
    
    shift = abs(p_cleaned - p_baseline)
    return round(shift, 3)

def compute_ci_width_change(ci_baseline: Optional[List[float]], ci_cleaned: Optional[List[float]]) -> float:
    """
    Calculate the change in Confidence Interval width.
    CI width is defined as (upper_bound - lower_bound).
    Returns the difference (cleaned_width - baseline_width) with 2 decimal precision.
    """
    if not ci_baseline or not ci_cleaned:
        logger.warning("Cannot compute CI width change: missing CI data.")
        return 0.0
    
    if len(ci_baseline) != 2 or len(ci_cleaned) != 2:
        logger.warning(f"Invalid CI format: expected 2 values, got {len(ci_baseline)} and {len(ci_cleaned)}")
        return 0.0

    try:
        width_baseline = abs(ci_baseline[1] - ci_baseline[0])
        width_cleaned = abs(ci_cleaned[1] - ci_cleaned[0])
        change = width_cleaned - width_baseline
        return round(change, 2)
    except (TypeError, ValueError):
        logger.warning("Non-numeric CI values encountered.")
        return 0.0

def compute_effect_size_delta(effect_baseline: float, effect_cleaned: float) -> float:
    """
    Calculate the delta in effect size (Cohen's d or R-squared).
    Returns (effect_cleaned - effect_baseline).
    """
    if effect_baseline is None or effect_cleaned is None:
        logger.warning("Cannot compute effect size delta: missing values.")
        return 0.0
    return round(effect_cleaned - effect_baseline, 4)

def calculate_inconsistency_rate(baseline_results: List[Dict[str, Any]], 
                                 cleaned_results: List[Dict[str, Any]], 
                                 significance_threshold: float = 0.05) -> float:
    """
    Calculate the inconsistency rate: proportion of datasets where significance status changes.
    Significance is determined by p <= significance_threshold.
    """
    if not baseline_results or not cleaned_results:
        logger.warning("Cannot calculate inconsistency rate: missing results.")
        return 0.0

    if len(baseline_results) != len(cleaned_results):
        logger.warning(f"Mismatch in result counts: {len(baseline_results)} vs {len(cleaned_results)}")
        return 0.0

    inconsistencies = 0
    total = len(baseline_results)

    for b_entry, c_entry in zip(baseline_results, cleaned_results):
        # Extract p-values safely
        p_b = b_entry.get('p_value') if isinstance(b_entry, dict) else None
        p_c = c_entry.get('p_value') if isinstance(c_entry, dict) else None

        if p_b is None or p_c is None:
            logger.warning(f"Skipping entry due to missing p-values: {b_entry.get('dataset_name', 'unknown')}")
            continue

        sig_b = p_b <= significance_threshold
        sig_c = p_c <= significance_threshold

        if sig_b != sig_c:
            inconsistencies += 1
            logger.debug(f"Inconsistency detected: {b_entry.get('dataset_name')} (Base: {sig_b}, Clean: {sig_c})")

    if total == 0:
        return 0.0
    
    return round(inconsistencies / total, 4)

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate (FWER).
    Adjusted p-value = min(p * n, 1.0).
    """
    if not p_values:
        return []
    
    n = len(p_values)
    corrected = []
    for p in p_values:
        corrected_p = min(p * n, 1.0)
        corrected.append(round(corrected_p, 4))
    
    logger.info(f"Applied Bonferroni correction to {n} p-values.")
    return corrected

def generate_comparison_report(baseline_path: str, cleaned_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main entry point for T027.
    Loads baseline and cleaned metrics, computes differences, and writes a comparison report.
    Computes:
      1. |p_cleaned - p_baseline|
      2. CI width change
      3. Effect size delta
      4. Inconsistency rate
    
    Args:
        baseline_path: Path to baseline_metrics.json
        cleaned_path: Path to cleaned_metrics.json
        output_path: Path to write the comparison report JSON
    
    Returns:
        The generated comparison report dictionary.
    """
    logger.info(f"Loading baseline metrics from {baseline_path}")
    logger.info(f"Loading cleaned metrics from {cleaned_path}")

    try:
        baseline_data = load_json_file(baseline_path)
        cleaned_data = load_json_file(cleaned_path)
    except FileNotFoundError as e:
        logger.error(f"Missing required artifact: {e}")
        raise

    report = {
        "timestamp": datetime.now().isoformat(),
        "source_baseline": baseline_path,
        "source_cleaned": cleaned_path,
        "metrics": []
    }

    # Normalize data structures
    # Expected structure: {'datasets': [ { 'dataset_name': ..., 't_test': { 'p_value': ..., 'ci': [...] }, ... } ]}
    # Or flat list depending on generation script. We handle both.
    
    b_datasets = baseline_data.get('datasets', baseline_data) if isinstance(baseline_data, dict) else baseline_data
    c_datasets = cleaned_data.get('datasets', cleaned_data) if isinstance(cleaned_data, dict) else cleaned_data

    if not isinstance(b_datasets, list) or not isinstance(c_datasets, list):
        logger.error("Expected 'datasets' key to be a list in both files.")
        raise ValueError("Invalid data structure in metrics files.")

    # Ensure we are comparing the same datasets (ordered by name if possible)
    b_map = {d.get('dataset_name', d.get('name', 'unknown')): d for d in b_datasets}
    c_map = {d.get('dataset_name', d.get('name', 'unknown')): d for d in c_datasets}
    
    common_keys = sorted(set(b_map.keys()) & set(c_map.keys()))
    
    if not common_keys:
        logger.warning("No common datasets found between baseline and cleaned results.")
        # Still write a report with empty metrics
        report["inconsistency_rate"] = 0.0
        report["summary"] = "No common datasets to compare."
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        return report

    p_shifts = []
    ci_changes = []
    effect_deltas = []
    inconsistency_count = 0

    for key in common_keys:
        b_entry = b_map[key]
        c_entry = c_map[key]
        
        # Extract p-values
        # Handle nested structure: t_test -> p_value or direct p_value
        b_p = b_entry.get('p_value')
        c_p = c_entry.get('p_value')
        
        if not b_p:
            b_stats = b_entry.get('t_test', {}) or b_entry.get('analysis', {}).get('t_test', {})
            b_p = b_stats.get('p_value')
        
        if not c_p:
            c_stats = c_entry.get('t_test', {}) or c_entry.get('analysis', {}).get('t_test', {})
            c_p = c_stats.get('p_value')

        # Extract CIs
        b_ci = b_entry.get('ci')
        c_ci = c_entry.get('ci')
        if not b_ci:
            b_stats = b_entry.get('t_test', {}) or b_entry.get('analysis', {}).get('t_test', {})
            b_ci = b_stats.get('ci')
        if not c_ci:
            c_stats = c_entry.get('t_test', {}) or c_entry.get('analysis', {}).get('t_test', {})
            c_ci = c_stats.get('ci')

        # Extract Effect Sizes
        b_eff = b_entry.get('effect_size')
        c_eff = c_entry.get('effect_size')
        if not b_eff:
            b_stats = b_entry.get('t_test', {}) or b_entry.get('analysis', {}).get('t_test', {})
            b_eff = b_stats.get('effect_size')
        if not c_eff:
            c_stats = c_entry.get('t_test', {}) or c_entry.get('analysis', {}).get('t_test', {})
            c_eff = c_stats.get('effect_size')

        # Compute metrics
        p_shift = calculate_p_value_shift(b_p, c_p)
        ci_change = compute_ci_width_change(b_ci, c_ci)
        eff_delta = compute_effect_size_delta(b_eff, c_eff) if b_eff is not None and c_eff is not None else 0.0

        # Check inconsistency
        if b_p is not None and c_p is not None:
            if (b_p <= 0.05) != (c_p <= 0.05):
                inconsistency_count += 1

        p_shifts.append(p_shift)
        ci_changes.append(ci_change)
        effect_deltas.append(eff_delta)

        report["metrics"].append({
            "dataset_name": key,
            "p_value_shift": p_shift,
            "ci_width_change": ci_change,
            "effect_size_delta": eff_delta,
            "baseline_p": b_p,
            "cleaned_p": c_p
        })

    # Calculate aggregate inconsistency rate
    total_comparisons = len(common_keys)
    inconsistency_rate = round(inconsistency_count / total_comparisons, 4) if total_comparisons > 0 else 0.0

    report["inconsistency_rate"] = inconsistency_rate
    report["summary"] = {
        "datasets_compared": total_comparisons,
        "inconsistencies_found": inconsistency_count,
        "mean_p_value_shift": round(np.mean(p_shifts), 4) if p_shifts else 0.0,
        "mean_ci_width_change": round(np.mean(ci_changes), 4) if ci_changes else 0.0
    }

    logger.info(f"Comparison report generated. Inconsistency Rate: {inconsistency_rate}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report written to {output_path}")
    return report

def main():
    """
    CLI entry point for T027.
    Expects environment variables or defaults:
      BASELINE_METRICS_PATH: data/processed/baseline_metrics.json
      CLEANED_METRICS_PATH: data/processed/cleaned_metrics.json
      OUTPUT_PATH: data/processed/comparison_report.json
    """
    setup_logging(logging.INFO)
    
    baseline_path = os.environ.get("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json")
    cleaned_path = os.environ.get("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json")
    output_path = os.environ.get("OUTPUT_PATH", "data/processed/comparison_report.json")

    logger.info(f"Starting T027: Metrics Comparison")
    logger.info(f"Baseline: {baseline_path}")
    logger.info(f"Cleaned: {cleaned_path}")
    logger.info(f"Output: {output_path}")

    try:
        generate_comparison_report(baseline_path, cleaned_path, output_path)
        logger.info("T027 completed successfully.")
    except Exception as e:
        logger.error(f"T027 failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
