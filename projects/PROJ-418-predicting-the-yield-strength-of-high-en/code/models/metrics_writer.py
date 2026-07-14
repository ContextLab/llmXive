import os
import json
import logging
from typing import Dict, Any, List, Optional

from utils.logging import get_logger

logger = get_logger(__name__)

def write_metrics_json(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Write evaluation metrics for all models (RF, GB, Linear) to a JSON file.

    Args:
        metrics: Dictionary containing metrics for each model.
                Expected structure:
                {
                    "Linear": {"R2": float, "MAE": float, "RMSE": float, "runtime": float},
                    "RandomForest": {"R2": float, "MAE": float, "RMSE": float, "runtime": float},
                    "GradientBoosting": {"R2": float, "MAE": float, "RMSE": float, "runtime": float}
                }
        output_path: Full path to the output JSON file (e.g., 'output/metrics.json')
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

    # Validate metrics structure
    required_models = ["Linear", "RandomForest", "GradientBoosting"]
    missing_models = [m for m in required_models if m not in metrics]
    if missing_models:
        logger.warning(f"Missing metrics for models: {missing_models}")

    # Ensure all metric keys exist for present models
    required_keys = ["R2", "MAE", "RMSE"]
    for model_name, model_metrics in metrics.items():
        for key in required_keys:
            if key not in model_metrics:
                logger.warning(f"Missing metric '{key}' for model '{model_name}'")
                model_metrics[key] = None

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Successfully wrote metrics to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write metrics to {output_path}: {e}")
        raise


def main() -> None:
    """
    Main entry point for the metrics writer.
    Expects metrics to be passed via command line arguments or loaded from a temporary
    state file if part of a larger pipeline. For standalone execution, this demonstrates
    the writer with placeholder structure (which should be replaced by actual T020 output).
    """
    # In a real pipeline, metrics would be passed from T020 or loaded from a shared state.
    # Here we define the expected interface for the writer.
    logger.info("Metrics writer module loaded. Use write_metrics_json() to save results.")


if __name__ == "__main__":
    main()
