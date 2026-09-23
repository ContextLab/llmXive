"""
T028: Generate Sensitivity Report
Generates data/results/sensitivity_report.json with significance status per threshold
and subset comparison (primary vs robustness).
Depends on: T026 (sensitivity sweep), T027c (robustness comparison).
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import utilities from existing project files
from utils import setup_logging, log_info, log_warning, log_error, load_json, save_json
from config import get_config

# Configure logging
logger = setup_logging()

def load_sensitivity_sweep_results() -> Dict[str, Any]:
    """Load results from T026 (sensitivity sweep)."""
    path = Path("data/results/sensitivity_sweep_results.json")
    if not path.exists():
        raise FileNotFoundError(f"T026 output missing: {path}")
    return load_json(path)

def load_robustness_comparison() -> Dict[str, Any]:
    """Load results from T027c (robustness comparison)."""
    path = Path("data/results/sensitivity_comparison.json")
    if not path.exists():
        raise FileNotFoundError(f"T027c output missing: {path}")
    return load_json(path)

def load_statistical_report() -> Dict[str, Any]:
    """Load primary statistical report (T022)."""
    path = Path("data/results/statistical_report.json")
    if not path.exists():
        raise FileNotFoundError(f"T022 output missing: {path}")
    return load_json(path)

def determine_significance(p_value: Optional[float], threshold: float) -> bool:
    """Determine if a result is significant at the given threshold."""
    if p_value is None:
        return False
    return p_value <= threshold

def check_borderline(p_value: Optional[float]) -> bool:
    """Check if p-value falls in the borderline range [0.04, 0.06]."""
    if p_value is None:
        return False
    return 0.04 <= p_value <= 0.06

def generate_sensitivity_report(
    sweep_results: Dict[str, Any],
    robustness_comparison: Dict[str, Any],
    stat_report: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate the full sensitivity report combining:
    1. Significance status per threshold for both metrics.
    2. Comparison between primary and robustness analysis.
    3. Borderline flags for p-values in [0.04, 0.06].
    """
    thresholds = sweep_results.get("thresholds_tested", [0.01, 0.05, 0.10])
    
    # Extract primary p-values from statistical report
    # Structure expected: results -> [metrics] -> p_value
    primary_pe_p = None
    primary_cc_p = None
    
    # Attempt to locate p-values in the stat_report structure
    if "results" in stat_report:
        for item in stat_report["results"]:
            if item.get("metric") == "perseverative_errors":
                primary_pe_p = item.get("p_value")
            elif item.get("metric") == "categories_completed":
                primary_cc_p = item.get("p_value")
    
    # Fallback if structure is flat
    if primary_pe_p is None and "perseverative_errors_p_value" in stat_report:
        primary_pe_p = stat_report["perseverative_errors_p_value"]
    if primary_cc_p is None and "categories_completed_p_value" in stat_report:
        primary_cc_p = stat_report["categories_completed_p_value"]

    report_entries = []
    borderline_found = False
    stable_count = 0

    for threshold in thresholds:
        pe_sig = determine_significance(primary_pe_p, threshold)
        cc_sig = determine_significance(primary_cc_p, threshold)
        
        # Check borderline status for this threshold
        pe_borderline = check_borderline(primary_pe_p) if primary_pe_p is not None else False
        cc_borderline = check_borderline(primary_cc_p) if primary_cc_p is not None else False
        is_sensitive = pe_borderline or cc_borderline
        
        if is_sensitive:
            borderline_found = True

        entry = {
            "threshold": threshold,
            "perseverative_errors_significant": pe_sig,
            "categories_completed_significant": cc_sig,
            "is_sensitive_to_threshold": is_sensitive
        }
        report_entries.append(entry)

    # Determine stability: if significance status changes across thresholds, it's unstable
    # For simplicity, we check if the 0.05 result matches the 0.01 and 0.10 results
    # If all are True or all are False, it's stable. If some differ, it's unstable.
    # However, usually stability means the conclusion doesn't flip at the boundary.
    # We'll define stable if the 0.05 result is the same as the 0.10 result (robustness)
    # and different from 0.01 (strictness) implies sensitivity to strictness.
    # A simpler metric: if the result is significant at 0.05, is it also at 0.10?
    # If yes, and not at 0.01, it's stable in the typical range.
    
    # Let's use the comparison from robustness analysis to inform stability
    robust_diff = robustness_comparison.get("significant_difference", False)
    
    # Calculate stability based on threshold sweep
    # If significance status is identical across all tested thresholds, it's stable.
    # If it changes, it's unstable.
    pe_significance = [e["perseverative_errors_significant"] for e in report_entries]
    cc_significance = [e["categories_completed_significant"] for e in report_entries]
    
    pe_stable = len(set(pe_significance)) == 1
    cc_stable = len(set(cc_significance)) == 1
    overall_stable = pe_stable and cc_stable and not robust_diff

    report = {
        "thresholds_tested": thresholds,
        "results": report_entries,
        "summary": {
            "stable_across_thresholds": overall_stable,
            "borderline_results_found": borderline_found,
            "robustness_check_passed": not robust_diff,
            "primary_pe_p_value": primary_pe_p,
            "primary_cc_p_value": primary_cc_p
        },
        "robustness_comparison": {
            "difference_detected": robust_diff,
            "details": robustness_comparison.get("comparison_details", {})
        }
    }

    return report

def main():
    """Main entry point for T028."""
    log_info("Starting T028: Sensitivity Report Generation")
    
    try:
        # Load dependencies
        sweep_results = load_sensitivity_sweep_results()
        robustness_comparison = load_robustness_comparison()
        stat_report = load_statistical_report()
        
        log_info("Loaded all dependency reports successfully.")
        
        # Generate report
        report = generate_sensitivity_report(sweep_results, robustness_comparison, stat_report)
        
        # Save report
        output_path = Path("data/results/sensitivity_report.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_json(report, output_path)
        
        log_info(f"T028 Complete: Sensitivity report saved to {output_path}")
        return 0
        
    except FileNotFoundError as e:
        log_error(f"Missing required dependency: {e}")
        raise
    except Exception as e:
        log_error(f"Error generating sensitivity report: {e}")
        raise

if __name__ == "__main__":
    exit(main())
