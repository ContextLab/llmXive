"""
T040: Create comparison report (ComparisonReport entity) with baseline_metrics, cleaned_metrics, absolute_diff, relative_diff, sensitivity_analysis.

This script aggregates metrics from baseline and cleaned analyses, calculates differences,
and generates a structured ComparisonReport artifact.
"""
import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from local modules based on API surface
from models import ComparisonReport
from reporting import load_json_file, save_json_file, calculate_p_value_shift, compute_ci_width_change, compute_effect_size_delta
from utils import setup_logging

# Configure logging
logger = setup_logging("INFO")

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
    """Load sensitivity analysis results if available."""
    if not os.path.exists(filepath):
        logger.info("Sensitivity analysis file not found, skipping.")
        return None
    return load_json_file(filepath)

def calculate_absolute_diff(baseline_val: float, cleaned_val: float) -> float:
    """Calculate absolute difference between baseline and cleaned values."""
    if baseline_val is None or cleaned_val is None:
        return 0.0
    return abs(cleaned_val - baseline_val)

def calculate_relative_diff(baseline_val: float, cleaned_val: float) -> float:
    """Calculate relative difference (percentage change) between baseline and cleaned values."""
    if baseline_val is None or cleaned_val is None or baseline_val == 0:
        return 0.0
    return abs((cleaned_val - baseline_val) / baseline_val)

def aggregate_metrics_for_comparison(baseline_entry: Dict[str, Any], cleaned_entry: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate metrics for a single dataset comparison."""
    result = {
        "dataset_name": baseline_entry.get("dataset_name", cleaned_entry.get("dataset_name", "Unknown")),
        "baseline_p_value": baseline_entry.get("t_test", {}).get("p_value"),
        "cleaned_p_value": cleaned_entry.get("t_test", {}).get("p_value"),
        "absolute_p_diff": 0.0,
        "relative_p_diff": 0.0,
        "baseline_ci_width": 0.0,
        "cleaned_ci_width": 0.0,
        "ci_width_change": 0.0,
        "baseline_effect_size": baseline_entry.get("t_test", {}).get("effect_size"),
        "cleaned_effect_size": cleaned_entry.get("t_test", {}).get("effect_size"),
        "effect_size_delta": 0.0,
        "cleaning_strategy": cleaned_entry.get("strategy", "Unknown")
    }
    
    # Calculate differences
    result["absolute_p_diff"] = calculate_absolute_diff(
        result["baseline_p_value"], result["cleaned_p_value"]
    )
    result["relative_p_diff"] = calculate_relative_diff(
        result["baseline_p_value"], result["cleaned_p_value"]
    )
    
    # CI Widths
    baseline_ci = baseline_entry.get("t_test", {}).get("ci", [])
    cleaned_ci = cleaned_entry.get("t_test", {}).get("ci", [])
    
    if baseline_ci and len(baseline_ci) == 2:
        result["baseline_ci_width"] = baseline_ci[1] - baseline_ci[0]
    if cleaned_ci and len(cleaned_ci) == 2:
        result["cleaned_ci_width"] = cleaned_ci[1] - cleaned_ci[0]
        
    result["ci_width_change"] = compute_ci_width_change(
        result["baseline_ci_width"], result["cleaned_ci_width"]
    )
    
    # Effect Size
    result["effect_size_delta"] = compute_effect_size_delta(
        result["baseline_effect_size"], result["cleaned_effect_size"]
    )
    
    return result

def create_comparison_report(
    baseline_data: Optional[Dict[str, Any]],
    cleaned_data: Optional[Dict[str, Any]],
    sensitivity_data: Optional[Dict[str, Any]]
) -> ComparisonReport:
    """Create the final ComparisonReport entity."""
    timestamp = datetime.now().isoformat()
    
    # Aggregate comparisons
    comparisons = []
    if baseline_data and cleaned_data:
        baseline_datasets = baseline_data.get("datasets", [])
        cleaned_datasets = cleaned_data.get("datasets", [])
        
        # Create a map for cleaned datasets by name
        cleaned_map = {d.get("dataset_name"): d for d in cleaned_datasets}
        
        for b_entry in baseline_datasets:
            ds_name = b_entry.get("dataset_name")
            c_entry = cleaned_map.get(ds_name)
            
            if c_entry:
                comparison = aggregate_metrics_for_comparison(b_entry, c_entry)
                comparisons.append(comparison)
    
    # Build the report data
    report_dict = {
        "created_at": timestamp,
        "baseline_metrics_summary": baseline_data.get("summary") if baseline_data else None,
        "cleaned_metrics_summary": cleaned_data.get("summary") if cleaned_data else None,
        "comparisons": comparisons,
        "sensitivity_analysis": sensitivity_data,
        "total_datasets_analyzed": len(comparisons),
        "inconsistency_rate": 0.0  # Placeholder, could be calculated from comparisons
    }
    
    # Calculate inconsistency rate (proportion where significance changes)
    if comparisons:
        inconsistent_count = 0
        for comp in comparisons:
            base_p = comp.get("baseline_p_value")
            clean_p = comp.get("cleaned_p_value")
            if base_p is not None and clean_p is not None:
                base_sig = base_p < 0.05
                clean_sig = clean_p < 0.05
                if base_sig != clean_sig:
                    inconsistent_count += 1
        report_dict["inconsistency_rate"] = inconsistent_count / len(comparisons)
    
    # Create the ComparisonReport object
    report = ComparisonReport(
        created_at=timestamp,
        baseline_metrics=baseline_data,
        cleaned_metrics=cleaned_data,
        absolute_diffs=[c["absolute_p_diff"] for c in comparisons],
        relative_diffs=[c["relative_p_diff"] for c in comparisons],
        sensitivity_analysis=sensitivity_data,
        comparisons=comparisons,
        inconsistency_rate=report_dict["inconsistency_rate"]
    )
    
    return report

def main():
    """Main entry point for T040."""
    logger.info("Starting T040: Create comparison report")
    
    # Load data
    baseline_data = load_baseline_metrics()
    cleaned_data = load_cleaned_metrics()
    sensitivity_data = load_sensitivity_analysis()
    
    if not baseline_data:
        logger.error("Baseline metrics are missing. Cannot create comparison report.")
        sys.exit(1)
        
    if not cleaned_data:
        logger.error("Cleaned metrics are missing. Cannot create comparison report.")
        sys.exit(1)
    
    # Create report
    report = create_comparison_report(baseline_data, cleaned_data, sensitivity_data)
    
    # Save report
    output_path = "data/processed/comparison_report.json"
    save_json_file(report.model_dump(), output_path)
    
    logger.info(f"Comparison report saved to {output_path}")
    logger.info(f"Total datasets analyzed: {report.total_datasets_analyzed}")
    logger.info(f"Inconsistency rate: {report.inconsistency_rate:.4f}")
    
    return 0

if __name__ == "__main__":
    main()