"""
Statistical Summary Persistence Module.

Implements Constitution IV compliance by persisting statistical analysis results
to a YAML file with the required schema structure.
"""
import os
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
import logging

from src.utils.logging import get_logger
from src.utils.checksum_utils import update_artifact_hash
from src.utils.versioning import update_artifact_timestamp

logger = get_logger(__name__)

# Default path relative to project root
DEFAULT_OUTPUT_PATH = "data/statistical_summary.yaml"


def create_empty_summary() -> Dict[str, Any]:
    """
    Create an empty statistical summary structure compliant with the schema.
    
    Returns:
        Dict with task_results (empty list) and aggregate_stats (zeros/nulls).
    """
    return {
        "task_results": [],
        "aggregate_stats": {
            "mean_accuracy_diff": None,
            "p_value": None,
            "effect_size": None,
            "ci_lower": None,
            "ci_upper": None
        }
    }


def save_statistical_summary(
    summary_data: Dict[str, Any],
    output_path: str = DEFAULT_OUTPUT_PATH
) -> str:
    """
    Save statistical summary to a YAML file.
    
    Args:
        summary_data: Dictionary containing task_results and aggregate_stats.
        output_path: Relative path to the output YAML file.
        
    Returns:
        Absolute path to the saved file.
    """
    abs_path = Path(output_path).resolve()
    
    # Ensure directory exists
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add metadata
    summary_data["metadata"] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": "1.0",
        "source": "statistical_summary.py"
    }
    
    # Write YAML
    with open(abs_path, 'w', encoding='utf-8') as f:
        yaml.dump(summary_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    logger.info(f"Statistical summary saved to {abs_path}")
    
    # Update checksum tracking (Constitution III/V)
    try:
        update_artifact_hash(str(abs_path))
        update_artifact_timestamp(str(abs_path))
    except Exception as e:
        logger.warning(f"Could not update state tracking for {abs_path}: {e}")
        
    return str(abs_path)


def load_statistical_summary(
    input_path: str = DEFAULT_OUTPUT_PATH
) -> Optional[Dict[str, Any]]:
    """
    Load statistical summary from a YAML file.
    
    Args:
        input_path: Relative path to the input YAML file.
        
    Returns:
        Dictionary with summary data, or None if file doesn't exist.
    """
    abs_path = Path(input_path).resolve()
    
    if not abs_path.exists():
        logger.warning(f"Statistical summary file not found: {abs_path}")
        return None
        
    with open(abs_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        
    return data


def add_task_result(
    summary_data: Dict[str, Any],
    task_id: str,
    accuracy: float,
    condition: str
) -> Dict[str, Any]:
    """
    Add a single task result to the summary.
    
    Args:
        summary_data: Existing summary dictionary.
        task_id: Unique identifier for the task.
        accuracy: Computed accuracy metric.
        condition: Experimental condition (e.g., "heterogeneous", "unified").
        
    Returns:
        Updated summary dictionary.
    """
    if "task_results" not in summary_data:
        summary_data["task_results"] = []
        
    result_entry = {
        "task_id": task_id,
        "accuracy": float(accuracy),
        "condition": str(condition),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    summary_data["task_results"].append(result_entry)
    logger.debug(f"Added result for {task_id} ({condition}): accuracy={accuracy}")
    
    return summary_data


def update_aggregate_stats(
    summary_data: Dict[str, Any],
    mean_accuracy_diff: float,
    p_value: float,
    effect_size: float,
    ci_lower: float,
    ci_upper: float
) -> Dict[str, Any]:
    """
    Update the aggregate statistics section of the summary.
    
    Args:
        summary_data: Existing summary dictionary.
        mean_accuracy_diff: Mean difference in accuracy between conditions.
        p_value: P-value from statistical test.
        effect_size: Effect size (e.g., r from Wilcoxon).
        ci_lower: Lower bound of 95% confidence interval.
        ci_upper: Upper bound of 95% confidence interval.
        
    Returns:
        Updated summary dictionary.
    """
    summary_data["aggregate_stats"] = {
        "mean_accuracy_diff": float(mean_accuracy_diff),
        "p_value": float(p_value),
        "effect_size": float(effect_size),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper)
    }
    
    logger.debug("Updated aggregate statistics")
    return summary_data


def generate_summary_from_analysis(
    task_results_list: List[Dict[str, Any]],
    analysis_results: Dict[str, float]
) -> Dict[str, Any]:
    """
    Generate a complete summary dictionary from raw analysis data.
    
    Args:
        task_results_list: List of task result dictionaries.
        analysis_results: Dictionary with keys: mean_accuracy_diff, p_value, 
                          effect_size, ci_lower, ci_upper.
                          
    Returns:
        Complete summary dictionary ready for serialization.
    """
    summary = create_empty_summary()
    
    # Add task results
    for res in task_results_list:
        summary = add_task_result(
            summary,
            task_id=res.get("task_id", "unknown"),
            accuracy=res.get("accuracy", 0.0),
            condition=res.get("condition", "unknown")
        )
        
    # Update aggregates if available
    if all(k in analysis_results for k in ["mean_accuracy_diff", "p_value", "effect_size", "ci_lower", "ci_upper"]):
        summary = update_aggregate_stats(
            summary,
            mean_accuracy_diff=analysis_results["mean_accuracy_diff"],
            p_value=analysis_results["p_value"],
            effect_size=analysis_results["effect_size"],
            ci_lower=analysis_results["ci_lower"],
            ci_upper=analysis_results["ci_upper"]
        )
        
    return summary


def main():
    """
    CLI entry point for testing the module.
    Creates a sample summary file in data/.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate statistical summary YAML")
    parser.add_argument(
        "--output", 
        type=str, 
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output path (default: {DEFAULT_OUTPUT_PATH})"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Generate a demo summary with fake data"
    )
    
    args = parser.parse_args()
    
    if args.demo:
        logger.info("Generating demo statistical summary...")
        demo_data = {
            "task_results": [
                {"task_id": "T001", "accuracy": 0.85, "condition": "heterogeneous", "timestamp": "2024-01-01T00:00:00Z"},
                {"task_id": "T001", "accuracy": 0.82, "condition": "unified", "timestamp": "2024-01-01T00:01:00Z"},
                {"task_id": "T002", "accuracy": 0.91, "condition": "heterogeneous", "timestamp": "2024-01-01T00:02:00Z"},
                {"task_id": "T002", "accuracy": 0.88, "condition": "unified", "timestamp": "2024-01-01T00:03:00Z"}
            ],
            "aggregate_stats": {
                "mean_accuracy_diff": 0.025,
                "p_value": 0.032,
                "effect_size": 0.45,
                "ci_lower": 0.005,
                "ci_upper": 0.045
            }
        }
    else:
        logger.info("Creating empty statistical summary...")
        demo_data = create_empty_summary()
        
    output_path = save_statistical_summary(demo_data, args.output)
    logger.info(f"Done. File written to: {output_path}")


if __name__ == "__main__":
    main()
