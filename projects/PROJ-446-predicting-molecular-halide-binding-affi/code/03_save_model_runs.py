"""
T022: Save model run artifacts to data/processed/model_runs.json.

This script aggregates metrics and feature importances from the trained
Random Forest and Gradient Boosting models (T019b, T020b) and saves them
to a single JSON artifact.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Import from local utils
from utils.logger import get_logger
from utils.config import get_data_path

logger = get_logger(__name__)

def load_model_metrics(model_type: str) -> Dict[str, Any]:
    """
    Load metrics and feature importances for a specific model type.
    
    Args:
        model_type: Either 'random_forest' or 'gradient_boosting'
        
    Returns:
        Dictionary containing folds, metrics, and feature_importances
    """
    metrics_path = get_data_path() / "processed" / "metrics" / f"{model_type}_metrics.json"
    
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
        
    with open(metrics_path, 'r') as f:
        return json.load(f)

def save_model_runs_artifact(
    random_forest_metrics: Dict[str, Any],
    gradient_boosting_metrics: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Aggregate model run artifacts into a single JSON file.
    
    Args:
        random_forest_metrics: Metrics from T019b
        gradient_boosting_metrics: Metrics from T020b
        output_path: Path to write the final model_runs.json
    """
    model_runs = {
        "model_type": "ensemble_comparison",
        "timestamp": "T022_execution",
        "models": {
            "random_forest": {
                "folds": random_forest_metrics.get("folds", []),
                "metrics": random_forest_metrics.get("metrics", {}),
                "feature_importances": random_forest_metrics.get("feature_importances", {})
            },
            "gradient_boosting": {
                "folds": gradient_boosting_metrics.get("folds", []),
                "metrics": gradient_boosting_metrics.get("metrics", {}),
                "feature_importances": gradient_boosting_metrics.get("feature_importances", {})
            }
        },
        "summary": {
            "random_forest_avg_r2": random_forest_metrics.get("metrics", {}).get("mean_r2", None),
            "random_forest_avg_rmse": random_forest_metrics.get("metrics", {}).get("mean_rmse", None),
            "gradient_boosting_avg_r2": gradient_boosting_metrics.get("metrics", {}).get("mean_r2", None),
            "gradient_boosting_avg_rmse": gradient_boosting_metrics.get("metrics", {}).get("mean_rmse", None)
        }
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(model_runs, f, indent=2)
        
    logger.info(f"Model runs artifact saved to {output_path}")

def main() -> int:
    """
    Main entry point for T022.
    
    Returns:
        0 on success, 1 on failure
    """
    try:
        data_path = get_data_path()
        output_path = data_path / "processed" / "model_runs.json"
        
        logger.info("Loading Random Forest metrics...")
        rf_metrics = load_model_metrics("random_forest")
        
        logger.info("Loading Gradient Boosting metrics...")
        gb_metrics = load_model_metrics("gradient_boosting")
        
        logger.info("Aggregating model run artifacts...")
        save_model_runs_artifact(rf_metrics, gb_metrics, output_path)
        
        logger.info("T022 completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required metrics file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T022 execution: {e}")
        raise

if __name__ == "__main__":
    exit(main())
