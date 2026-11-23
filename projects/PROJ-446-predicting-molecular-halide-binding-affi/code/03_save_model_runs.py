import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from utils.logger import get_logger
from utils.config import get_path

logger = get_logger(__name__)

def load_model_metrics(model_type: str) -> Dict[str, Any]:
    """
    Load metrics for a specific model type from the metrics directory.
    
    Args:
        model_type: Either 'random_forest' or 'gradient_boosting'
        
    Returns:
        Dictionary containing model metrics
        
    Raises:
        FileNotFoundError: If metrics file does not exist
        json.JSONDecodeError: If metrics file is invalid JSON
    """
    metrics_path = get_path(f"data/processed/metrics/{model_type}_metrics.json")
    logger.info(f"Loading metrics from {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
        
    return metrics

def save_model_runs_artifact() -> None:
    """
    Aggregate model run artifacts from Random Forest and Gradient Boosting
    into a single model_runs.json file.
    
    This includes:
    - model_type
    - folds (number of cross-validation folds)
    - metrics (R², RMSE per fold and mean)
    - feature importances (if available)
    
    Output: data/processed/model_runs.json
    """
    output_path = get_path("data/processed/model_runs.json")
    runs = []
    
    # Load Random Forest artifacts
    try:
        rf_metrics = load_model_metrics("random_forest")
        rf_run = {
            "model_type": "RandomForest",
            "folds": rf_metrics.get("folds", 5),
            "metrics": rf_metrics.get("metrics", {}),
            "feature_importances": rf_metrics.get("feature_importances", {})
        }
        runs.append(rf_run)
        logger.info("Successfully loaded Random Forest metrics")
    except FileNotFoundError:
        logger.warning("Random Forest metrics file not found. Skipping RF in model_runs.")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in Random Forest metrics: {e}")
    
    # Load Gradient Boosting artifacts
    try:
        gb_metrics = load_model_metrics("gradient_boosting")
        gb_run = {
            "model_type": "GradientBoosting",
            "folds": gb_metrics.get("folds", 5),
            "metrics": gb_metrics.get("metrics", {}),
            "feature_importances": gb_metrics.get("feature_importances", {})
        }
        runs.append(gb_run)
        logger.info("Successfully loaded Gradient Boosting metrics")
    except FileNotFoundError:
        logger.warning("Gradient Boosting metrics file not found. Skipping GB in model_runs.")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in Gradient Boosting metrics: {e}")
    
    # Write combined artifact
    if not runs:
        logger.warning("No model runs were successfully loaded. Creating empty artifact.")
    
    with open(output_path, 'w') as f:
        json.dump({"model_runs": runs}, f, indent=2)
        
    logger.info(f"Saved model runs artifact to {output_path}")

def main() -> None:
    """Entry point for saving model run artifacts."""
    logger.info("Starting model runs artifact aggregation...")
    save_model_runs_artifact()
    logger.info("Model runs artifact aggregation complete.")

if __name__ == "__main__":
    main()
