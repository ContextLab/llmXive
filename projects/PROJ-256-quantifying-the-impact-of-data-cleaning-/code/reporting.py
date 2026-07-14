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
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved JSON to {filepath}")

def calculate_p_value_shift(p_baseline: float, p_cleaned: float) -> float:
    """
    Calculate the absolute difference between baseline and cleaned p-values.
    Precision: >= 3 decimal places.
    """
    if p_baseline is None or p_cleaned is None:
        logger.warning("Cannot calculate p-value shift with None values")
        return 0.0
    shift = abs(p_cleaned - p_baseline)
    return round(shift, 3)

def compute_ci_width_change(ci_baseline: Optional[List[float]], ci_cleaned: Optional[List[float]]) -> float:
    """
    Calculate the change in Confidence Interval width.
    CI width = upper - lower.
    Change = width_cleaned - width_baseline.
    Precision: >= 2 decimal places.
    """
    if not ci_baseline or not ci_cleaned:
        logger.warning("Cannot compute CI width change with missing CI data")
        return 0.0
    try:
        width_baseline = ci_baseline[1] - ci_baseline[0]
        width_cleaned = ci_cleaned[1] - ci_cleaned[0]
        change = width_cleaned - width_baseline
        return round(change, 2)
    except (IndexError, TypeError, ValueError) as e:
        logger.warning(f"Error computing CI width change: {e}")
        return 0.0

def compute_effect_size_delta(effect_baseline: Optional[float], effect_cleaned: Optional[float]) -> float:
    """
    Calculate the delta in effect size (e.g., Cohen's d or R-squared).
    Delta = effect_cleaned - effect_baseline.
    """
    if effect_baseline is None or effect_cleaned is None:
        logger.warning("Cannot compute effect size delta with None values")
        return 0.0
    delta = effect_cleaned - effect_baseline
    return round(delta, 4)

def calculate_inconsistency_rate(baseline_results: List[Dict], cleaned_results: List[Dict], alpha: float = 0.05) -> float:
    """
    Calculate the proportion of datasets where the significance status changes
    between baseline and cleaned analysis.
    Significance is determined by p-value < alpha.
    Inconsistency = (count of changed status) / (total count).
    """
    if not baseline_results or not cleaned_results:
        logger.warning("Cannot calculate inconsistency rate with empty results")
        return 0.0

    if len(baseline_results) != len(cleaned_results):
        logger.warning(f"Mismatch in result counts: {len(baseline_results)} vs {len(cleaned_results)}")
        # Proceed with min length to avoid crash, but log warning
        min_len = min(len(baseline_results), len(cleaned_results))
        baseline_results = baseline_results[:min_len]
        cleaned_results = cleaned_results[:min_len]

    changes = 0
    total = len(baseline_results)

    for base, clean in zip(baseline_results, cleaned_results):
        p_base = base.get('p_value')
        p_clean = clean.get('p_value')

        if p_base is None or p_clean is None:
            continue

        sig_base = p_base < alpha
        sig_clean = p_clean < alpha

        if sig_base != sig_clean:
            changes += 1

    if total == 0:
        return 0.0

    rate = changes / total
    logger.info(f"Inconsistency Rate calculated: {rate:.3f} ({changes}/{total})")
    return round(rate, 4)

def apply_bonferroni_correction(p_values: List[float], num_tests: Optional[int] = None) -> List[float]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate (FWER).
    Adjusted p = min(p * num_tests, 1.0).
    """
    if not p_values:
        return []

    if num_tests is None:
        num_tests = len(p_values)

    if num_tests == 0:
        return [1.0] * len(p_values)

    corrected = []
    for p in p_values:
        if p is None:
            corrected.append(1.0)
        else:
            adj = min(p * num_tests, 1.0)
            corrected.append(round(adj, 4))

    logger.info(f"Applied Bonferroni correction for {num_tests} tests")
    return corrected

def process_single_comparison(
    baseline_entry: Dict[str, Any],
    cleaned_entry: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process a single pair of baseline and cleaned entries to compute all comparison metrics.
    """
    # Extract p-values
    p_base = baseline_entry.get('p_value')
    p_clean = cleaned_entry.get('p_value')

    # Extract CIs (expecting list [lower, upper])
    ci_base = baseline_entry.get('ci')
    ci_clean = cleaned_entry.get('ci')

    # Extract effect sizes (handle different keys like 'effect_size', 'cohens_d', 'r_squared')
    eff_base = baseline_entry.get('effect_size') or baseline_entry.get('cohens_d') or baseline_entry.get('r_squared')
    eff_clean = cleaned_entry.get('effect_size') or cleaned_entry.get('cohens_d') or cleaned_entry.get('r_squared')

    # Calculate metrics
    p_shift = calculate_p_value_shift(p_base, p_clean)
    ci_change = compute_ci_width_change(ci_base, ci_clean)
    eff_delta = compute_effect_size_delta(eff_base, eff_clean)

    return {
        'dataset_name': baseline_entry.get('dataset_name', 'Unknown'),
        'p_value_shift': p_shift,
        'ci_width_change': ci_change,
        'effect_size_delta': eff_delta,
        'baseline_p_value': p_base,
        'cleaned_p_value': p_clean,
        'baseline_ci_width': (ci_base[1] - ci_base[0]) if ci_base else None,
        'cleaned_ci_width': (ci_clean[1] - ci_clean[0]) if ci_clean else None,
        'timestamp': datetime.now().isoformat()
    }

