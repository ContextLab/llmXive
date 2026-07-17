import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

# Import from project API surface
from config import get_annotated_data_path, get_processed_data_path, ensure_dirs
from utils.logging import get_experiment_logger

logger = get_experiment_logger(__name__)

# Constants for density levels as per task requirements
DENSITY_LEVELS = [1, 3, 5, 10]

def calculate_ui_completeness(ui_elements: List[Dict[str, Any]]) -> float:
    """
    Calculate UI completeness score based on the number of elements generated.
    Returns a float between 0.0 and 1.0.
    """
    if not ui_elements:
        return 0.0
    
    # Simple heuristic: more elements = higher completeness, capped at 1.0
    # Assuming a maximum of 10 elements for full completeness in this context
    max_elements = 10
    score = min(len(ui_elements) / max_elements, 1.0)
    return round(score, 4)

def calculate_metrics_for_run(
    run_data: Dict[str, Any],
    density_level: int
) -> Dict[str, Any]:
    """
    Calculate metrics for a single simulation run.
    
    Args:
        run_data: Dictionary containing simulation run results
        density_level: The information density level used (1, 3, 5, or 10)
        
    Returns:
        Dictionary containing calculated metrics including ui_element_count
    """
    metrics = {
        "density_level": density_level,
        "run_id": run_data.get("run_id", "unknown"),
        "query_id": run_data.get("query_id", "unknown"),
        "intent": run_data.get("intent", "unknown"),
        "router_confidence": run_data.get("router_confidence", 0.0),
        "latency_seconds": run_data.get("latency_seconds", 0.0),
        "generation_time_seconds": run_data.get("generation_time_seconds", 0.0),
        "total_time_seconds": run_data.get("total_time_seconds", 0.0),
        "abandoned": run_data.get("abandoned", False),
        "abandonment_time_seconds": run_data.get("abandonment_time_seconds", 0.0),
        "ui_elements": run_data.get("ui_elements", []),
        "ui_element_count": len(run_data.get("ui_elements", [])),
        "fallback_used": run_data.get("fallback_used", False),
        "fallback_no_match": run_data.get("fallback_no_match", False),
    }
    
    # Calculate UI completeness score
    metrics["ui_completeness_score"] = calculate_ui_completeness(metrics["ui_elements"])
    
    # Calculate alignment score using rubric if available
    if "alignment_score" in run_data:
        metrics["alignment_score"] = run_data["alignment_score"]
    else:
        # Placeholder if not calculated yet - should be calculated by rubric.py
        metrics["alignment_score"] = None
    
    return metrics

def aggregate_metrics_by_density(
    all_metrics: List[Dict[str, Any]]
) -> Dict[int, Dict[str, Any]]:
    """
    Aggregate metrics by density level.
    
    Args:
        all_metrics: List of metric dictionaries from multiple runs
        
    Returns:
        Dictionary mapping density levels to aggregated statistics
    """
    aggregated = {level: [] for level in DENSITY_LEVELS}
    
    for metrics in all_metrics:
        density = metrics.get("density_level")
        if density in aggregated:
            aggregated[density].append(metrics)
    
    # Calculate statistics for each density level
    summary = {}
    for density, runs in aggregated.items():
        if not runs:
            summary[density] = {
                "count": 0,
                "avg_latency": None,
                "avg_generation_time": None,
                "avg_alignment_score": None,
                "avg_ui_completeness": None,
                "total_abandoned": 0,
                "total_fallback_used": 0,
                "ui_element_counts": []
            }
            continue
        
        latencies = [r["latency_seconds"] for r in runs if r["latency_seconds"] is not None]
        gen_times = [r["generation_time_seconds"] for r in runs if r["generation_time_seconds"] is not None]
        alignment_scores = [r["alignment_score"] for r in runs if r["alignment_score"] is not None]
        completeness_scores = [r["ui_completeness_score"] for r in runs if r["ui_completeness_score"] is not None]
        ui_element_counts = [r["ui_element_count"] for r in runs]
        
        summary[density] = {
            "count": len(runs),
            "avg_latency": round(sum(latencies) / len(latencies), 4) if latencies else None,
            "avg_generation_time": round(sum(gen_times) / len(gen_times), 4) if gen_times else None,
            "avg_alignment_score": round(sum(alignment_scores) / len(alignment_scores), 4) if alignment_scores else None,
            "avg_ui_completeness": round(sum(completeness_scores) / len(completeness_scores), 4) if completeness_scores else None,
            "total_abandoned": sum(1 for r in runs if r["abandoned"]),
            "total_fallback_used": sum(1 for r in runs if r["fallback_used"]),
            "ui_element_counts": ui_element_counts,
            "min_ui_elements": min(ui_element_counts) if ui_element_counts else 0,
            "max_ui_elements": max(ui_element_counts) if ui_element_counts else 0,
            "avg_ui_elements": round(sum(ui_element_counts) / len(ui_element_counts), 4) if ui_element_counts else 0
        }
    
    return summary

