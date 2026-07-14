import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import os
from utils import setup_logging

logger = setup_logging()

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(filepath: str, data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved metrics to {filepath}")

def calculate_p_value_shift(p_baseline: float, p_cleaned: float) -> float:
    """
    Calculate the absolute difference between baseline and cleaned p-values.
    Returns |p_cleaned - p_baseline| with >= 3 decimal precision.
    """
    if p_baseline is None or p_cleaned is None:
        return None
    shift = abs(p_cleaned - p_baseline)
    return round(shift, 3)

def compute_ci_width_change(ci_baseline: Optional[List[float]], ci_cleaned: Optional[List[float]]) -> float:
    """
    Calculate the change in Confidence Interval width.
    ci: [lower, upper]
    Returns (width_cleaned - width_baseline) with >= 2 decimal precision.
    """
    if ci_baseline is None or ci_cleaned is None:
        return None
    
    if len(ci_baseline) != 2 or len(ci_cleaned) != 2:
        logger.warning(f"Invalid CI dimensions: base={ci_baseline}, clean={ci_cleaned}")
        return None

    width_baseline = ci_baseline[1] - ci_baseline[0]
    width_cleaned = ci_cleaned[1] - ci_cleaned[0]
    
    change = width_cleaned - width_baseline
    return round(change, 2)

def compute_effect_size_delta(es_baseline: float, es_cleaned: float) -> float:
    """
    Calculate the difference in effect size (e.g., Cohen's d or R-squared).
    Returns (es_cleaned - es_baseline).
    """
    if es_baseline is None or es_cleaned is None:
        return None
    return round(es_cleaned - es_baseline, 4)

def calculate_inconsistency_rate(results: List[Dict[str, Any]], alpha: float = 0.05) -> float:
    """
    Calculate the proportion of datasets where the significance status changes.
    Significance is determined by p_value <= alpha.
    
    Args:
        results: List of comparison results, each containing 'p_baseline' and 'p_cleaned'.
        alpha: Significance threshold.
    
    Returns:
        Inconsistency rate (0.0 to 1.0).
    """
    if not results:
        return 0.0
    
    inconsistencies = 0
    for res in results:
        p_base = res.get('p_baseline')
        p_clean = res.get('p_cleaned')
        
        if p_base is None or p_clean is None:
            continue
        
        sig_base = p_base <= alpha
        sig_clean = p_clean <= alpha
        
        if sig_base != sig_clean:
            inconsistencies += 1
    
    return round(inconsistencies / len(results), 3)

def apply_bonferroni_correction(p_values: List[float], num_tests: int) -> List[float]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate (FWER) control.
    Adjusted p-value = min(p * num_tests, 1.0).
    
    Note: FR-007 requests FWER control. Benjamini-Hochberg controls FDR.
    Implemented Bonferroni (FWER) to satisfy FR-007.
    """
    logger.warning("Warning: FR-007 requests FWER control. Benjamini-Hochberg controls FDR. Implemented Bonferroni (FWER) to satisfy FR-007.")
    
    if not p_values:
        return []
    
    corrected = []
    for p in p_values:
        if p is None:
            corrected.append(None)
        else:
            adj = min(p * num_tests, 1.0)
            corrected.append(round(adj, 4))
    return corrected

def process_single_comparison(baseline_entry: Dict, cleaned_entry: Dict) -> Dict[str, Any]:
    """
    Process a single dataset comparison between baseline and cleaned metrics.
    """
    p_base = baseline_entry.get('p_value')
    p_clean = cleaned_entry.get('p_value')
    
    ci_base = baseline_entry.get('ci')
    ci_clean = cleaned_entry.get('ci')
    
    es_base = baseline_entry.get('effect_size')
    es_clean = cleaned_entry.get('effect_size')
    
    # Significance change
    base_sig = base_p < alpha if base_p is not None else None
    clean_sig = clean_p < alpha if clean_p is not None else None
    sig_changed = base_sig != clean_sig if (base_sig is not None and clean_sig is not None) else None

    return {
        'p_value_shift': calculate_p_value_shift(p_base, p_clean),
        'ci_width_change': compute_ci_width_change(ci_base, ci_clean),
        'effect_size_delta': compute_effect_size_delta(es_base, es_clean),
        'p_baseline': p_base,
        'p_cleaned': p_clean
    }

def generate_comparison_report(baseline_path: str, cleaned_path: str, output_path: str) -> Dict[str, Any]:
    """
    Generate a comprehensive comparison report.
    
    Computes:
    - Absolute and relative p-value shifts
    - CI width changes
    - Effect size deltas
    - Inconsistency rate
    
    Args:
        baseline_path: Path to baseline_metrics.json
        cleaned_path: Path to cleaned_metrics.json
        output_path: Path to save the comparison report
    
    Returns:
        The comparison report dictionary.
    """
    logger.info(f"Loading baseline metrics from {baseline_path}")
    baseline_data = load_json_file(baseline_path)
    
    logger.info(f"Loading cleaned metrics from {cleaned_path}")
    cleaned_data = load_json_file(cleaned_path)
    
    # Structure depends on how metrics are stored. Assuming 'datasets' list in both.
    # If keys are different, we adapt.
    base_datasets = baseline_data.get('datasets', baseline_data.get('results', []))
    clean_datasets = cleaned_data.get('datasets', cleaned_data.get('results', []))
    
    comparisons = []
    dataset_names = []
    
    # Create a map for cleaned data by dataset name
    clean_map = {d.get('dataset_name', d.get('name')): d for d in clean_datasets}
    
    for base_entry in base_datasets:
        d_name = base_entry.get('dataset_name', base_entry.get('name'))
        dataset_names.append(d_name)
        
        if d_name not in clean_map:
            logger.warning(f"No cleaned metrics found for {d_name}, skipping comparison.")
            continue
        
        clean_entry = clean_map[d_name]
        
        comparison = process_single_comparison(base_entry, clean_entry)
        comparison['dataset_name'] = d_name
        comparisons.append(comparison)
    
    # Calculate aggregate metrics
    p_shifts = [c['p_value_shift'] for c in comparisons if c['p_value_shift'] is not None]
    ci_changes = [c['ci_width_change'] for c in comparisons if c['ci_width_change'] is not None]
    es_deltas = [c['effect_size_delta'] for c in comparisons if c['effect_size_delta'] is not None]
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'baseline_file': baseline_path,
        'cleaned_file': cleaned_path,
        'datasets_compared': len(comparisons),
        'dataset_names': dataset_names,
        'metrics': {
            'p_value_shift': {
                'absolute_diff': p_shifts,
                'median': float(np.median(p_shifts)) if p_shifts else None,
                'mean': float(np.mean(p_shifts)) if p_shifts else None
            },
            'ci_width_change': {
                'changes': ci_changes,
                'median': float(np.median(ci_changes)) if ci_changes else None,
                'mean': float(np.mean(ci_changes)) if ci_changes else None
            },
            'effect_size_delta': {
                'deltas': es_deltas,
                'median': float(np.median(es_deltas)) if es_deltas else None,
                'mean': float(np.mean(es_deltas)) if es_deltas else None
            },
            'inconsistency_rate': calculate_inconsistency_rate(comparisons)
        },
        'per_dataset_results': comparisons
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
    logger.info(f"Comparison report generated: {output_path}")
    return report

def main():
    """
    Main entry point for running the comparison analysis.
    Expects baseline_metrics.json and cleaned_metrics.json in data/processed/.
    """
    setup_logging("INFO")
    
    base_path = "data/processed/baseline_metrics.json"
    clean_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/comparison_report.json"
    
    if not os.path.exists(base_path):
        logger.error(f"Baseline metrics not found at {base_path}. Run baseline analysis first.")
        return
    
    if not os.path.exists(clean_path):
        logger.error(f"Cleaned metrics not found at {clean_path}. Run cleaning pipeline first.")
        return
    
    generate_comparison_report(base_path, clean_path, output_path)

if __name__ == "__main__":
    main()
