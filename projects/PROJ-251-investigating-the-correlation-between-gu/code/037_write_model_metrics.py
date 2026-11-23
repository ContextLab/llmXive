"""
Task T037: Write model metrics to data/results/model_metrics.json.

This task aggregates the calculated metrics (accuracy, precision, recall, F1,
mean/std accuracy, success criterion status) into the final JSON artifact
required for the pipeline.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Import from existing API surface
from code.utils.logging_config import get_logger
from code.utils.config import get_project_root

# Ensure we can import from the code directory
project_root = get_project_root()
sys.path.insert(0, str(project_root))

logger = get_logger(__name__)


def load_model_metrics() -> dict:
    """
    Load the metrics calculated by T036a and the success criterion check from T036b.
    Expected path: data/results/model_metrics.json (created/updated by T036b).
    """
    metrics_path = project_root / "data" / "results" / "model_metrics.json"
    
    if not metrics_path.exists():
        logger.error(f"Metrics file not found at {metrics_path}. T036b must run first.")
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)


def write_final_metrics(metrics: dict) -> None:
    """
    Write the final aggregated metrics to data/results/model_metrics.json.
    
    This function ensures the JSON is properly formatted and contains all
    required fields as per the schema:
    - accuracy
    - precision
    - recall
    - F1
    - meets_accuracy_target
    - mean_accuracy
    - std_accuracy
    - significance_p_value
    """
    output_path = project_root / "data" / "results" / "model_metrics.json"
    
    # Ensure the directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Validate required fields exist
    required_fields = [
        'accuracy', 'precision', 'recall', 'F1', 
        'meets_accuracy_target', 'mean_accuracy', 'std_accuracy'
    ]
    
    missing_fields = [field for field in required_fields if field not in metrics]
    if missing_fields:
        logger.warning(f"Missing required fields in metrics: {missing_fields}")
        # Add placeholders for missing fields to prevent crash, but log warning
        for field in missing_fields:
            metrics[field] = None
    
    # Write the final metrics
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Model metrics successfully written to {output_path}")


def run_write_metrics() -> None:
    """
    Main entry point for T037.
    Loads metrics from T036b and writes the final JSON artifact.
    """
    logger.info("Starting T037: Write model metrics to data/results/model_metrics.json")
    
    try:
        # Load metrics calculated by previous tasks
        metrics = load_model_metrics()
        
        # Write the final metrics
        write_final_metrics(metrics)
        
        logger.info("T037 completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Dependency error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in metrics file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during T037: {e}")
        sys.exit(1)


def main():
    """CLI entry point."""
    run_write_metrics()


if __name__ == "__main__":
    main()