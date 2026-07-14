"""
Task T040: Create Comparison Report (ComparisonReport entity)

This script loads baseline metrics, cleaned metrics, and sensitivity analysis results,
calculates absolute and relative differences, aggregates metrics, and creates a
ComparisonReport entity saved to data/processed/comparison_report.json.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

# Import from sibling modules
from models import ComparisonReport, Dataset, CleaningStrategy, AnalysisResult
from reporting import load_json_file, save_json_file, calculate_p_value_shift
from utils import setup_logging, compute_file_checksum

logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Optional[Dict[str, Any]]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}")
        return None
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Optional[Dict[str, Any]]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Cleaned metrics file not found: {filepath}")
        return None
    return load_json_file(filepath)

def load_sensitivity_analysis(filepath: str = "data/processed/sensitivity_analysis.json") -> Optional[Dict[str, Any]]:
    """Load sensitivity analysis results from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Sensitivity analysis file not found: {filepath}. Proceeding without sensitivity data.")
        return None
    return load_json_file(filepath)

def calculate_absolute_diff(base_val: float, clean_val: float) -> float:
    """Calculate absolute difference between two values."""
    if base_val is None or clean_val is None or np.isnan(base_val) or np.isnan(clean_val):
        return float('nan')
    return abs(clean_val - base_val)

def calculate_relative_diff(base_val: float, clean_val: float) -> float:
    """Calculate relative difference between two values."""
    if base_val is None or clean_val is None or np.isnan(base_val) or np.isnan(clean_val) or base_val == 0:
        return float('nan')
    return (clean_val - base_val) / base_val

