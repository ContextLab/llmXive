import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import os
from config import get_config

logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_p_value_shift(p_baseline: float, p_cleaned: float) -> float:
    """
    Compute absolute difference between cleaned and baseline p-values.
    Returns |p_cleaned - p_baseline| with >= 3 decimal precision.
    """
    if p_baseline is None or p_cleaned is None:
        logger.warning("Cannot calculate p-value shift: None values present.")
        return float('nan')
    shift = abs(p_cleaned - p_baseline)
    return round(shift, 3)

def compute_ci_width_change(ci_baseline: List[float], ci_cleaned: List[float]) -> float:
    """
    Compute change in Confidence Interval width.
    ci_baseline/cleaned expected as [lower, upper].
    Returns change in width (cleaned - baseline) with >= 2 decimal precision.
    """
    if not ci_baseline or not ci_cleaned or len(ci_baseline) != 2 or len(ci_cleaned) != 2:
        logger.warning("Cannot compute CI width change: invalid CI bounds.")
        return float('nan')
    
    width_baseline = ci_baseline[1] - ci_baseline[0]
    width_cleaned = ci_cleaned[1] - ci_cleaned[0]
    
    change = width_cleaned - width_baseline
    return round(change, 2)

def compute_effect_size_delta(es_baseline: float, es_cleaned: float) -> float:
    """
    Compute difference in effect size (Cohen's d or R^2).
    Returns es_cleaned - es_baseline.
    """
    if es_baseline is None or es_cleaned is None:
        logger.warning("Cannot compute effect size delta: None values present.")
        return float('nan')
    return round(es_cleaned - es_baseline, 3)

def calculate_inconsistency_rate(baseline_results: List[Dict], cleaned_results: List[Dict], alpha: float = 0.05) -> float:
    """
    Calculate the proportion of datasets where the significance status changes.
    Significance is defined as p <= alpha.
    
    Returns: float (0.0 to 1.0)
    """
    if not baseline_results or not cleaned_results:
        logger.warning("Cannot calculate inconsistency rate: empty result lists.")
        return 0.0
    
    if len(baseline_results) != len(cleaned_results):
        logger.error(f"Mismatch in result counts: baseline={len(baseline_results)}, cleaned={len(cleaned_results)}")
        return float('nan')
    
    inconsistencies = 0
    total = len(baseline_results)
    
    for b, c in zip(baseline_results, cleaned_results):
        p_base = b.get('p_value')
        p_clean = c.get('p_value')
        
        if p_base is None or p_clean is None:
            continue
            
        sig_base = p_base <= alpha
        sig_clean = p_clean <= alpha
        
        if sig_base != sig_clean:
            inconsistencies += 1
    
    if total == 0:
        return 0.0
    
    return round(inconsistencies / total, 3)

