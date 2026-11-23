import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Project-relative imports based on API surface
from config import get_config
from utils.logging_config import get_logger, log_info_with_context, log_error_with_context
from models.alloy_entry import AlloyEntry

logger = get_logger(__name__)

def load_loso_results(loso_file_path: str) -> Dict[str, Any]:
    """
    Load LOSO-CV results from a JSON file.
    Expected structure:
    {
        "results": [
            {
                "system": "str",
                "r2_score": float,
                "predictions": [...],
                "actuals": [...],
                "uncertainty": float
            },
            ...
        ],
        "global_r2": float,
        "global_uncertainty": float
    }
    """
    if not os.path.exists(loso_file_path):
        raise FileNotFoundError(f"LOSO results file not found: {loso_file_path}")

    try:
        with open(loso_file_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded LOSO results from {loso_file_path}")
        return data
    except json.JSONDecodeError as e:
        log_error_with_context(f"Failed to decode JSON from {loso_file_path}", exception=e)
        raise

def calculate_system_coverage(loso_results: Dict[str, Any], min_r2_threshold: float = 0.6) -> Dict[str, Any]:
    """
    Calculate system-level coverage stats based on LOSO-CV results.
    Returns stats about which systems passed/failed the R2 threshold.
    """
    results = loso_results.get("results", [])
    if not results:
        return {
            "total_systems": 0,
            "passed_systems": 0,
            "failed_systems": 0,
            "coverage_percentage": 0.0,
            "failed_system_names": []
        }

    passed = 0
    failed = 0
    failed_names = []

    for res in results:
        r2 = res.get("r2_score", 0.0)
        system = res.get("system", "Unknown")
        if r2 >= min_r2_threshold:
            passed += 1
        else:
            failed += 1
            failed_names.append(system)

    total = len(results)
    coverage_pct = (passed / total * 100) if total > 0 else 0.0

    return {
        "total_systems": total,
        "passed_systems": passed,
        "failed_systems": failed,
        "coverage_percentage": round(coverage_pct, 2),
        "failed_system_names": failed_names,
        "min_r2_threshold": min_r2_threshold
    }

def identify_unreliable_regions(loso_results: Dict[str, Any], uncertainty_threshold: Optional[float] = None) -> Dict[str, Any]:
    """
    Identify regions (systems) where prediction uncertainty exceeds a threshold.
    If uncertainty_threshold is not provided, use the 90th percentile of observed uncertainties.
    """
    results = loso_results.get("results", [])
    if not results:
        return {
            "unreliable_systems": [],
            "threshold_used": None,
            "count": 0
        }

    uncertainties = [r.get("uncertainty", 0.0) for r in results]
    
    if uncertainty_threshold is None:
        # Calculate 90th percentile dynamically
        sorted_unc = sorted(uncertainties)
        idx = int(0.9 * len(sorted_unc))
        uncertainty_threshold = sorted_unc[min(idx, len(sorted_unc)-1)]
        logger.info(f"Using dynamic uncertainty threshold (90th percentile): {uncertainty_threshold:.4f}")

    unreliable_systems = []
    for res in results:
        unc = res.get("uncertainty", 0.0)
        system = res.get("system", "Unknown")
        r2 = res.get("r2_score", 0.0)
        
        # Flag if high uncertainty OR low R2 (even if uncertainty is moderate)
        if unc > uncertainty_threshold or r2 < 0.6:
            unreliable_systems.append({
                "system": system,
                "uncertainty": round(unc, 4),
                "r2_score": round(r2, 4),
                "reason": "high_uncertainty" if unc > uncertainty_threshold else "low_r2"
            })

    return {
        "unreliable_systems": unreliable_systems,
        "threshold_used": round(uncertainty_threshold, 4),
        "count": len(unreliable_systems)
    }

def generate_validation_report(loso_results: Dict[str, Any], 
                               coverage_stats: Dict[str, Any], 
                               unreliable_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate the comprehensive model validation report linking LOSO-CV to uncertainty metrics.
    This report is required by T022b to explicitly link LOSO-CV results to uncertainty metrics.
    """
    global_r2 = loso_results.get("global_r2", 0.0)
    global_uncertainty = loso_results.get("global_uncertainty", 0.0)
    
    # Determine if the model is reliable overall
    is_reliable = global_r2 > 0.6 and unreliable_info["count"] < (coverage_stats["total_systems"] * 0.2)
    
    report = {
        "global_metrics": {
            "global_r2_score": round(global_r2, 4),
            "global_uncertainty": round(global_uncertainty, 4),
            "is_reliable_overall": is_reliable
        },
        "system_coverage": coverage_stats,
        "unreliable_regions": unreliable_info,
        "summary": {
            "total_systems_evaluated": coverage_stats["total_systems"],
            "systems_with_reliable_predictions": coverage_stats["passed_systems"],
            "systems_flagged_as_unreliable": unreliable_info["count"],
            "recommendation": "Proceed with Pareto optimization" if is_reliable else "Review unreliable regions before optimization"
        },
        "metadata": {
            "generated_at": "T022b_validation_report",
            "task_id": "T022b",
            "description": "LOSO-CV results linked to uncertainty metrics"
        }
    }
    
    return report

def save_validation_report(report: Dict[str, Any], output_path: str) -> None:
    """
    Save the validation report to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {output_path}")

def main():
    """
    Main entry point for T022b: Link LOSO-CV results to uncertainty metrics.
    """
    parser = argparse.ArgumentParser(description="Generate model validation report from LOSO-CV results")
    parser.add_argument("--loso-file", type=str, default="data/processed/loso_test_results.json",
                        help="Path to LOSO-CV results JSON file")
    parser.add_argument("--output-file", type=str, default="data/processed/model_validation_report.json",
                        help="Path to output validation report JSON file")
    parser.add_argument("--uncertainty-threshold", type=float, default=None,
                        help="Optional fixed uncertainty threshold (default: 90th percentile)")
    
    args = parser.parse_args()
    
    log_info_with_context("Starting T022b: Linking LOSO-CV to uncertainty metrics")
    
    try:
        # 1. Load LOSO results
        loso_data = load_loso_results(args.loso_file)
        
        # 2. Calculate system coverage stats
        coverage_stats = calculate_system_coverage(loso_data, min_r2_threshold=0.6)
        
        # 3. Identify unreliable regions
        unreliable_info = identify_unreliable_regions(loso_data, uncertainty_threshold=args.uncertainty_threshold)
        
        # 4. Generate comprehensive report
        report = generate_validation_report(loso_data, coverage_stats, unreliable_info)
        
        # 5. Save report
        save_validation_report(report, args.output_file)
        
        log_info_with_context(f"T022b completed successfully. Report: {args.output_file}")
        print(json.dumps(report["summary"], indent=2))
        
    except Exception as e:
        log_error_with_context(f"T022b failed: {str(e)}", exception=e)
        sys.exit(1)

if __name__ == "__main__":
    main()
