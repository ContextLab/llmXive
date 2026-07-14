import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import os

logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        raise

def save_json_file(filepath: str, data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved JSON to {filepath}")

def calculate_p_value_shift(p_baseline: float, p_cleaned: float) -> float:
    """
    Calculate the absolute difference between baseline and cleaned p-values.
    Returns |p_cleaned - p_baseline| with >= 3 decimal precision.
    """
    if p_baseline is None or p_cleaned is None:
        logger.warning("Cannot calculate p-value shift: missing p-values")
        return float('nan')
    
    shift = abs(p_cleaned - p_baseline)
    return round(shift, 3)

def compute_ci_width_change(ci_baseline: List[float], ci_cleaned: List[float]) -> float:
    """
    Calculate the change in confidence interval width.
    CI width = upper - lower.
    Returns (width_cleaned - width_baseline) with >= 2 decimal precision.
    """
    if not ci_baseline or not ci_cleaned:
        logger.warning("Cannot compute CI width change: missing CI data")
        return float('nan')
    
    if len(ci_baseline) < 2 or len(ci_cleaned) < 2:
        logger.warning("CI data must have at least 2 elements (lower, upper)")
        return float('nan')
    
    width_baseline = ci_baseline[1] - ci_baseline[0]
    width_cleaned = ci_cleaned[1] - ci_cleaned[0]
    
    change = width_cleaned - width_baseline
    return round(change, 2)

def compute_effect_size_delta(effect_baseline: float, effect_cleaned: float) -> float:
    """
    Calculate the delta in effect size (e.g., Cohen's d or R-squared).
    Returns effect_cleaned - effect_baseline.
    """
    if effect_baseline is None or effect_cleaned is None:
        logger.warning("Cannot compute effect size delta: missing effect sizes")
        return float('nan')
    
    delta = effect_cleaned - effect_baseline
    return round(delta, 3)

def calculate_inconsistency_rate(baseline_results: List[Dict], cleaned_results: List[Dict], 
                                 alpha: float = 0.05) -> float:
    """
    Calculate the proportion of datasets where significance status changes
    between baseline and cleaned results.
    
    Significance is determined by p <= alpha.
    Inconsistency occurs if (p_baseline <= alpha) != (p_cleaned <= alpha).
    
    Returns the inconsistency rate (0.0 to 1.0).
    """
    if not baseline_results or not cleaned_results:
        logger.warning("Cannot calculate inconsistency rate: empty results")
        return 0.0
    
    if len(baseline_results) != len(cleaned_results):
        logger.warning(f"Mismatched result counts: {len(baseline_results)} baseline vs {len(cleaned_results)} cleaned")
        # Try to match by dataset name if available, otherwise use index
        min_len = min(len(baseline_results), len(cleaned_results))
        baseline_results = baseline_results[:min_len]
        cleaned_results = cleaned_results[:min_len]
    
    inconsistencies = 0
    total = len(baseline_results)
    
    for base_entry, clean_entry in zip(baseline_results, cleaned_results):
        # Extract p-values - handle different possible structures
        base_p = None
        clean_p = None
        
        # Try direct p_value key
        if 'p_value' in base_entry:
            base_p = base_entry['p_value']
        elif 'analysis' in base_entry and isinstance(base_entry['analysis'], dict):
            if 'p_value' in base_entry['analysis']:
                base_p = base_entry['analysis']['p_value']
        
        if 'p_value' in clean_entry:
            clean_p = clean_entry['p_value']
        elif 'analysis' in clean_entry and isinstance(clean_entry['analysis'], dict):
            if 'p_value' in clean_entry['analysis']:
                clean_p = clean_entry['analysis']['p_value']
        
        if base_p is None or clean_p is None:
            logger.warning(f"Could not extract p-values for inconsistency check: base={base_entry.get('dataset_name', 'unknown')}, clean={clean_entry.get('dataset_name', 'unknown')}")
            continue
        
        base_significant = base_p <= alpha
        clean_significant = clean_p <= alpha
        
        if base_significant != clean_significant:
            inconsistencies += 1
            logger.debug(f"Inconsistency detected: {base_entry.get('dataset_name', 'unknown')} - base_p={base_p:.4f}, clean_p={clean_p:.4f}")
    
    if total == 0:
        return 0.0
    
    return round(inconsistencies / total, 3)

def apply_bonferroni_correction(p_values: List[float], num_tests: Optional[int] = None) -> List[float]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate (FWER) control.
    
    Adjusted p-value = min(p * num_tests, 1.0)
    
    Args:
        p_values: List of raw p-values
        num_tests: Number of hypothesis tests. If None, uses len(p_values).
    
    Returns:
        List of adjusted p-values.
    """
    if not p_values:
        return []
    
    n = num_tests if num_tests is not None else len(p_values)
    
    if n == 0:
        return [1.0] * len(p_values)
    
    adjusted = []
    for p in p_values:
        if p is None:
            adjusted.append(None)
        else:
            adj_p = min(p * n, 1.0)
            adjusted.append(round(adj_p, 4))
    
    return adjusted

def process_single_comparison(baseline_entry: Dict, cleaned_entry: Dict, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Process a single dataset comparison, computing all metrics.
    
    Args:
        baseline_entry: Metrics from baseline analysis
        cleaned_entry: Metrics from cleaned analysis
        alpha: Significance threshold
    
    Returns:
        Dictionary with computed metrics
    """
    result = {
        'dataset_name': baseline_entry.get('dataset_name', cleaned_entry.get('dataset_name', 'unknown')),
        'baseline_p_value': baseline_entry.get('p_value'),
        'cleaned_p_value': cleaned_entry.get('p_value'),
        'p_value_shift': None,
        'ci_width_change': None,
        'effect_size_delta': None,
        'baseline_significant': None,
        'cleaned_significant': None,
        'inconsistent': None
    }
    
    # P-value shift
    base_p = baseline_entry.get('p_value')
    clean_p = cleaned_entry.get('p_value')
    if base_p is not None and clean_p is not None:
        result['p_value_shift'] = calculate_p_value_shift(base_p, clean_p)
        result['baseline_significant'] = base_p <= alpha
        result['cleaned_significant'] = clean_p <= alpha
        result['inconsistent'] = result['baseline_significant'] != result['cleaned_significant']
    
    # CI width change
    base_ci = baseline_entry.get('ci_95')
    clean_ci = cleaned_entry.get('ci_95')
    if base_ci and clean_ci:
        result['ci_width_change'] = compute_ci_width_change(base_ci, clean_ci)
    
    # Effect size delta
    base_effect = baseline_entry.get('effect_size')
    clean_effect = cleaned_entry.get('effect_size')
    if base_effect is not None and clean_effect is not None:
        result['effect_size_delta'] = compute_effect_size_delta(base_effect, clean_effect)
    
    return result

def generate_comparison_report(baseline_file: str, cleaned_file: str, 
                               output_file: str, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Generate a comprehensive comparison report between baseline and cleaned metrics.
    
    Args:
        baseline_file: Path to baseline_metrics.json
        cleaned_file: Path to cleaned_metrics.json
        output_file: Path to write the comparison report
        alpha: Significance threshold for inconsistency calculation
    
    Returns:
        The comparison report dictionary
    """
    logger.info(f"Loading baseline metrics from {baseline_file}")
    baseline_data = load_json_file(baseline_file)
    
    logger.info(f"Loading cleaned metrics from {cleaned_file}")
    cleaned_data = load_json_file(cleaned_file)
    
    # Extract datasets lists - handle different possible structures
    baseline_datasets = baseline_data.get('datasets', [])
    cleaned_datasets = cleaned_data.get('datasets', [])
    
    # If the structure is flat (list at root), use it directly
    if not baseline_datasets and isinstance(baseline_data, list):
        baseline_datasets = baseline_data
    if not cleaned_datasets and isinstance(cleaned_data, list):
        cleaned_datasets = cleaned_data
    
    if not baseline_datasets:
        logger.error("No baseline datasets found in metrics file")
        raise ValueError("No baseline datasets found")
    
    if not cleaned_datasets:
        logger.error("No cleaned datasets found in metrics file")
        raise ValueError("No cleaned datasets found")
    
    # Process comparisons
    comparisons = []
    dataset_names_baseline = {d.get('dataset_name', 'unknown') for d in baseline_datasets}
    dataset_names_cleaned = {d.get('dataset_name', 'unknown') for d in cleaned_datasets}
    
    logger.info(f"Baseline datasets: {dataset_names_baseline}")
    logger.info(f"Cleaned datasets: {dataset_names_cleaned}")
    
    # Match datasets by name
    matched_names = dataset_names_baseline.intersection(dataset_names_cleaned)
    unmatched_baseline = dataset_names_baseline - dataset_names_cleaned
    unmatched_cleaned = dataset_names_cleaned - dataset_names_baseline
    
    if unmatched_baseline:
        logger.warning(f"Baseline datasets with no cleaned counterpart: {unmatched_baseline}")
    if unmatched_cleaned:
        logger.warning(f"Cleaned datasets with no baseline counterpart: {unmatched_cleaned}")
    
    for name in matched_names:
        base_entry = next((d for d in baseline_datasets if d.get('dataset_name') == name), None)
        clean_entry = next((d for d in cleaned_datasets if d.get('dataset_name') == name), None)
        
        if base_entry and clean_entry:
            comparison = process_single_comparison(base_entry, clean_entry, alpha)
            comparisons.append(comparison)
    
    # Calculate aggregate metrics
    total_comparisons = len(comparisons)
    inconsistent_count = sum(1 for c in comparisons if c.get('inconsistent'))
    inconsistency_rate = round(inconsistent_count / total_comparisons, 3) if total_comparisons > 0 else 0.0
    
    # P-value shifts
    p_shifts = [c['p_value_shift'] for c in comparisons if c.get('p_value_shift') is not None]
    avg_p_shift = round(np.mean(p_shifts), 3) if p_shifts else float('nan')
    median_p_shift = round(float(np.median(p_shifts)), 3) if p_shifts else float('nan')
    
    # CI width changes
    ci_changes = [c['ci_width_change'] for c in comparisons if c.get('ci_width_change') is not None]
    avg_ci_change = round(np.mean(ci_changes), 2) if ci_changes else float('nan')
    median_ci_change = round(float(np.median(ci_changes)), 2) if ci_changes else float('nan')
    
    # Effect size deltas
    effect_deltas = [c['effect_size_delta'] for c in comparisons if c.get('effect_size_delta') is not None]
    avg_effect_delta = round(np.mean(effect_deltas), 3) if effect_deltas else float('nan')
    median_effect_delta = round(float(np.median(effect_deltas)), 3) if effect_deltas else float('nan')
    
    report = {
        'report_generated': datetime.now().isoformat(),
        'alpha_threshold': alpha,
        'summary': {
            'total_datasets_compared': total_comparisons,
            'inconsistent_count': inconsistent_count,
            'inconsistency_rate': inconsistency_rate,
            'p_value_shift': {
                'mean': avg_p_shift,
                'median': median_p_shift
            },
            'ci_width_change': {
                'mean': avg_ci_change,
                'median': median_ci_change
            },
            'effect_size_delta': {
                'mean': avg_effect_delta,
                'median': median_effect_delta
            }
        },
        'comparisons': comparisons,
        'unmatched_baseline_datasets': list(unmatched_baseline),
        'unmatched_cleaned_datasets': list(unmatched_cleaned)
    }
    
    logger.info(f"Generated comparison report with {total_comparisons} comparisons")
    logger.info(f"Inconsistency rate: {inconsistency_rate}")
    
    save_json_file(output_file, report)
    
    return report

def main():
    """Main entry point for running the comparison report generation."""
    logging.basicConfig(level=logging.INFO)
    
    # Default paths - can be overridden by environment or arguments
    baseline_file = os.getenv('BASELINE_METRICS_PATH', 'data/processed/baseline_metrics.json')
    cleaned_file = os.getenv('CLEANED_METRICS_PATH', 'data/processed/cleaned_metrics.json')
    output_file = os.getenv('COMPARISON_REPORT_PATH', 'data/processed/comparison_report.json')
    
    if not os.path.exists(baseline_file):
        logger.error(f"Baseline metrics file not found: {baseline_file}")
        logger.info("Please ensure baseline analysis has been run first (T012)")
        return 1
    
    if not os.path.exists(cleaned_file):
        logger.error(f"Cleaned metrics file not found: {cleaned_file}")
        logger.info("Please ensure cleaned analysis has been run first (T023)")
        return 1
    
    try:
        report = generate_comparison_report(baseline_file, cleaned_file, output_file)
        logger.info(f"Comparison report successfully written to {output_file}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate comparison report: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())