"""
T034: Save PredictiveModelArtifact with metrics, hyperparameters, and comparison results.

This script aggregates the results from the XGBoost model training (T031/T032)
and the model comparison analysis (T033) into a single, versioned artifact.

Inputs:
    - artifacts/xgboost_metrics.json (from T032)
    - artifacts/model_comparison.json (from T033)
    - artifacts/xgboost_model.pkl (from T031, for hyperparameter extraction if needed)

Output:
    - artifacts/predictive_model_artifact.json
"""
import os
import sys
import logging
import json
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_training_results():
    """
    Loads the XGBoost metrics and model parameters.
    Returns a dictionary containing metrics and hyperparameters.
    """
    metrics_path = Path("artifacts/xgboost_metrics.json")
    model_path = Path("artifacts/xgboost_model.pkl")

    if not metrics_path.exists():
        raise FileNotFoundError(f"Required input file missing: {metrics_path}")

    logger.info(f"Loading training metrics from {metrics_path}")
    with open(metrics_path, 'r') as f:
        metrics_data = json.load(f)

    # Attempt to load hyperparameters if stored in the metrics file
    # If not, we assume they are embedded or we load from a separate config if it existed.
    # Based on T032 spec, metrics usually include R2, MAE, RMSE and best_params.
    result = {
        "metrics": metrics_data.get("metrics", {}),
        "hyperparameters": metrics_data.get("best_params", metrics_data.get("hyperparameters", {})),
        "training_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Verify essential metrics exist
    required_metrics = ['r2', 'mae', 'rmse']
    for m in required_metrics:
        if m not in result["metrics"]:
            logger.warning(f"Metric '{m}' not found in {metrics_path}. It will be recorded as null.")

    return result

def save_predictive_artifact(training_data, comparison_path):
    """
    Combines training data and comparison results into the final artifact.
    """
    comparison_file = Path(comparison_path)
    if not comparison_file.exists():
        logger.warning(f"Comparison file not found at {comparison_file}. "
                       "The 'comparison_results' section will be empty.")
        comparison_results = {}
    else:
        logger.info(f"Loading comparison results from {comparison_file}")
        with open(comparison_file, 'r') as f:
            comparison_results = json.load(f)

    artifact = {
        "artifact_type": "PredictiveModelArtifact",
        "version": "1.0.0",
        "description": "Aggregated XGBoost predictive model results and LME comparison.",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_info": {
            "type": "XGBoostRegressor",
            "hyperparameters": training_data["hyperparameters"],
            "metrics": training_data["metrics"]
        },
        "comparison_results": comparison_results,
        "source_files": [
            "artifacts/xgboost_metrics.json",
            "artifacts/model_comparison.json"
        ]
    }

    output_path = Path("artifacts/predictive_model_artifact.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving predictive model artifact to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(artifact, f, indent=2)

    return output_path

def main():
    """
    Main entry point for T034.
    """
    logger.info("Starting T034: Save PredictiveModelArtifact")

    try:
        # Step 1: Load training results
        training_data = load_training_results()

        # Step 2: Load comparison results
        comparison_path = "artifacts/model_comparison.json"

        # Step 3: Save the combined artifact
        output_path = save_predictive_artifact(training_data, comparison_path)

        logger.info(f"T034 completed successfully. Artifact saved to: {output_path}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON input: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T034 execution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())