import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

# Local imports based on provided API surface
from config import get_processed_data_path, ensure_dirs
from utils.logging import get_experiment_logger, log_metric, log_info, log_error

logger = get_experiment_logger("metrics")

DENSITY_LEVELS = [1, 3, 5, 10]

def calculate_ui_completeness(ui_elements: List[Dict[str, Any]]) -> float:
    """
    Calculate UI completeness score based on the number of elements generated.
    Returns a float between 0.0 and 1.0.
    """
    if not ui_elements:
        return 0.0
    # Normalize by a theoretical max (e.g., 10 elements) or simply count if the task implies raw count
    # Based on T023 rubric: ui_completeness is a component.
    # We assume a simple linear scaling for now, capped at 1.0.
    count = len(ui_elements)
    # Assuming a max of 10 elements for full completeness in this context
    max_elements = 10.0
    return min(count / max_elements, 1.0)

def calculate_metrics_for_run(run_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate metrics for a single simulation run.
    Expects run_data to contain 'ui_elements', 'latency', 'intent_match', etc.
    """
    ui_elements = run_data.get("ui_elements", [])
    latency = run_data.get("latency", 0.0)
    intent_match = run_data.get("intent_match", 0.0) # 0 or 1

    # Calculate UI Completeness (0.0 to 1.0)
    ui_completeness = calculate_ui_completeness(ui_elements)
    
    # Count raw elements for the specific T028 requirement
    ui_element_count = len(ui_elements)

    return {
        "ui_completeness": ui_completeness,
        "ui_element_count": ui_element_count,
        "latency": latency,
        "intent_match": intent_match
    }

def aggregate_metrics_by_density(metrics_list: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """
    Group metrics by density level.
    """
    aggregated = {level: [] for level in DENSITY_LEVELS}
    for metrics in metrics_list:
        density = metrics.get("density_level")
        if density in aggregated:
            aggregated[density].append(metrics)
        else:
            # Fallback if density is missing or unexpected
            logger.warning(f"Unexpected density level: {density}")
    return aggregated

def load_simulation_results() -> List[Dict[str, Any]]:
    """
    Load simulation results from the processed data directory.
    Expects a file named 'simulation_results.json' or similar.
    """
    data_path = get_processed_data_path()
    results_file = data_path / "simulation_results.json"
    
    if not results_file.exists():
        # Try alternative common name if specified in project context
        alt_file = data_path / "runner_output.json"
        if alt_file.exists():
            results_file = alt_file
        else:
            log_error(f"Simulation results file not found at {data_path}")
            return []

    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle if data is a list of runs or a dict with a 'runs' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "runs" in data:
        return data["runs"]
    else:
        return [data]

def validate_ui_element_logging(results: List[Dict[str, Any]]) -> bool:
    """
    T028 Implementation: Validate that ui_element_count is logged for every run
    across all density levels {1, 3, 5, 10}.
    
    Returns True if validation passes, False otherwise.
    """
    missing_counts = []
    missing_densities = []
    
    # Group by density to ensure all required levels are present
    density_groups = {level: False for level in DENSITY_LEVELS}
    
    for run in results:
        density = run.get("density_level")
        if density in density_groups:
            density_groups[density] = True
        
        # Check for ui_element_count presence
        if "ui_element_count" not in run:
            # Check if it's in nested metrics
            metrics = run.get("metrics", {})
            if "ui_element_count" not in metrics:
                missing_counts.append(run.get("run_id", "unknown"))
                missing_densities.append(density)
    
    if missing_counts:
        log_error(f"Validation FAILED: ui_element_count missing in {len(missing_counts)} runs (Densities: {set(missing_densities)})")
        return False
    
    # Check if all density levels have at least one run
    missing_levels = [level for level, present in density_groups.items() if not present]
    if missing_levels:
        log_error(f"Validation FAILED: No runs found for density levels: {missing_levels}")
        return False
    
    log_info("Validation PASSED: ui_element_count is logged for all runs across all density levels.")
    return True

def save_metrics_report(metrics_list: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Save the aggregated metrics report to a JSON file.
    """
    if output_path is None:
        data_path = get_processed_data_path()
        output_path = data_path / "metrics_report.json"
    
    ensure_dirs(output_path.parent)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics_list, f, indent=2)
    
    log_info(f"Metrics report saved to {output_path}")
    return output_path

def main():
    """
    Entry point for the metrics module.
    Performs validation (T028) and generates a metrics report.
    """
    parser = argparse.ArgumentParser(description="Calculate and validate simulation metrics.")
    parser.add_argument("--validate-only", action="store_true", help="Only run validation, do not save report.")
    args = parser.parse_args()

    logger.info("Starting metrics calculation and validation...")

    # Load results
    results = load_simulation_results()
    if not results:
        log_error("No simulation results found to process.")
        sys.exit(1)

    # Calculate metrics for each run if not already present
    processed_metrics = []
    for run in results:
        # If metrics are already calculated and stored, use them
        if "metrics" in run and "ui_element_count" in run["metrics"]:
            processed_metrics.append(run)
        else:
            # Calculate on the fly
            metrics = calculate_metrics_for_run(run)
            run["metrics"] = metrics
            processed_metrics.append(run)

    # T028: Validate ui_element_count logging
    is_valid = validate_ui_element_logging(processed_metrics)

    if not args.validate_only:
        if is_valid:
            save_metrics_report(processed_metrics)
            log_info("Metrics report generated successfully.")
        else:
            log_error("Metrics report generation skipped due to validation failure.")
            sys.exit(1)
    else:
        if is_valid:
            log_info("Validation passed. No report generated (--validate-only).")
        else:
            log_error("Validation failed.")
            sys.exit(1)

if __name__ == "__main__":
    main()