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

def calculate_p_value_shift(p_cleaned: float, p_baseline: float) -> float:
    """
    Calculate the absolute difference between cleaned and baseline p-values.
    Returns |p_cleaned - p_baseline| with at least 3 decimal precision.
    """
    if not (0 < p_cleaned < 1) or not (0 < p_baseline < 1):
        logger.warning(f"Invalid p-values detected: cleaned={p_cleaned}, baseline={p_baseline}")
        return 0.0
    
    shift = abs(p_cleaned - p_baseline)
    return round(shift, 3)

def compute_ci_width_change(ci_cleaned: Tuple[float, float], ci_baseline: Tuple[float, float]) -> float:
    """
    Calculate the change in confidence interval width.
    Returns (width_cleaned - width_baseline) with at least 2 decimal precision.
    """
    if ci_cleaned is None or ci_baseline is None:
        logger.warning("CI is None, cannot compute width change")
        return 0.0
    
    try:
        width_cleaned = ci_cleaned[1] - ci_cleaned[0]
        width_baseline = ci_baseline[1] - ci_baseline[0]
        
        if not (np.isfinite(width_cleaned) and np.isfinite(width_baseline)):
            logger.warning("Non-finite CI bounds detected")
            return 0.0
        
        change = width_cleaned - width_baseline
        return round(change, 2)
    except (TypeError, IndexError) as e:
        logger.warning(f"Error computing CI width change: {e}")
        return 0.0

def compute_effect_size_delta(effect_cleaned: float, effect_baseline: float) -> float:
    """
    Calculate the difference in effect size (e.g., Cohen's d or R-squared).
    Returns (effect_cleaned - effect_baseline).
    """
    if effect_cleaned is None or effect_baseline is None:
        logger.warning("Effect size is None, cannot compute delta")
        return 0.0
    
    try:
        if not (np.isfinite(effect_cleaned) and np.isfinite(effect_baseline)):
            logger.warning("Non-finite effect sizes detected")
            return 0.0
        
        return round(effect_cleaned - effect_baseline, 3)
    except (TypeError, ValueError) as e:
        logger.warning(f"Error computing effect size delta: {e}")
        return 0.0

