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
    if p_cleaned is None or p_baseline is None:
        return None
    return round(abs(p_cleaned - p_baseline), 3)

def compute_ci_width_change(ci_cleaned: List[float], ci_baseline: List[float]) -> float:
    """
    Calculate the change in confidence interval width.
    ci_cleaned and ci_baseline are expected to be [lower, upper].
    Returns (width_cleaned - width_baseline) with at least 2 decimal precision.
    """
    if not ci_cleaned or not ci_baseline or len(ci_cleaned) != 2 or len(ci_baseline) != 2:
        return None
    width_cleaned = ci_cleaned[1] - ci_cleaned[0]
    width_baseline = ci_baseline[1] - ci_baseline[0]
    return round(width_cleaned - width_baseline, 2)

def compute_effect_size_delta(effect_cleaned: float, effect_baseline: float) -> float:
    """
    Calculate the delta in effect size (Cohen's d or R²).
    Returns (effect_cleaned - effect_baseline).
    """
    if effect_cleaned is None or effect_baseline is None:
        return None
    return round(effect_cleaned - effect_baseline, 3)

def calculate_inconsistency_rate(baseline_results: List[Dict], cleaned_results: List[Dict], alpha: float = 0.05) -> float:
    """
    Calculate the proportion of datasets where the significance status changes
    between baseline and cleaned results.
    
    Args:
        baseline_results: List of dicts with 'p_value' for each dataset/test
        cleaned_results: List of dicts with 'p_value' for each dataset/test
        alpha: Significance threshold (default 0.05)
        
    Returns:
        float: Proportion of tests where significance status changed (0.0 to 1.0)
    """
    if not baseline_results or not cleaned_results:
        logger.warning("Empty baseline or cleaned results for inconsistency rate calculation")
        return 0.0
    
    if len(baseline_results) != len(cleaned_results):
        logger.warning(f"Mismatched result counts: baseline={len(baseline_results)}, cleaned={len(cleaned_results)}")
        # Attempt to align by index, ignoring extra
        min_len = min(len(baseline_results), len(cleaned_results))
        baseline_results = baseline_results[:min_len]
        cleaned_results = cleaned_results[:min_len]

    inconsistent_count = 0
    total_count = 0

    for base_entry, clean_entry in zip(baseline_results, cleaned_results):
        p_base = base_entry.get('p_value')
        p_clean = clean_entry.get('p_value')
        
        if p_base is None or p_clean is None:
            continue
        
        sig_base = p_base < alpha
        sig_clean = p_clean < alpha
        
        if sig_base != sig_clean:
            inconsistent_count += 1
        
        total_count += 1

    if total_count == 0:
        logger.warning("No valid p-values found for inconsistency rate calculation")
        return 0.0

    return round(inconsistent_count / total_count, 3)

