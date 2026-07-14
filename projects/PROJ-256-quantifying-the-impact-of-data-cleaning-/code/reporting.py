import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import os

logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(data: Dict[str, Any], filepath: str) -> None:
    """Save data to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def calculate_p_value_shift(p_baseline: float, p_cleaned: float) -> float:
    """Calculate the absolute difference between baseline and cleaned p-values."""
    if p_baseline is None or p_cleaned is None:
        return None
    return round(abs(p_cleaned - p_baseline), 3)

def compute_ci_width_change(ci_baseline: List[float], ci_cleaned: List[float]) -> float:
    """Calculate the change in confidence interval width."""
    if not ci_baseline or not ci_cleaned or len(ci_baseline) != 2 or len(ci_cleaned) != 2:
        return None
    width_baseline = ci_baseline[1] - ci_baseline[0]
    width_cleaned = ci_cleaned[1] - ci_cleaned[0]
    return round(width_cleaned - width_baseline, 2)

def compute_effect_size_delta(es_baseline: float, es_cleaned: float) -> float:
    """Calculate the difference in effect size."""
    if es_baseline is None or es_cleaned is None:
        return None
    return round(es_cleaned - es_baseline, 3)

def calculate_inconsistency_rate(baseline_results: List[Dict], cleaned_results: List[Dict], alpha: float = 0.05) -> float:
    """
    Calculate the proportion of datasets where significance status changes.
    FR-006: Inconsistency Rate = proportion of datasets where significance status changes.
    """
    if not baseline_results or not cleaned_results:
        logger.warning("Empty baseline or cleaned results for inconsistency rate calculation.")
        return 0.0

    if len(baseline_results) != len(cleaned_results):
        logger.warning(f"Mismatch in number of datasets: baseline={len(baseline_results)}, cleaned={len(cleaned_results)}")
        return 0.0

    inconsistent_count = 0
    total_count = 0

    for base, clean in zip(baseline_results, cleaned_results):
        total_count += 1
        base_p = base.get('p_value')
        clean_p = clean.get('p_value')

        if base_p is None or clean_p is None:
            logger.warning(f"Skipping dataset due to missing p-values: {base.get('dataset_name', 'Unknown')}")
            continue

        base_sig = base_p < alpha
        clean_sig = clean_p < alpha

        if base_sig != clean_sig:
            inconsistent_count += 1

    if total_count == 0:
        return 0.0

    return round(inconsistent_count / total_count, 3)

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate (FWER).
    Adjusted alpha = alpha / number_of_tests.
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return []
    
    # Bonferroni: divide alpha by number of tests
    adjusted_alpha = alpha / n_tests
    
    # Log the implementation choice vs FDR
    logger.warning("Warning: FR-007 requests FWER control. Benjamini-Hochberg controls FDR. Implemented Bonferroni (FWER) to satisfy FR-007.")
    
    # Return adjusted p-values (p * n_tests) or 1.0 if > 1
    adjusted_p_values = []
    for p in p_values:
        adj_p = p * n_tests
        adjusted_p_values.append(min(adj_p, 1.0))
    
    return adjusted_p_values

def generate_comparison_report(baseline_metrics_path: str, cleaned_metrics_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main function to generate the comparison report per T027.
    Computes:
    1. |p_cleaned - p_baseline| (>=3 decimal precision)
    2. CI width change (>=2 decimal precision)
    3. Effect-size delta
    4. Inconsistency rate (proportion of datasets where significance status changes) per FR-006.
    
    Dependencies:
    - data/processed/baseline_metrics.json
    - data/processed/cleaned_metrics.json
    """
    logger.info(f"Loading baseline metrics from {baseline_metrics_path}")
    try:
        baseline_data = load_json_file(baseline_metrics_path)
    except FileNotFoundError:
        logger.error(f"Baseline metrics file not found: {baseline_metrics_path}")
        raise

    logger.info(f"Loading cleaned metrics from {cleaned_metrics_path}")
    try:
        cleaned_data = load_json_file(cleaned_metrics_path)
    except FileNotFoundError:
        logger.error(f"Cleaned metrics file not found: {cleaned_metrics_path}")
        raise

    # Structure of metrics usually contains a 'datasets' list or similar
    # We need to align them by dataset_name or index.
    # Assuming structure: { "datasets": [ { "dataset_name": "...", "analysis": { "t_test": { "p_value": ... } } } ] }
    
    baseline_datasets = baseline_data.get('datasets', baseline_data if isinstance(baseline_data, list) else [])
    cleaned_datasets = cleaned_data.get('datasets', cleaned_data if isinstance(cleaned_data, list) else [])

    if not baseline_datasets:
        logger.warning("No baseline datasets found in metrics.")
        return {"error": "No baseline datasets"}
    
    if not cleaned_datasets:
        logger.warning("No cleaned datasets found in metrics.")
        return {"error": "No cleaned datasets"}

    # Create a map for cleaned data by name for easier lookup
    cleaned_map = {d.get('dataset_name'): d for d in cleaned_datasets if d.get('dataset_name')}
    
    comparison_results = []
    p_value_shifts = []
    ci_changes = []
    effect_size_deltas = []
    inconsistency_count = 0
    total_comparisons = 0

    for base_entry in baseline_datasets:
        name = base_entry.get('dataset_name')
        if not name:
            continue
        
        clean_entry = cleaned_map.get(name)
        if not clean_entry:
            logger.warning(f"No cleaned entry found for baseline dataset: {name}")
            continue

        total_comparisons += 1

        # Extract p-values
        # Handle nested structures: analysis -> t_test -> p_value or direct p_value
        base_analysis = base_entry.get('analysis', base_entry)
        base_t_test = base_analysis.get('t_test', {})
        base_p = base_t_test.get('p_value') if isinstance(base_t_test, dict) else base_t_test

        clean_analysis = clean_entry.get('analysis', clean_entry)
        clean_t_test = clean_analysis.get('t_test', {})
        clean_p = clean_t_test.get('p_value') if isinstance(clean_t_test, dict) else clean_t_test

        # Extract CIs
        base_ci = base_t_test.get('ci') if isinstance(base_t_test, dict) else None
        clean_ci = clean_t_test.get('ci') if isinstance(clean_t_test, dict) else None

        # Extract Effect Sizes
        base_es = base_t_test.get('effect_size') if isinstance(base_t_test, dict) else None
        clean_es = clean_t_test.get('effect_size') if isinstance(clean_t_test, dict) else None

        # Calculate metrics
        p_shift = calculate_p_value_shift(base_p, clean_p) if base_p is not None and clean_p is not None else None
        ci_change = compute_ci_width_change(base_ci, clean_ci) if base_ci and clean_ci else None
        es_delta = compute_effect_size_delta(base_es, clean_es) if base_es is not None and clean_es is not None else None

        if p_shift is not None:
            p_value_shifts.append(p_shift)
        
        if ci_change is not None:
            ci_changes.append(ci_change)
        
        if es_delta is not None:
            effect_size_deltas.append(es_delta)

        # Inconsistency check
        alpha = 0.05
        if base_p is not None and clean_p is not None:
            base_sig = base_p < alpha
            clean_sig = clean_p < alpha
            if base_sig != clean_sig:
                inconsistency_count += 1

        comparison_results.append({
            "dataset_name": name,
            "p_value_shift": p_shift,
            "ci_width_change": ci_change,
            "effect_size_delta": es_delta,
            "significance_changed": (base_p is not None and clean_p is not None and (base_p < alpha) != (clean_p < alpha))
        })

    inconsistency_rate = inconsistency_count / total_comparisons if total_comparisons > 0 else 0.0

    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_datasets_compared": total_comparisons,
            "inconsistency_rate": round(inconsistency_rate, 3),
            "avg_p_value_shift": round(np.mean(p_value_shifts), 3) if p_value_shifts else None,
            "avg_ci_width_change": round(np.mean(ci_changes), 2) if ci_changes else None,
            "avg_effect_size_delta": round(np.mean(effect_size_deltas), 3) if effect_size_deltas else None
        },
        "per_dataset_comparison": comparison_results,
        "fr_006_inconsistency_rate": round(inconsistency_rate, 3)
    }

    logger.info(f"Saving comparison report to {output_path}")
    save_json_file(report, output_path)

    return report

def main():
    """Entry point for running the comparison analysis."""
    setup_logging = globals().get('setup_logging')
    if setup_logging:
        setup_logging("INFO")
    
    # Paths relative to project root
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/comparison_report.json"

    try:
        report = generate_comparison_report(baseline_path, cleaned_path, output_path)
        logger.info("Comparison report generated successfully.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Missing required artifact: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error generating comparison report: {e}")
        return 1

if __name__ == "__main__":
    import sys
    # Ensure utils is available for setup_logging if not imported globally
    from utils import setup_logging
    main()