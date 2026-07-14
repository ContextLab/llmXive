"""
Script to run the metrics comparison analysis (T027).
"""
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reporting import load_json_file, save_json_file, calculate_p_value_shift, compute_ci_width_change, compute_effect_size_delta, calculate_inconsistency_rate

logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned metrics file not found: {filepath}")
    return load_json_file(filepath)

def main():
    """
    Main entry point for T027 comparison analysis.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    output_path = "data/processed/t027_comparison_report.json"
    
    logger.info(f"Loading baseline metrics from {baseline_path}")
    baseline_data = load_baseline_metrics(baseline_path)
    
    logger.info(f"Loading cleaned metrics from {cleaned_path}")
    cleaned_data = load_cleaned_metrics(cleaned_path)
    
    comparisons = []
    baseline_datasets = baseline_data.get("datasets", [])
    cleaned_datasets = cleaned_data.get("datasets", [])
    
    # Map cleaned datasets by name for lookup
    cleaned_map = {d.get("dataset_name"): d for d in cleaned_datasets}
    
    for b_entry in baseline_datasets:
        ds_name = b_entry.get("dataset_name")
        c_entry = cleaned_map.get(ds_name)
        
        if not c_entry:
            logger.warning(f"No cleaned metrics found for {ds_name}, skipping comparison.")
            continue
        
        # Extract metrics for comparison
        b_tests = b_entry.get("t_test", {}) or b_entry.get("regression", {})
        c_tests = c_entry.get("t_test", {}) or c_entry.get("regression", {})
        
        # Handle both single test dicts and lists of tests
        if isinstance(b_tests, dict):
            b_tests = [b_tests]
        if isinstance(c_tests, dict):
            c_tests = [c_tests]
        
        for b_test, c_test in zip(b_tests, c_tests):
            b_p = b_test.get("p_value")
            c_p = c_test.get("p_value")
            
            b_ci = b_test.get("ci")
            c_ci = c_test.get("ci")
            
            b_ci_width = (b_ci[1] - b_ci[0]) if b_ci and len(b_ci) == 2 else None
            c_ci_width = (c_ci[1] - c_ci[0]) if c_ci and len(c_ci) == 2 else None
            
            b_es = b_test.get("effect_size")
            c_es = c_test.get("effect_size")
            
            p_shift = calculate_p_value_shift(b_p, c_p)
            ci_change = compute_ci_width_change(b_ci_width, c_ci_width)
            es_delta = compute_effect_size_delta(b_es, c_es)
            
            comparisons.append({
                "dataset_name": ds_name,
                "test_name": b_test.get("test_name", "unknown"),
                "p_value_shift": round(p_shift, 3),
                "ci_width_change": round(ci_change, 2) if ci_change is not None else None,
                "effect_size_delta": round(es_delta, 3) if es_delta is not None else None,
                "baseline_p": b_p,
                "cleaned_p": c_p
            })
    
    # Calculate overall inconsistency rate
    base_results = [b.get("t_test", b.get("regression", {})) for b in baseline_datasets]
    clean_results = [c.get("t_test", c.get("regression", {})) for c in cleaned_datasets]
    
    # Flatten if necessary
    if any(isinstance(r, list) for r in base_results):
        base_results = [item for sublist in base_results for item in (sublist if isinstance(sublist, list) else [sublist])]
    if any(isinstance(r, list) for r in clean_results):
        clean_results = [item for sublist in clean_results for item in (sublist if isinstance(sublist, list) else [sublist])]
        
    inconsistency_rate = calculate_inconsistency_rate(base_results, clean_results)
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_comparisons": len(comparisons),
        "inconsistency_rate": round(inconsistency_rate, 3),
        "comparisons": comparisons
    }
    
    save_json_file(output_path, report)
    logger.info(f"Comparison report written to {output_path}")
    print(f"Success: T027 comparison analysis complete. Output: {output_path}")

if __name__ == "__main__":
    main()