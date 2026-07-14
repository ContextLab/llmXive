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
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(filepath: str, data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved JSON file: {filepath}")

def calculate_p_value_shift(p_baseline: float, p_cleaned: float) -> float:
    """
    Calculate the absolute difference in p-values.
    Returns |p_cleaned - p_baseline| with at least 3 decimal precision.
    """
    if p_baseline is None or p_cleaned is None:
        logger.warning("Cannot calculate p-value shift: None value encountered")
        return None
    shift = abs(p_cleaned - p_baseline)
    return round(shift, 3)

def compute_ci_width_change(ci_baseline: Optional[List[float]], ci_cleaned: Optional[List[float]]) -> Optional[float]:
    """
    Calculate the change in Confidence Interval width.
    Returns (width_cleaned - width_baseline) with at least 2 decimal precision.
    CI is expected as [lower, upper].
    """
    if not ci_baseline or not ci_cleaned or len(ci_baseline) != 2 or len(ci_cleaned) != 2:
        logger.warning("Cannot compute CI width change: invalid CI data")
        return None
    
    width_baseline = ci_baseline[1] - ci_baseline[0]
    width_cleaned = ci_cleaned[1] - ci_cleaned[0]
    
    change = width_cleaned - width_baseline
    return round(change, 2)

def compute_effect_size_delta(es_baseline: Optional[float], es_cleaned: Optional[float]) -> Optional[float]:
    """
    Calculate the delta in effect size (Cohen's d or R²).
    Returns (es_cleaned - es_baseline).
    """
    if es_baseline is None or es_cleaned is None:
        logger.warning("Cannot compute effect size delta: None value encountered")
        return None
    return round(es_cleaned - es_baseline, 4)

def calculate_inconsistency_rate(baseline_results: List[Dict], cleaned_results: List[Dict], alpha: float = 0.05) -> float:
    """
    Calculate the proportion of datasets where significance status changes
    between baseline and cleaned analysis.
    
    Args:
        baseline_results: List of dicts containing baseline metrics (must have 'p_value')
        cleaned_results: List of dicts containing cleaned metrics (must have 'p_value')
        alpha: Significance threshold (default 0.05)
    
    Returns:
        Inconsistency rate as a float between 0 and 1.
    """
    if not baseline_results or not cleaned_results:
        logger.warning("Empty result lists provided for inconsistency rate calculation")
        return 0.0
    
    if len(baseline_results) != len(cleaned_results):
        logger.warning(f"Mismatch in result counts: {len(baseline_results)} baseline vs {len(cleaned_results)} cleaned. Proceeding with min length.")
        min_len = min(len(baseline_results), len(cleaned_results))
        baseline_results = baseline_results[:min_len]
        cleaned_results = cleaned_results[:min_len]

    inconsistencies = 0
    total = len(baseline_results)

    for b, c in zip(baseline_results, cleaned_results):
        p_b = b.get('p_value')
        p_c = c.get('p_value')

        if p_b is None or p_c is None:
            logger.warning(f"Skipping pair due to missing p-value: {b.get('dataset_name', 'Unknown')}")
            continue

        sig_b = p_b < alpha
        sig_c = p_c < alpha

        if sig_b != sig_c:
            inconsistencies += 1
            logger.debug(f"Inconsistency found: {b.get('dataset_name', 'Unknown')} (p_b={p_b:.4f}, p_c={p_c:.4f})")

    if total == 0:
        return 0.0
    
    rate = inconsistencies / total
    logger.info(f"Calculated Inconsistency Rate: {rate:.4f} ({inconsistencies}/{total})")
    return rate

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate (FWER) control.
    
    Note: FR-007 requests FWER control. Benjamini-Hochberg controls FDR. 
    Implemented Bonferroni (FWER) to satisfy FR-007.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance threshold
    
    Returns:
        List of adjusted p-values (capped at 1.0).
    """
    n = len(p_values)
    if n == 0:
        return []
    
    logger.warning("Warning: FR-007 requests FWER control. Benjamini-Hochberg controls FDR. Implemented Bonferroni (FWER) to satisfy FR-007.")
    
    adjusted = [min(p * n, 1.0) for p in p_values]
    return adjusted

def process_single_comparison(baseline_entry: Dict, cleaned_entry: Dict, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Process a single dataset comparison to extract metrics.
    """
    p_b = baseline_entry.get('p_value')
    p_c = cleaned_entry.get('p_value')
    
    ci_b = baseline_entry.get('ci')
    ci_c = cleaned_entry.get('ci')
    
    es_b = baseline_entry.get('effect_size')
    es_c = cleaned_entry.get('effect_size')
    
    dataset_name = baseline_entry.get('dataset_name', 'Unknown')
    
    p_shift = calculate_p_value_shift(p_b, p_c)
    ci_change = compute_ci_width_change(ci_b, ci_c)
    es_delta = compute_effect_size_delta(es_b, es_c)
    
    return {
        'dataset_name': dataset_name,
        'p_baseline': p_b,
        'p_cleaned': p_c,
        'p_shift': p_shift,
        'ci_baseline_width': (ci_b[1] - ci_b[0]) if ci_b else None,
        'ci_cleaned_width': (ci_c[1] - ci_c[0]) if ci_c else None,
        'ci_width_change': ci_change,
        'effect_size_baseline': es_b,
        'effect_size_cleaned': es_c,
        'effect_size_delta': es_delta,
        'significant_baseline': p_b < alpha if p_b is not None else None,
        'significant_cleaned': p_c < alpha if p_c is not None else None,
        'inconsistent': (p_b < alpha) != (p_c < alpha) if (p_b is not None and p_c is not None) else None
    }

def generate_comparison_report(baseline_metrics_path: str, cleaned_metrics_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main function to generate the comparison report.
    Loads baseline and cleaned metrics, computes differences, and saves the report.
    
    Args:
        baseline_metrics_path: Path to baseline_metrics.json
        cleaned_metrics_path: Path to cleaned_metrics.json
        output_path: Path where the comparison report will be saved
    
    Returns:
        The generated report dictionary.
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

    # Handle potential structure variations
    baseline_results = baseline_data.get('results', baseline_data.get('datasets', []))
    cleaned_results = cleaned_data.get('results', cleaned_data.get('datasets', []))
    
    if not baseline_results:
        logger.warning("No baseline results found in the loaded file.")
    if not cleaned_results:
        logger.warning("No cleaned results found in the loaded file.")

    comparisons = []
    for b_entry, c_entry in zip(baseline_results, cleaned_results):
        comp = process_single_comparison(b_entry, c_entry)
        comparisons.append(comp)

    # Calculate aggregate inconsistency rate
    # We need to map them by dataset name if possible, but assuming order matches for now
    # If names are present, we can be smarter, but the task implies a direct comparison per dataset
    inconsistent_count = sum(1 for c in comparisons if c.get('inconsistent') is True)
    total_comparisons = len(comparisons)
    inconsistency_rate = inconsistent_count / total_comparisons if total_comparisons > 0 else 0.0

    # Apply Bonferroni to all p-values if we want to be strict, 
    # but the task specifically asks for the rate of significance change.
    # We will include the rate in the report.

    report = {
        'generated_at': datetime.now().isoformat(),
        'baseline_source': baseline_metrics_path,
        'cleaned_source': cleaned_metrics_path,
        'summary': {
            'total_datasets': total_comparisons,
            'inconsistent_datasets': inconsistent_count,
            'inconsistency_rate': round(inconsistency_rate, 4),
            'alpha_threshold': 0.05
        },
        'per_dataset_comparisons': comparisons
    }

    save_json_file(output_path, report)
    logger.info(f"Comparison report saved to {output_path}")
    return report

def main():
    """
    Entry point for running the comparison analysis directly.
    Expects environment variables or hardcoded paths for input/output.
    """
    # Default paths based on project structure
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/comparison_report.json"

    # Check for env overrides
    baseline_path = os.environ.get('BASELINE_METRICS_PATH', baseline_path)
    cleaned_path = os.environ.get('CLEANED_METRICS_PATH', cleaned_path)
    output_path = os.environ.get('COMPARISON_OUTPUT_PATH', output_path)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        report = generate_comparison_report(baseline_path, cleaned_path, output_path)
        print(f"Comparison Report Generated: {output_path}")
        print(f"Inconsistency Rate: {report['summary']['inconsistency_rate']}")
    except Exception as e:
        logger.error(f"Failed to generate comparison report: {e}")
        raise

if __name__ == "__main__":
    main()