def calculate_inconsistency_rate(baseline_metrics: List[Dict], cleaned_metrics: List[Dict], alpha: float = 0.05) -> float:
    """
    Calculate the proportion of datasets where the significance status changes
    between baseline and cleaned analysis.
    
    Returns the inconsistency rate (0.0 to 1.0).
    """
    if not baseline_metrics or not cleaned_metrics:
        logger.warning("Empty metrics lists provided for inconsistency rate calculation")
        return 0.0
    
    # Create a mapping of dataset names to their baseline p-values
    baseline_p_map = {}
    for entry in baseline_metrics:
        # Handle different possible structures
        if isinstance(entry, dict):
            ds_name = entry.get('dataset_name') or entry.get('name') or entry.get('id')
            if ds_name:
                # Try to find p-value in various locations
                p_val = None
                if 'p_value' in entry:
                    p_val = entry['p_value']
                elif 'analysis' in entry and isinstance(entry['analysis'], dict):
                    if 't_test' in entry['analysis'] and isinstance(entry['analysis']['t_test'], dict):
                        p_val = entry['analysis']['t_test'].get('p_value')
                elif 't_test' in entry and isinstance(entry['t_test'], dict):
                    p_val = entry['t_test'].get('p_value')
                
                if p_val is not None and np.isfinite(p_val):
                    baseline_p_map[ds_name] = p_val
    
    # Count inconsistencies
    inconsistencies = 0
    total_comparable = 0
    
    for entry in cleaned_metrics:
        if isinstance(entry, dict):
            ds_name = entry.get('dataset_name') or entry.get('name') or entry.get('id')
            if ds_name and ds_name in baseline_p_map:
                total_comparable += 1
                
                # Get cleaned p-value
                clean_p = None
                if 'p_value' in entry:
                    clean_p = entry['p_value']
                elif 'analysis' in entry and isinstance(entry['analysis'], dict):
                    if 't_test' in entry['analysis'] and isinstance(entry['analysis']['t_test'], dict):
                        clean_p = entry['analysis']['t_test'].get('p_value')
                elif 't_test' in entry and isinstance(entry['t_test'], dict):
                    clean_p = entry['t_test'].get('p_value')
                
                if clean_p is not None and np.isfinite(clean_p):
                    baseline_significant = baseline_p_map[ds_name] <= alpha
                    cleaned_significant = clean_p <= alpha
                    
                    if baseline_significant != cleaned_significant:
                        inconsistencies += 1
                        logger.debug(f"Inconsistency found for {ds_name}: baseline p={baseline_p_map[ds_name]:.4f}, cleaned p={clean_p:.4f}")
    
    if total_comparable == 0:
        logger.warning("No comparable datasets found for inconsistency rate calculation")
        return 0.0
    
    rate = inconsistencies / total_comparable
    logger.info(f"Inconsistency rate: {rate:.3f} ({inconsistencies}/{total_comparable} datasets)")
    return round(rate, 3)

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate (FWER) control.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level (default 0.05)
    
    Returns:
        Tuple of (adjusted_p_values, significant_flags)
    """
    if not p_values:
        return [], []
    
    n_tests = len(p_values)
    adjusted_alpha = alpha / n_tests if n_tests > 0 else alpha
    
    adjusted_p_values = []
    significant_flags = []
    
    for p in p_values:
        adjusted_p = min(p * n_tests, 1.0)
        adjusted_p_values.append(round(adjusted_p, 3))
        significant_flags.append(adjusted_p <= alpha)
    
    logger.info(f"Applied Bonferroni correction: {n_tests} tests, adjusted alpha = {adjusted_alpha:.4f}")
    return adjusted_p_values, significant_flags

def generate_comparison_report(baseline_metrics_path: str, cleaned_metrics_path: str, output_path: str) -> Dict[str, Any]:
    """
    Generate a comprehensive comparison report between baseline and cleaned metrics.
    
    Args:
        baseline_metrics_path: Path to baseline_metrics.json
        cleaned_metrics_path: Path to cleaned_metrics.json
        output_path: Path to write the comparison report JSON
    
    Returns:
        Dictionary containing the comparison report
    """
    logger.info(f"Generating comparison report from {baseline_metrics_path} and {cleaned_metrics_path}")
    
    try:
        baseline_metrics = load_json_file(baseline_metrics_path)
        cleaned_metrics = load_json_file(cleaned_metrics_path)
    except FileNotFoundError as e:
        logger.error(f"Missing required metrics file: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in metrics file: {e}")
        raise
    
    # Ensure we're working with lists
    if isinstance(baseline_metrics, dict) and 'datasets' in baseline_metrics:
        baseline_list = baseline_metrics['datasets']
    elif isinstance(baseline_metrics, list):
        baseline_list = baseline_metrics
    else:
        baseline_list = [baseline_metrics] if baseline_metrics else []
    
    if isinstance(cleaned_metrics, dict) and 'datasets' in cleaned_metrics:
        cleaned_list = cleaned_metrics['datasets']
    elif isinstance(cleaned_metrics, list):
        cleaned_list = cleaned_metrics
    else:
        cleaned_list = [cleaned_metrics] if cleaned_metrics else []
    
    # Calculate metrics
    p_value_shifts = []
    ci_width_changes = []
    effect_size_deltas = []
    
    report_datasets = []
    
    # Create mapping for comparison
    baseline_map = {}
    for entry in baseline_list:
        ds_name = entry.get('dataset_name') or entry.get('name') or entry.get('id')
        if ds_name:
            baseline_map[ds_name] = entry
    
    for cleaned_entry in cleaned_list:
        ds_name = cleaned_entry.get('dataset_name') or cleaned_entry.get('name') or entry.get('id')
        if ds_name and ds_name in baseline_map:
            baseline_entry = baseline_map[ds_name]
            
            # Extract p-values
            base_p = None
            clean_p = None
            
            # Try various structures for baseline
            if 'p_value' in baseline_entry:
                base_p = baseline_entry['p_value']
            elif 'analysis' in baseline_entry and isinstance(baseline_entry['analysis'], dict):
                if 't_test' in baseline_entry['analysis']:
                    base_p = baseline_entry['analysis']['t_test'].get('p_value')
            elif 't_test' in baseline_entry and isinstance(baseline_entry['t_test'], dict):
                base_p = baseline_entry['t_test'].get('p_value')
            
            # Try various structures for cleaned
            if 'p_value' in cleaned_entry:
                clean_p = cleaned_entry['p_value']
            elif 'analysis' in cleaned_entry and isinstance(cleaned_entry['analysis'], dict):
                if 't_test' in cleaned_entry['analysis']:
                    clean_p = cleaned_entry['analysis']['t_test'].get('p_value')
            elif 't_test' in cleaned_entry and isinstance(cleaned_entry['t_test'], dict):
                clean_p = cleaned_entry['t_test'].get('p_value')
            
            if base_p is not None and clean_p is not None:
                p_shift = calculate_p_value_shift(clean_p, base_p)
                p_value_shifts.append(p_shift)
                
                # Extract CIs
                base_ci = None
                clean_ci = None
                
                if 'ci' in baseline_entry:
                    base_ci = baseline_entry['ci']
                elif 'analysis' in baseline_entry and isinstance(baseline_entry['analysis'], dict):
                    if 't_test' in baseline_entry['analysis']:
                        base_ci = baseline_entry['analysis']['t_test'].get('ci')
                
                if 'ci' in cleaned_entry:
                    clean_ci = cleaned_entry['ci']
                elif 'analysis' in cleaned_entry and isinstance(cleaned_entry['analysis'], dict):
                    if 't_test' in cleaned_entry['analysis']:
                        clean_ci = cleaned_entry['analysis']['t_test'].get('ci')
                
                ci_change = compute_ci_width_change(clean_ci, base_ci)
                ci_width_changes.append(ci_change)
                
                # Extract effect sizes
                base_eff = None
                clean_eff = None
                
                if 'effect_size' in baseline_entry:
                    base_eff = baseline_entry['effect_size']
                elif 'analysis' in baseline_entry and isinstance(baseline_entry['analysis'], dict):
                    if 't_test' in baseline_entry['analysis']:
                        base_eff = baseline_entry['analysis']['t_test'].get('effect_size')
                
                if 'effect_size' in cleaned_entry:
                    clean_eff = cleaned_entry['effect_size']
                elif 'analysis' in cleaned_entry and isinstance(cleaned_entry['analysis'], dict):
                    if 't_test' in cleaned_entry['analysis']:
                        clean_eff = cleaned_entry['analysis']['t_test'].get('effect_size')
                
                if base_eff is not None and clean_eff is not None:
                    eff_delta = compute_effect_size_delta(clean_eff, base_eff)
                    effect_size_deltas.append(eff_delta)
                
                report_datasets.append({
                    'dataset_name': ds_name,
                    'baseline_p_value': round(base_p, 3),
                    'cleaned_p_value': round(clean_p, 3),
                    'p_value_shift': p_shift,
                    'ci_width_change': ci_change,
                    'effect_size_delta': round(clean_eff - base_eff, 3) if base_eff is not None and clean_eff is not None else None
                })
    
    # Calculate inconsistency rate
    inconsistency_rate = calculate_inconsistency_rate(baseline_list, cleaned_list)
    
    # Calculate summary statistics
    summary = {
        'total_datasets_compared': len(report_datasets),
        'p_value_shifts': {
            'mean': float(np.mean(p_value_shifts)) if p_value_shifts else 0.0,
            'median': float(np.median(p_value_shifts)) if p_value_shifts else 0.0,
            'std': float(np.std(p_value_shifts)) if p_value_shifts else 0.0,
            'min': float(np.min(p_value_shifts)) if p_value_shifts else 0.0,
            'max': float(np.max(p_value_shifts)) if p_value_shifts else 0.0
        },
        'ci_width_changes': {
            'mean': float(np.mean(ci_width_changes)) if ci_width_changes else 0.0,
            'median': float(np.median(ci_width_changes)) if ci_width_changes else 0.0,
            'std': float(np.std(ci_width_changes)) if ci_width_changes else 0.0,
            'min': float(np.min(ci_width_changes)) if ci_width_changes else 0.0,
            'max': float(np.max(ci_width_changes)) if ci_width_changes else 0.0
        },
        'effect_size_deltas': {
            'mean': float(np.mean(effect_size_deltas)) if effect_size_deltas else 0.0,
            'median': float(np.median(effect_size_deltas)) if effect_size_deltas else 0.0,
            'std': float(np.std(effect_size_deltas)) if effect_size_deltas else 0.0,
            'min': float(np.min(effect_size_deltas)) if effect_size_deltas else 0.0,
            'max': float(np.max(effect_size_deltas)) if effect_size_deltas else 0.0
        },
        'inconsistency_rate': inconsistency_rate
    }
    
    comparison_report = {
        'generated_at': datetime.now().isoformat(),
        'baseline_metrics_file': baseline_metrics_path,
        'cleaned_metrics_file': cleaned_metrics_path,
        'summary': summary,
        'per_dataset_details': report_datasets
    }
    
    # Write report to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(comparison_report, f, indent=2)
    
    logger.info(f"Comparison report written to {output_path}")
    return comparison_report

def main():
    """Main entry point for the reporting module."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/comparison_report.json"
    
    if os.path.exists(baseline_path) and os.path.exists(cleaned_path):
        try:
            report = generate_comparison_report(baseline_path, cleaned_path, output_path)
            logger.info("Comparison report generated successfully")
            print(json.dumps(report['summary'], indent=2))
        except Exception as e:
            logger.error(f"Failed to generate comparison report: {e}")
            raise
    else:
        logger.warning(f"Required metrics files not found. Expected: {baseline_path}, {cleaned_path}")
        logger.info("Skipping comparison report generation")

if __name__ == "__main__":
    main()