def aggregate_metrics_for_comparison(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate metrics from baseline and cleaned results to compute comparison statistics.
    
    Returns a dictionary with:
    - absolute_diff: dict of metric_name -> mean absolute difference
    - relative_diff: dict of metric_name -> mean relative difference
    - inconsistency_rate: proportion of tests where significance status changed
    - summary: high-level summary statistics
    """
    if not baseline_metrics or not cleaned_metrics:
        logger.error("Cannot aggregate: missing baseline or cleaned metrics.")
        return {}
    
    # Extract datasets from both
    base_datasets = baseline_metrics.get("datasets", [])
    clean_datasets = cleaned_metrics.get("datasets", [])
    
    # Create a map for quick lookup by dataset_name
    clean_map = {d.get("dataset_name"): d for d in clean_datasets}
    
    abs_diffs = {}
    rel_diffs = {}
    inconsistency_count = 0
    total_tests = 0
    
    for base_entry in base_datasets:
        ds_name = base_entry.get("dataset_name")
        if ds_name not in clean_map:
            logger.warning(f"No cleaned metrics found for dataset: {ds_name}")
            continue
        
        clean_entry = clean_map[ds_name]
        
        # Compare t-test results
        base_tests = base_entry.get("analysis", {}).get("t_tests", {})
        clean_tests = clean_entry.get("analysis", {}).get("t_tests", {})
        
        for test_name in base_tests:
            if test_name not in clean_tests:
                continue
            
            total_tests += 1
            base_p = base_tests[test_name].get("p_value")
            clean_p = clean_tests[test_name].get("p_value")
            base_ci_width = base_tests[test_name].get("ci_width")
            clean_ci_width = clean_tests[test_name].get("ci_width")
            base_effect = base_tests[test_name].get("effect_size")
            clean_effect = clean_tests[test_name].get("effect_size")
            
            # Absolute differences
            abs_p = calculate_absolute_diff(base_p, clean_p)
            abs_ci = calculate_absolute_diff(base_ci_width, clean_ci_width)
            abs_eff = calculate_absolute_diff(base_effect, clean_effect)
            
            # Relative differences
            rel_p = calculate_relative_diff(base_p, clean_p)
            rel_ci = calculate_relative_diff(base_ci_width, clean_ci_width)
            rel_eff = calculate_relative_diff(base_effect, clean_effect)
            
            # Accumulate for averaging
            for key, val in [("p_value", abs_p), ("ci_width", abs_ci), ("effect_size", abs_eff)]:
                if key not in abs_diffs:
                    abs_diffs[key] = []
                if not np.isnan(val):
                    abs_diffs[key].append(val)
            
            for key, val in [("p_value", rel_p), ("ci_width", rel_ci), ("effect_size", rel_eff)]:
                if key not in rel_diffs:
                    rel_diffs[key] = []
                if not np.isnan(val):
                    rel_diffs[key].append(val)
            
            # Inconsistency: check if significance status changed (p < 0.05)
            if base_p is not None and clean_p is not None:
                base_sig = base_p < 0.05
                clean_sig = clean_p < 0.05
                if base_sig != clean_sig:
                    inconsistency_count += 1
    
    # Calculate means
    def safe_mean(lst):
        if not lst:
            return float('nan')
        return float(np.mean(lst))
    
    final_abs = {k: safe_mean(v) for k, v in abs_diffs.items()}
    final_rel = {k: safe_mean(v) for k, v in rel_diffs.items()}
    
    inconsistency_rate = inconsistency_count / total_tests if total_tests > 0 else 0.0
    
    return {
        "absolute_diff": final_abs,
        "relative_diff": final_rel,
        "inconsistency_rate": inconsistency_rate,
        "total_comparisons": total_tests,
        "inconsistent_count": inconsistency_count
    }

def create_comparison_report(
    baseline_metrics: Optional[Dict[str, Any]],
    cleaned_metrics: Optional[Dict[str, Any]],
    sensitivity_analysis: Optional[Dict[str, Any]],
    output_path: str = "data/processed/comparison_report.json"
) -> Optional[Dict[str, Any]]:
    """
    Create a ComparisonReport entity with all required fields.
    
    Args:
        baseline_metrics: Loaded baseline metrics dict
        cleaned_metrics: Loaded cleaned metrics dict
        sensitivity_analysis: Loaded sensitivity analysis dict
        output_path: Path to save the report JSON
    
    Returns:
        The created report dict (or None if creation failed)
    """
    logger.info("Creating comparison report...")
    
    # Aggregate metrics
    aggregated = aggregate_metrics_for_comparison(baseline_metrics, cleaned_metrics)
    
    # Prepare report data
    report_data = {
        "id": f"CR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "created_at": datetime.now().isoformat(),
        "baseline_metrics": baseline_metrics,
        "cleaned_metrics": cleaned_metrics,
        "sensitivity_analysis": sensitivity_analysis,
        "absolute_diff": aggregated.get("absolute_diff", {}),
        "relative_diff": aggregated.get("relative_diff", {}),
        "inconsistency_rate": aggregated.get("inconsistency_rate", 0.0),
        "total_comparisons": aggregated.get("total_comparisons", 0),
        "inconsistent_count": aggregated.get("inconsistent_count", 0),
        "status": "complete" if baseline_metrics and cleaned_metrics else "incomplete"
    }
    
    # Save to file
    save_json_file(output_path, report_data)
    logger.info(f"Comparison report saved to: {output_path}")
    
    # Also save checksum
    checksum = compute_file_checksum(output_path)
    report_data["checksum"] = checksum
    logger.info(f"Report checksum: {checksum}")
    
    return report_data

def main():
    """Main entry point for T040."""
    setup_logging()
    
    logger.info("Starting T040: Create Comparison Report")
    
    # Load dependencies
    baseline = load_baseline_metrics()
    cleaned = load_cleaned_metrics()
    sensitivity = load_sensitivity_analysis()
    
    if not baseline:
        logger.error("Cannot create report: Baseline metrics missing.")
        return 1
    
    if not cleaned:
        logger.error("Cannot create report: Cleaned metrics missing.")
        return 1
    
    # Create report
    report = create_comparison_report(baseline, cleaned, sensitivity)
    
    if report:
        logger.info("T040 completed successfully.")
        return 0
    else:
        logger.error("T040 failed to create report.")
        return 1

if __name__ == "__main__":
    exit(main())