"""
T029: Generate model_report.json with metrics, hyperparameters, and statistical test results.

This script aggregates the outputs from the training and evaluation phases to produce
the final model report artifact as required by FR-007.

Expected Inputs:
  - data/artifacts/best_model_config.json (from code/models/train.py)
  - data/artifacts/evaluation_results.json (from code/models/evaluate.py)

Expected Output:
  - data/artifacts/model_report.json
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_paths, ensure_directories
from utils.logging_config import get_logger
from utils.provenance import record_artifact, compute_file_checksum

logger = get_logger(__name__)

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        logger.error(f"Required input file not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {file_path}: {e}")
        return None

def generate_model_report(
    train_results: Dict[str, Any],
    eval_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Combine training and evaluation results into the final model report structure.
    
    The report structure must contain:
    {
        "metrics": { "R2": float, "MAE": float, "RMSE": float },
        "hyperparameters": { ... },
        "statistical_test": { "method": str, "p_value": float, "confidence_interval": [float, float] }
    }
    """
    # Extract metrics from evaluation results
    # Assuming eval_results contains a 'metrics' key with R2, MAE, RMSE
    metrics = eval_results.get('metrics', {})
    
    # Extract hyperparameters from training results
    # Assuming train_results contains a 'best_params' or 'hyperparameters' key
    hyperparameters = train_results.get('best_params', train_results.get('hyperparameters', {}))
    
    # Extract statistical test results
    # Assuming eval_results contains a 'statistical_test' key
    stat_test = eval_results.get('statistical_test', {})
    
    report = {
        "metrics": {
            "R2": metrics.get("R2", 0.0),
            "MAE": metrics.get("MAE", 0.0),
            "RMSE": metrics.get("RMSE", 0.0)
        },
        "hyperparameters": hyperparameters,
        "statistical_test": {
            "method": stat_test.get("method", "unknown"),
            "p_value": stat_test.get("p_value", 0.0),
            "confidence_interval": stat_test.get("confidence_interval", [0.0, 0.0])
        }
    }
    
    return report

def main():
    """
    Main entry point for generating the model report.
    
    1. Loads training results (best model config/hyperparameters).
    2. Loads evaluation results (metrics, statistical tests).
    3. Merges them into the required JSON structure.
    4. Saves to data/artifacts/model_report.json.
    5. Records provenance for the new artifact.
    """
    paths = get_paths()
    ensure_directories()
    
    # Define input paths based on the pipeline flow
    # T026/T025 should have written the best model config here
    train_output_path = paths["data"] / "artifacts" / "best_model_config.json"
    
    # T027/T028 should have written the evaluation results here
    eval_output_path = paths["data"] / "artifacts" / "evaluation_results.json"
    
    # Define output path
    output_path = paths["data"] / "artifacts" / "model_report.json"
    
    logger.info(f"Loading training results from: {train_output_path}")
    train_data = load_json_file(train_output_path)
    
    logger.info(f"Loading evaluation results from: {eval_output_path}")
    eval_data = load_json_file(eval_output_path)
    
    if train_data is None or eval_data is None:
        logger.error("Failed to load required input files. Cannot generate report.")
        sys.exit(1)
    
    logger.info("Generating model report...")
    report = generate_model_report(train_data, eval_data)
    
    # Write the report to disk
    try:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Model report successfully written to: {output_path}")
    except IOError as e:
        logger.error(f"Failed to write model report: {e}")
        sys.exit(1)
    
    # Record provenance
    checksum = compute_file_checksum(output_path)
    record_artifact(
        artifact_path=str(output_path.relative_to(project_root)),
        checksum=checksum,
        task_id="T029",
        description="Model performance report with metrics, hyperparameters, and statistical tests"
    )
    
    logger.info("Task T029 completed successfully.")

if __name__ == "__main__":
    main()