def apply_bonferroni_correction(p_values: List[float], num_tests: int = None) -> List[float]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate (FWER) control.
    
    Args:
        p_values: List of raw p-values
        num_tests: Number of tests (defaults to len(p_values))
        
    Returns:
        List of adjusted p-values (capped at 1.0)
    """
    if not p_values:
        return []
    
    n = num_tests if num_tests is not None else len(p_values)
    if n == 0:
        logger.warning("Number of tests is zero, returning empty list")
        return []
        
    adjusted = [min(p * n, 1.0) for p in p_values]
    logger.info(f"Applied Bonferroni correction to {n} tests")
    return adjusted

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
    logger.info(f"Loading baseline metrics from {baseline_metrics_path}")
    baseline_data = load_json_file(baseline_metrics_path)
    
    logger.info(f"Loading cleaned metrics from {cleaned_metrics_path}")
    cleaned_data = load_json_file(cleaned_metrics_path)
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "baseline_file": baseline_metrics_path,
        "cleaned_file": cleaned_metrics_path,
        "datasets": [],
        "summary": {
            "total_datasets": 0,
            "inconsistency_rate": None,
            "avg_p_value_shift": None,
            "avg_ci_width_change": None,
            "avg_effect_size_delta": None
        }
    }

    baseline_datasets = baseline_data.get('datasets', [])
    cleaned_datasets = cleaned_data.get('datasets', [])
    
    # Create a map for cleaned data by dataset name for easier lookup
    cleaned_map = {}
    for cd in cleaned_datasets:
        name = cd.get('dataset_name') or cd.get('dataset_id')
        if name:
            cleaned_map[name] = cd

    p_shifts = []
    ci_changes = []
    effect_deltas = []
    inconsistent_tests = 0
    total_tests = 0

    for bd in baseline_datasets:
        dataset_name = bd.get('dataset_name') or bd.get('dataset_id')
        cleaned_entry = cleaned_map.get(dataset_name)
        
        if not cleaned_entry:
            logger.warning(f"No cleaned data found for dataset: {dataset_name}")
            continue

        comparison_entry = {
            "dataset_name": dataset_name,
            "tests": []
        }

        baseline_tests = bd.get('analysis', {}).get('tests', [])
        cleaned_tests = cleaned_entry.get('analysis', {}).get('tests', [])
        
        # Align tests by name
        base_test_map = {t.get('test_name'): t for t in baseline_tests}
        clean_test_map = {t.get('test_name'): t for t in cleaned_tests}
        
        common_tests = set(base_test_map.keys()) & set(clean_test_map.keys())
        
        for test_name in common_tests:
            bt = base_test_map[test_name]
            ct = clean_test_map[test_name]
            
            p_base = bt.get('p_value')
            p_clean = ct.get('p_value')
            
            ci_base = bt.get('ci')
            ci_clean = ct.get('ci')
            
            eff_base = bt.get('effect_size')
            eff_clean = ct.get('effect_size')
            
            p_shift = calculate_p_value_shift(p_clean, p_base)
            ci_change = compute_ci_width_change(ci_clean, ci_base) if ci_base and ci_clean else None
            eff_delta = compute_effect_size_delta(eff_clean, eff_base)
            
            # Check inconsistency
            if p_base is not None and p_clean is not None:
                sig_base = p_base < 0.05
                sig_clean = p_clean < 0.05
                if sig_base != sig_clean:
                    inconsistent_tests += 1
                total_tests += 1

            if p_shift is not None:
                p_shifts.append(p_shift)
            if ci_change is not None:
                ci_changes.append(ci_change)
            if eff_delta is not None:
                effect_deltas.append(eff_delta)

            comparison_entry['tests'].append({
                "test_name": test_name,
                "p_value_baseline": p_base,
                "p_value_cleaned": p_clean,
                "p_value_shift": p_shift,
                "ci_width_change": ci_change,
                "effect_size_delta": eff_delta,
                "inconsistent": p_base is not None and p_clean is not None and (p_base < 0.05) != (p_clean < 0.05)
            })
        
        report['datasets'].append(comparison_entry)

    report['summary']['total_datasets'] = len(report['datasets'])
    
    if total_tests > 0:
        report['summary']['inconsistency_rate'] = round(inconsistent_tests / total_tests, 3)
    else:
        report['summary']['inconsistency_rate'] = 0.0
        
    report['summary']['avg_p_value_shift'] = round(np.mean(p_shifts), 3) if p_shifts else None
    report['summary']['avg_ci_width_change'] = round(np.mean(ci_changes), 2) if ci_changes else None
    report['summary']['avg_effect_size_delta'] = round(np.mean(effect_deltas), 3) if effect_deltas else None

    # Write report to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Comparison report written to {output_path}")
    return report

def main():
    """Main entry point for the reporting module."""
    setup_logging()
    logger.info("Reporting module initialized")
    
    # Example usage (can be overridden by calling scripts)
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/comparison_report.json"
    
    if os.path.exists(baseline_path) and os.path.exists(cleaned_path):
        generate_comparison_report(baseline_path, cleaned_path, output_path)
    else:
        logger.warning(f"Required input files not found. Expected: {baseline_path}, {cleaned_path}")

if __name__ == "__main__":
    main()