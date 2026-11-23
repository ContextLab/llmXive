import os
import json
import logging
from typing import Dict, Any, List, Optional

from utils.logging import get_logger

logger = get_logger(__name__)


def write_metrics_json(
    metrics: Dict[str, Dict[str, float]],
    output_path: str = "output/metrics.json",
    overwrite: bool = True,
) -> None:
    """
    Write model evaluation metrics to a JSON file.

    Args:
        metrics: Dictionary mapping model names to their metric dictionaries.
                 Expected structure:
                 {
                     "LinearRegression": {"r2": ..., "mae": ..., "rmse": ...},
                     "RandomForest": {"r2": ..., "mae": ..., "rmse": ...},
                     "GradientBoosting": {"r2": ..., "mae": ..., "rmse": ...}
                 }
        output_path: Path to the output JSON file.
        overwrite: If True, overwrite existing file. If False, append to existing JSON
                   (creating list of runs if file exists). Default is True.

    Raises:
        FileNotFoundError: If output directory does not exist.
        json.JSONDecodeError: If existing file is not valid JSON and overwrite=False.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

    # Load existing metrics if file exists and not overwriting
    existing_data = []
    if os.path.exists(output_path) and not overwrite:
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    existing_data = []
                else:
                    existing_data = json.loads(content)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Existing file {output_path} is not valid JSON. "
                f"Set overwrite=True or fix the file.",
                e.doc,
                e.pos,
            )

    # Prepare the new run data
    run_data = {
        "models": metrics,
    }

    # Combine with existing data if not overwriting
    if not overwrite and existing_data:
        existing_data.append(run_data)
        final_data = existing_data
    else:
        final_data = run_data

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2)

    logger.info(f"Wrote metrics for {len(metrics)} models to {output_path}")


def main() -> None:
    """
    Main entry point for metrics writer script.
    Demonstrates usage by writing sample metrics (to be replaced by actual training output).
    """
    # Example usage - in real pipeline, metrics come from evaluate_model results
    sample_metrics = {
        "LinearRegression": {
            "r2": 0.45,
            "mae": 120.5,
            "rmse": 150.2,
        },
        "RandomForest": {
            "r2": 0.78,
            "mae": 85.3,
            "rmse": 110.1,
        },
        "GradientBoosting": {
            "r2": 0.82,
            "mae": 78.9,
            "rmse": 105.4,
        },
    }

    output_path = "output/metrics.json"
    write_metrics_json(sample_metrics, output_path)

    logger.info("Metrics writer completed successfully.")


if __name__ == "__main__":
    main()