def apply_bonferroni_correction(p_values: List[float], m: Optional[int] = None) -> List[float]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate (FWER).
    Adjusted p-value = min(p * m, 1.0).
    
    Args:
        p_values: List of raw p-values.
        m: Number of tests. If None, m = len(p_values).
    
    Returns:
        List of adjusted p-values.
    """
    if not p_values:
        return []
    
    if m is None:
        m = len(p_values)
    
    logger.warning("Warning: FR-007 requests FWER control. Benjamini-Hochberg controls FDR. Implemented Bonferroni (FWER) to satisfy FR-007.")
    
    adjusted = []
    for p in p_values:
        adj = min(p * m, 1.0)
        adjusted.append(round(adj, 4))
    
    return adjusted

def generate_comparison_report(
    baseline_filepath: str,
    cleaned_filepath: str,
    output_filepath: str
) -> Dict[str, Any]:
    """
    Orchestrate the full metrics comparison.
    1. Load baseline and cleaned metrics.
    2. Compute p-value shifts, CI width changes, effect size deltas.
    3. Calculate inconsistency rate.
    4. Aggregate results and write to output JSON.
    
    Args:
        baseline_filepath: Path to baseline_metrics.json
        cleaned_filepath: Path to cleaned_metrics.json
        output_filepath: Path to write the comparison report
    
    Returns:
        The generated comparison report dictionary.
    """
    logger.info(f"Loading baseline metrics from {baseline_filepath}")
    baseline_data = load_json_file(baseline_filepath)
    
    logger.info(f"Loading cleaned metrics from {cleaned_filepath}")
    cleaned_data = load_json_file(cleaned_filepath)
    
    # Normalize inputs: handle both single dict and list of dicts
    baseline_list = baseline_data if isinstance(baseline_data, list) else [baseline_data]
    cleaned_list = cleaned_data if isinstance(cleaned_data, list) else [cleaned_data]
    
    comparison_results = []
    p_value_shifts = []
    ci_width_changes = []
    effect_size_deltas = []
    
    for b_item, c_item in zip(baseline_list, cleaned_list):
        # Identify dataset
        dataset_id = b_item.get('dataset_id', c_item.get('dataset_id', 'unknown'))
        strategy = c_item.get('strategy', 'cleaned')
        
        # Extract values safely
        p_base = b_item.get('p_value')
        p_clean = c_item.get('p_value')
        
        ci_base = b_item.get('ci_bounds', [None, None])
        ci_clean = c_item.get('ci_bounds', [None, None])
        
        es_base = b_item.get('effect_size')
        es_clean = c_item.get('effect_size')
        
        # Compute metrics
        p_shift = calculate_p_value_shift(p_base, p_clean)
        ci_change = compute_ci_width_change(ci_base, ci_clean)
        es_delta = compute_effect_size_delta(es_base, es_clean)
        
        # Collect for aggregation
        if not np.isnan(p_shift):
            p_value_shifts.append(p_shift)
        if not np.isnan(ci_change):
            ci_width_changes.append(ci_change)
        if not np.isnan(es_delta):
            effect_size_deltas.append(es_delta)
        
        comparison_results.append({
            "dataset_id": dataset_id,
            "strategy": strategy,
            "p_value_shift": p_shift,
            "ci_width_change": ci_change,
            "effect_size_delta": es_delta
        })
    
    # Calculate Inconsistency Rate (FR-006)
    # We need to compare significance status across all pairs
    inconsistency_rate = calculate_inconsistency_rate(baseline_list, cleaned_list)
    
    # Aggregate Summary Statistics
    summary = {
        "median_p_value_shift": float(np.median(p_value_shifts)) if p_value_shifts else None,
        "iqr_p_value_shift": float(np.subtract(*np.percentile(p_value_shifts, [75, 25]))) if len(p_value_shifts) >= 2 else None,
        "median_ci_width_change": float(np.median(ci_width_changes)) if ci_width_changes else None,
        "median_effect_size_delta": float(np.median(effect_size_deltas)) if effect_size_deltas else None,
        "inconsistency_rate": inconsistency_rate
    }
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "baseline_file": baseline_filepath,
        "cleaned_file": cleaned_filepath,
        "summary": summary,
        "per_dataset_results": comparison_results
    }
    
    # Write output
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    with open(output_filepath, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Comparison report written to {output_filepath}")
    return report

def main():
    """Entry point for running the comparison report generation."""
    setup_logging()
    config = get_config()
    
    baseline_path = config.get('BASELINE_METRICS_PATH', 'data/processed/baseline_metrics.json')
    cleaned_path = config.get('CLEANED_METRICS_PATH', 'data/processed/cleaned_metrics.json')
    output_path = config.get('COMPARISON_REPORT_PATH', 'data/processed/comparison_report.json')
    
    try:
        generate_comparison_report(baseline_path, cleaned_path, output_path)
        logger.info("Metrics comparison completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating comparison report: {e}")
        raise

if __name__ == "__main__":
    main()