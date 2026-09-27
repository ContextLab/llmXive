"""
Verification of Success Criterion SC-001: Lift over Majority Baseline.

This module implements the verification step to explicitly calculate and assert
the "[deferred] lift" condition (Accuracy > Majority Baseline + [deferred])
required by SC-001.

It consumes:
- data/results/majority_class_baseline_metrics.json (from T017b)
- data/results/model_metrics.json (from T019c, or generated on-the-fly if needed)

It produces:
- data/validation/success_criterion_check.json

The script fails loudly if the real data sources are missing or if the verification
cannot be performed.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_path_results, get_path_validation, get_path_processed_data
from logging_config import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Configuration for the deferred lift threshold.
# Since the specific value is "[deferred]", we define a placeholder constant
# that must be set via environment variable or config before running,
# or we use a strict default of 0.0 (meaning strictly greater than baseline).
# For this implementation, we assume a strict check: Accuracy > Baseline.
# If a specific lift is required later, it can be injected here.
DEFAULT_DEFERRED_LIFT_THRESHOLD = 0.0

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def calculate_lift(actual_metric: float, baseline_metric: float) -> float:
    """Calculate the lift as (Actual - Baseline)."""
    return actual_metric - baseline_metric

def verify_success_criterion(
    model_metrics_path: Path,
    majority_baseline_path: Path,
    output_path: Path,
    deferred_threshold: float = DEFAULT_DEFERRED_LIFT_THRESHOLD
) -> Dict[str, Any]:
    """
    Verify the SC-001 success criterion.

    Checks:
    1. Model Accuracy > Majority Baseline Accuracy + deferred_threshold

    Returns a dictionary with the verification result.
    """
    logger.info(f"Loading model metrics from: {model_metrics_path}")
    model_metrics = load_json_file(model_metrics_path)
    
    logger.info(f"Loading majority baseline metrics from: {majority_baseline_path}")
    baseline_metrics = load_json_file(majority_baseline_path)

    # Extract relevant metrics
    # We look for 'Accuracy' in the model metrics. 
    # The structure might vary slightly, so we check common keys.
    model_accuracy = None
    if 'Accuracy' in model_metrics:
        model_accuracy = model_metrics['Accuracy']
    elif 'accuracy' in model_metrics:
        model_accuracy = model_metrics['accuracy']
    
    if model_accuracy is None:
        # Check if it's nested under a specific model name if the file contains multiple
        for key, value in model_metrics.items():
            if isinstance(value, dict) and 'Accuracy' in value:
                model_accuracy = value['Accuracy']
                break
            if isinstance(value, dict) and 'accuracy' in value:
                model_accuracy = value['accuracy']
                break

    if model_accuracy is None:
        raise ValueError("Could not find 'Accuracy' in model metrics file.")

    baseline_accuracy = None
    if 'Accuracy' in baseline_metrics:
        baseline_accuracy = baseline_metrics['Accuracy']
    elif 'accuracy' in baseline_metrics:
        baseline_accuracy = baseline_metrics['accuracy']
    
    if baseline_accuracy is None:
        # Check for nested structure
        for key, value in baseline_metrics.items():
            if isinstance(value, dict) and 'Accuracy' in value:
                baseline_accuracy = value['Accuracy']
                break
            if isinstance(value, dict) and 'accuracy' in value:
                baseline_accuracy = value['accuracy']
                break

    if baseline_accuracy is None:
        raise ValueError("Could not find 'Accuracy' in majority baseline metrics file.")

    logger.info(f"Model Accuracy: {model_accuracy:.4f}")
    logger.info(f"Majority Baseline Accuracy: {baseline_accuracy:.4f}")
    logger.info(f"Deferred Lift Threshold: {deferred_threshold:.4f}")

    required_accuracy = baseline_accuracy + deferred_threshold
    lift = calculate_lift(model_accuracy, baseline_accuracy)
    passed = model_accuracy > required_accuracy

    result = {
        "success_criterion": "SC-001",
        "description": "Model Accuracy > Majority Baseline Accuracy + [deferred]",
        "model_accuracy": model_accuracy,
        "majority_baseline_accuracy": baseline_accuracy,
        "lift": lift,
        "required_threshold": required_accuracy,
        "deferred_threshold_used": deferred_threshold,
        "passed": passed,
        "timestamp": str(Path(__file__).resolve().parent.parent.parent / "logs" / "timestamp_placeholder") # Placeholder for actual timestamp logic if needed
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write result to file
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Verification result written to: {output_path}")
    logger.info(f"SC-001 Verification: {'PASSED' if passed else 'FAILED'}")

    return result

def main():
    """Main entry point for the verification script."""
    # Define paths relative to project root
    results_dir = get_path_results()
    validation_dir = get_path_validation()
    
    model_metrics_path = results_dir / "model_metrics.json"
    majority_baseline_path = results_dir / "majority_class_baseline_metrics.json"
    output_path = validation_dir / "success_criterion_check.json"

    # Get deferred threshold from environment if set, else use default
    deferred_threshold_str = os.environ.get("DEFERRED_LIFT_THRESHOLD")
    deferred_threshold = float(deferred_threshold_str) if deferred_threshold_str else DEFAULT_DEFERRED_LIFT_THRESHOLD

    try:
        result = verify_success_criterion(
            model_metrics_path,
            majority_baseline_path,
            output_path,
            deferred_threshold
        )
        
        if not result["passed"]:
            logger.warning("Success criterion SC-001 was NOT met.")
            # Do not exit with error code to allow the artifact to be generated, 
            # but log the failure clearly.
            # If the pipeline strictly requires failure, we could sys.exit(1) here.
        else:
            logger.info("Success criterion SC-001 was met.")
            
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid data in input files: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        raise

if __name__ == "__main__":
    main()