def save_metrics_report(
    metrics_data: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Save metrics report to JSON file.
    
    Args:
        metrics_data: Dictionary containing metrics and aggregated statistics
        output_path: Optional custom output path
        
    Returns:
        Path to the saved report file
    """
    if output_path is None:
        output_dir = get_processed_data_path()
        ensure_dirs(output_dir)
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(Path(output_dir) / f"metrics_report_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics_data, f, indent=2, default=str)
    
    logger.info(f"Metrics report saved to {output_path}")
    return output_path

def load_simulation_results(
    simulation_log_path: str
) -> List[Dict[str, Any]]:
    """
    Load simulation results from a log file.
    
    Args:
        simulation_log_path: Path to the simulation log JSON file
        
    Returns:
        List of simulation run dictionaries
    """
    if not os.path.exists(simulation_log_path):
        raise FileNotFoundError(f"Simulation log not found at {simulation_log_path}")
    
    with open(simulation_log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both single run and multiple runs
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "runs" in data:
        return data["runs"]
    else:
        return [data]

def validate_ui_element_logging(
    metrics_report_path: str
) -> Dict[str, Any]:
    """
    Validate that ui_element_count is logged for every run at each density level.
    
    Args:
        metrics_report_path: Path to the metrics report JSON file
        
    Returns:
        Validation report with status and details
    """
    if not os.path.exists(metrics_report_path):
        return {
            "valid": False,
            "error": f"Metrics report not found at {metrics_report_path}"
        }
    
    with open(metrics_report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    # Check if aggregated data exists
    if "aggregated" not in report:
        return {
            "valid": False,
            "error": "Aggregated metrics not found in report"
        }
    
    aggregated = report["aggregated"]
    validation_results = {}
    all_valid = True
    
    for density in DENSITY_LEVELS:
        if density not in aggregated:
            validation_results[density] = {
                "valid": False,
                "error": f"No data for density level {density}"
            }
            all_valid = False
            continue
        
        level_data = aggregated[density]
        if "ui_element_counts" not in level_data:
            validation_results[density] = {
                "valid": False,
                "error": f"ui_element_counts not found for density level {density}"
            }
            all_valid = False
            continue
        
        counts = level_data["ui_element_counts"]
        count = level_data.get("count", 0)
        
        if len(counts) != count:
            validation_results[density] = {
                "valid": False,
                "error": f"Mismatch: {len(counts)} ui_element_counts but {count} total runs"
            }
            all_valid = False
        elif count == 0:
            validation_results[density] = {
                "valid": False,
                "error": f"No runs found for density level {density}"
            }
            all_valid = False
        else:
            validation_results[density] = {
                "valid": True,
                "run_count": count,
                "element_counts_logged": len(counts),
                "min_elements": min(counts),
                "max_elements": max(counts),
                "avg_elements": round(sum(counts) / len(counts), 4)
            }
    
    return {
        "valid": all_valid,
        "density_levels_checked": DENSITY_LEVELS,
        "results": validation_results,
        "summary": {
            "all_density_levels_valid": all_valid,
            "total_density_levels": len(DENSITY_LEVELS),
            "valid_density_levels": sum(1 for r in validation_results.values() if r.get("valid", False))
        }
    }

def main():
    """
    Main entry point for metrics calculation and validation.
    """
    parser = argparse.ArgumentParser(description="Calculate and validate simulation metrics")
    parser.add_argument(
        "--simulation-log",
        type=str,
        required=True,
        help="Path to the simulation log JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save the metrics report (optional)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing metrics report"
    )
    
    args = parser.parse_args()
    
    if args.validate_only:
        # Validation mode
        validation_result = validate_ui_element_logging(args.simulation_log)
        print(json.dumps(validation_result, indent=2))
        
        if validation_result["valid"]:
            logger.info("Validation PASSED: ui_element_count is logged for all runs at all density levels")
            sys.exit(0)
        else:
            logger.error("Validation FAILED: ui_element_count is missing for some runs")
            sys.exit(1)
    
    # Normal metrics calculation mode
    logger.info(f"Loading simulation results from {args.simulation_log}")
    runs = load_simulation_results(args.simulation_log)
    
    if not runs:
        logger.error("No simulation runs found in the log file")
        sys.exit(1)
    
    logger.info(f"Processing {len(runs)} simulation runs")
    
    # Calculate metrics for each run
    all_metrics = []
    for run in runs:
        density = run.get("density_level")
        if density not in DENSITY_LEVELS:
            logger.warning(f"Skipping run with invalid density level: {density}")
            continue
        
        metrics = calculate_metrics_for_run(run, density)
        all_metrics.append(metrics)
    
    if not all_metrics:
        logger.error("No valid metrics could be calculated")
        sys.exit(1)
    
    # Aggregate by density
    aggregated = aggregate_metrics_by_density(all_metrics)
    
    # Prepare report
    report = {
        "total_runs": len(all_metrics),
        "density_levels_analyzed": [d for d in DENSITY_LEVELS if d in aggregated],
        "aggregated": aggregated,
        "individual_metrics": all_metrics
    }
    
    # Save report
    report_path = save_metrics_report(report, args.output)
    
    # Validate ui_element_count logging
    validation_result = validate_ui_element_logging(report_path)
    
    print("\n" + "="*60)
    print("METRICS VALIDATION REPORT")
    print("="*60)
    print(json.dumps(validation_result, indent=2))
    
    if validation_result["valid"]:
        print("\n✓ SUCCESS: ui_element_count is logged for every run at all density levels (1, 3, 5, 10)")
        sys.exit(0)
    else:
        print("\n✗ FAILURE: ui_element_count is missing for some runs")
        sys.exit(1)

if __name__ == "__main__":
    main()