def generate_comparison_report(
    baseline_metrics_path: str,
    cleaned_metrics_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Generate a full comparison report by loading baseline and cleaned metrics,
    computing per-dataset comparisons, and calculating aggregate statistics.
    """
    logger.info(f"Loading baseline metrics from {baseline_metrics_path}")
    baseline_data = load_json_file(baseline_metrics_path)
    
    logger.info(f"Loading cleaned metrics from {cleaned_metrics_path}")
    cleaned_data = load_json_file(cleaned_metrics_path)

    # Ensure we are working with lists of datasets
    baseline_datasets = baseline_data.get('datasets', baseline_data if isinstance(baseline_data, list) else [])
    cleaned_datasets = cleaned_data.get('datasets', cleaned_data if isinstance(cleaned_data, list) else [])

    if not baseline_datasets:
        raise ValueError("No baseline datasets found in input file")
    if not cleaned_datasets:
        logger.warning("No cleaned datasets found in input file. Report will only contain baseline data.")
        cleaned_datasets = [{} for _ in baseline_datasets]

    comparisons = []
    p_shifts = []
    ci_changes = []
    eff_deltas = []
    significance_changes = 0

    # Map cleaned by dataset name for lookup if order differs
    cleaned_map = {c.get('dataset_name'): c for c in cleaned_datasets if c.get('dataset_name')}

    for base in baseline_datasets:
        name = base.get('dataset_name')
        clean = cleaned_map.get(name, {})
        
        if not clean and name:
            # Try to find by index if name missing
            idx = next((i for i, d in enumerate(baseline_datasets) if d.get('dataset_name') == name), -1)
            if idx >= 0 and idx < len(cleaned_datasets):
                clean = cleaned_datasets[idx]

        comp = process_single_comparison(base, clean)
        comparisons.append(comp)

        if comp['p_value_shift'] != 0.0:
            p_shifts.append(comp['p_value_shift'])
        if comp['ci_width_change'] != 0.0:
            ci_changes.append(comp['ci_width_change'])
        if comp['effect_size_delta'] != 0.0:
            eff_deltas.append(comp['effect_size_delta'])

        # Track significance change for inconsistency rate
        p_base = base.get('p_value')
        p_clean = clean.get('p_value')
        if p_base is not None and p_clean is not None:
            if (p_base < 0.05) != (p_clean < 0.05):
                significance_changes += 1

    # Calculate aggregate inconsistency rate
    total_count = len(baseline_datasets)
    inconsistency_rate = significance_changes / total_count if total_count > 0 else 0.0

    report = {
        'report_generated': datetime.now().isoformat(),
        'total_datasets_analyzed': total_count,
        'inconsistency_rate': round(inconsistency_rate, 4),
        'summary_statistics': {
            'p_value_shift': {
                'mean': float(np.mean(p_shifts)) if p_shifts else 0.0,
                'median': float(np.median(p_shifts)) if p_shifts else 0.0,
                'std': float(np.std(p_shifts)) if p_shifts else 0.0,
                'min': float(np.min(p_shifts)) if p_shifts else 0.0,
                'max': float(np.max(p_shifts)) if p_shifts else 0.0
            },
            'ci_width_change': {
                'mean': float(np.mean(ci_changes)) if ci_changes else 0.0,
                'median': float(np.median(ci_changes)) if ci_changes else 0.0,
                'std': float(np.std(ci_changes)) if ci_changes else 0.0
            },
            'effect_size_delta': {
                'mean': float(np.mean(eff_deltas)) if eff_deltas else 0.0,
                'median': float(np.median(eff_deltas)) if eff_deltas else 0.0,
                'std': float(np.std(eff_deltas)) if eff_deltas else 0.0
            }
        },
        'per_dataset_comparisons': comparisons
    }

    save_json_file(output_path, report)
    logger.info(f"Comparison report saved to {output_path}")
    return report