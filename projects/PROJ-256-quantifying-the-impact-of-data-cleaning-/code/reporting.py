import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(filepath: str, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def calculate_p_value_shift(p_baseline: float, p_cleaned: float) -> float:
    """
    Calculate the absolute difference between baseline and cleaned p-values.
    Requirement: ≥3 decimal precision.
    """
    if p_baseline is None or p_cleaned is None:
        return None
    diff = abs(p_cleaned - p_baseline)
    return round(diff, 3)

def compute_ci_width_change(ci_baseline: Optional[List[float]], ci_cleaned: Optional[List[float]]) -> Optional[float]:
    """
    Calculate the change in confidence interval width.
    CI width = upper_bound - lower_bound.
    Returns: (cleaned_width - baseline_width).
    Requirement: ≥2 decimal precision.
    """
    if not ci_baseline or not ci_cleaned:
        return None
    if len(ci_baseline) != 2 or len(ci_cleaned) != 2:
        return None
    
    try:
        width_baseline = abs(ci_baseline[1] - ci_baseline[0])
        width_cleaned = abs(ci_cleaned[1] - ci_cleaned[0])
        change = width_cleaned - width_baseline
        return round(change, 2)
    except (TypeError, ValueError):
        return None

def compute_effect_size_delta(effect_baseline: float, effect_cleaned: float) -> float:
    """
    Calculate the delta in effect size (e.g., Cohen's d or R²).
    """
    if effect_baseline is None or effect_cleaned is None:
        return None
    return round(effect_cleaned - effect_baseline, 3)

def calculate_inconsistency_rate(baseline_results: List[Dict], cleaned_results: List[Dict], alpha: float = 0.05) -> float:
    """
    Calculate the proportion of datasets where the significance status changes
    between baseline and cleaned results.
    Significance is defined as p_value < alpha.
    """
    if not baseline_results or not cleaned_results:
        logger.warning("No results provided for inconsistency rate calculation.")
        return 0.0
    
    if len(baseline_results) != len(cleaned_results):
        logger.warning("Mismatched number of baseline and cleaned results. Attempting to match by dataset name.")
        # Attempt to match by dataset name if lists are mismatched
        base_map = {r.get('dataset_name', r.get('dataset_id', 'unknown')): r for r in baseline_results}
        clean_map = {r.get('dataset_name', r.get('dataset_id', 'unknown')): r for r in cleaned_results}
        
        common_keys = set(base_map.keys()) & set(clean_map.keys())
        if not common_keys:
            logger.error("No common datasets found between baseline and cleaned results.")
            return 0.0
        
        comparisons = []
        for key in common_keys:
            comparisons.append((base_map[key], clean_map[key]))
    else:
        comparisons = list(zip(baseline_results, cleaned_results))

    inconsistent_count = 0
    total_count = len(comparisons)
    
    if total_count == 0:
        return 0.0

    for base_entry, clean_entry in comparisons:
        base_p = base_entry.get('p_value')
        clean_p = clean_entry.get('p_value')
        
        if base_p is None or clean_p is None:
            logger.warning(f"Missing p-value for dataset: {base_entry.get('dataset_name', 'unknown')}")
            continue
        
        base_sig = base_p < alpha
        clean_sig = clean_p < alpha
        
        if base_sig != clean_sig:
            inconsistent_count += 1

    rate = inconsistent_count / total_count
    logger.info(f"Inconsistency rate calculated: {inconsistent_count}/{total_count} = {rate:.3f}")
    return round(rate, 3)

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate (FWER) control.
    Returns: (adjusted_p_values, is_significant_list)
    """
    n = len(p_values)
    if n == 0:
        return [], []
    
    adjusted = [min(p * n, 1.0) for p in p_values]
    significant = [p < (alpha / n) for p in p_values]
    
    logger.info(f"Bonferroni correction applied: {n} tests, alpha={alpha}, adjusted_alpha={alpha/n:.4f}")
    return adjusted, significant

def process_single_comparison(base_entry: Dict, clean_entry: Dict, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Process a single pair of baseline and cleaned entries to compute all comparison metrics.
    """
    dataset_name = base_entry.get('dataset_name') or base_entry.get('dataset_id')
    base_p = base_entry.get('p_value')
    clean_p = clean_entry.get('p_value')
    
    # P-value shift
    p_shift = calculate_p_value_shift(base_p, clean_p)
    
    # CI Width Change
    base_ci = base_entry.get('ci')
    clean_ci = clean_entry.get('ci')
    ci_change = compute_ci_width_change(base_ci, clean_ci)
    
    # Effect Size Delta
    base_effect = base_entry.get('effect_size')
    clean_effect = clean_entry.get('effect_size')
    effect_delta = compute_effect_size_delta(base_effect, clean_effect)
    
    # Significance change
    base_sig = base_p < alpha if base_p is not None else None
    clean_sig = clean_p < alpha if clean_p is not None else None
    sig_changed = base_sig != clean_sig if (base_sig is not None and clean_sig is not None) else None

    return {
        'dataset_name': dataset_name,
        'baseline': {
            'p_value': base_p,
            'ci': base_ci,
            'effect_size': base_effect,
            'significant': base_sig
        },
        'cleaned': {
            'p_value': clean_p,
            'ci': clean_ci,
            'effect_size': clean_effect,
            'significant': clean_sig
        },
        'metrics': {
            'p_value_shift': p_shift,
            'ci_width_change': ci_change,
            'effect_size_delta': effect_delta,
            'significance_changed': sig_changed
        }
    }

def generate_comparison_report(baseline_path: str, cleaned_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main function to generate the full comparison report.
    1. Load baseline and cleaned metrics.
    2. Compute per-dataset comparisons.
    3. Compute global inconsistency rate.
    4. Save report to output_path.
    """
    logger.info(f"Generating comparison report from {baseline_path} and {cleaned_path}")
    
    try:
        baseline_data = load_json_file(baseline_path)
        cleaned_data = load_json_file(cleaned_path)
    except FileNotFoundError as e:
        logger.error(f"Missing required artifact: {e}")
        raise

    # Normalize data structures if they are wrapped in keys like 'datasets'
    baseline_list = baseline_data.get('datasets', baseline_data.get('results', baseline_data))
    if isinstance(baseline_list, dict):
        baseline_list = [baseline_list]
    elif not isinstance(baseline_list, list):
        baseline_list = []
        
    cleaned_list = cleaned_data.get('datasets', cleaned_data.get('results', cleaned_data))
    if isinstance(cleaned_list, dict):
        cleaned_list = [cleaned_list]
    elif not isinstance(cleaned_list, list):
        cleaned_list = []

    comparisons = []
    # Match by dataset name if possible, otherwise by index if counts match
    if len(baseline_list) == len(cleaned_list) and len(baseline_list) > 0:
        for b, c in zip(baseline_list, cleaned_list):
            # Try to match by name if they differ but we have names
            b_name = b.get('dataset_name') or b.get('dataset_id')
            c_name = c.get('dataset_name') or c.get('dataset_id')
            if b_name and c_name and b_name != c_name:
                # Attempt to find matching cleaned entry
                match = next((x for x in cleaned_list if (x.get('dataset_name') or x.get('dataset_id')) == b_name), None)
                if match:
                    c = match
            comparisons.append(process_single_comparison(b, c))
    else:
        # Fallback: try to match by name across all combinations (naive)
        base_map = {b.get('dataset_name') or b.get('dataset_id'): b for b in baseline_list}
        clean_map = {c.get('dataset_name') or c.get('dataset_id'): c for c in cleaned_list}
        common_keys = set(base_map.keys()) & set(clean_map.keys())
        for key in common_keys:
            comparisons.append(process_single_comparison(base_map[key], clean_map[key]))

    if not comparisons:
        logger.warning("No matching datasets found for comparison.")
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'datasets_compared': 0,
                'inconsistency_rate': 0.0
            },
            'comparisons': []
        }
    else:
        # Calculate global inconsistency rate
        sig_changed_count = sum(1 for c in comparisons if c['metrics']['significance_changed'] is True)
        total = len(comparisons)
        inconsistency_rate = round(sig_changed_count / total, 3) if total > 0 else 0.0
        
        # Aggregate metrics
        p_shifts = [c['metrics']['p_value_shift'] for c in comparisons if c['metrics']['p_value_shift'] is not None]
        ci_changes = [c['metrics']['ci_width_change'] for c in comparisons if c['metrics']['ci_width_change'] is not None]
        effect_deltas = [c['metrics']['effect_size_delta'] for c in comparisons if c['metrics']['effect_size_delta'] is not None]
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'datasets_compared': total,
                'inconsistency_rate': inconsistency_rate,
                'avg_p_value_shift': round(np.mean(p_shifts), 3) if p_shifts else None,
                'avg_ci_width_change': round(np.mean(ci_changes), 2) if ci_changes else None,
                'avg_effect_size_delta': round(np.mean(effect_deltas), 3) if effect_deltas else None
            },
            'comparisons': comparisons
        }

    save_json_file(output_path, report)
    logger.info(f"Comparison report saved to {output_path}")
    return report

def main():
    """
    Entry point for running the comparison report generation.
    Expects environment variables or defaults for paths.
    """
    setup_logging = None
    try:
        from utils import setup_logging
    except ImportError:
        pass
    
    if setup_logging:
        setup_logging("INFO")
    
    baseline_path = os.getenv("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json")
    cleaned_path = os.getenv("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json")
    output_path = os.getenv("COMPARISON_REPORT_PATH", "data/processed/comparison_report.json")
    
    try:
        generate_comparison_report(baseline_path, cleaned_path, output_path)
        print(f"Comparison report generated successfully at {output_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure baseline_metrics.json and cleaned_metrics.json exist in data/processed/")
        return 1
    except Exception as e:
        logger.exception("Unexpected error during comparison generation")
        print(f"Error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())