"""
Task T055b: Compute RMSE/MAE for binary validation.

Loads the binary validation results from T095c-Exec (data/processed/sc003_binary_validation.json),
calculates overall RMSE and MAE across all systems that have valid data,
and writes the summary to data/processed/sc003_binary_metrics.json.
"""
import json
import logging
import math
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from code.config import PROCESSED_PATH, get_logger

logger = get_logger(__name__)

INPUT_PATH = PROCESSED_PATH / "sc003_binary_validation.json"
OUTPUT_PATH = PROCESSED_PATH / "sc003_binary_metrics.json"


def load_validation_results() -> List[Dict[str, Any]]:
    """Load binary validation results from JSON file."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Ensure T095c-Exec has been run successfully."
        )

    with open(INPUT_PATH, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(
            f"Expected a list of validation results in {INPUT_PATH}, got {type(data)}"
        )

    return data


def calculate_rmse(predictions: List[float], targets: List[float]) -> float:
    """Calculate Root Mean Squared Error."""
    if len(predictions) != len(targets) or len(predictions) == 0:
        return float('nan')

    squared_errors = [(p - t) ** 2 for p, t in zip(predictions, targets)]
    mse = sum(squared_errors) / len(squared_errors)
    return math.sqrt(mse)


def calculate_mae(predictions: List[float], targets: List[float]) -> float:
    """Calculate Mean Absolute Error."""
    if len(predictions) != len(targets) or len(predictions) == 0:
        return float('nan')

    absolute_errors = [abs(p - t) for p, t in zip(predictions, targets)]
    return sum(absolute_errors) / len(absolute_errors)


def compute_overall_metrics(validation_results: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    """
    Compute overall RMSE and MAE across all binary systems with data.

    Filters out entries where rmse or mae is null (no_data cases).
    """
    all_predictions = []
    all_targets = []

    for entry in validation_results:
        system = entry.get("system", "unknown")
        status = entry.get("status", "unknown")

        if status == "no_data" or entry.get("rmse") is None:
            logger.debug(f"Skipping system {system}: no data available")
            continue

        # Extract predictions and targets if available
        # The validation results may contain detailed arrays or just summary metrics
        # If detailed arrays are present, use them; otherwise, we compute from individual points
        # For this implementation, we assume the validation results contain 'predictions' and 'targets' lists
        predictions = entry.get("predictions")
        targets = entry.get("targets")

        if predictions is not None and targets is not None:
            all_predictions.extend(predictions)
            all_targets.extend(targets)
        else:
            # Fallback: if individual points are not stored, we cannot compute overall metrics
            # In this case, we would need to aggregate the per-system RMSE/MAE values
            # which is not mathematically equivalent to overall RMSE/MAE.
            # For now, we log a warning and skip this entry for overall calculation.
            logger.warning(
                f"System {system} has summary metrics but no prediction/target arrays. "
                "Cannot contribute to overall RMSE/MAE calculation."
            )

    if len(all_predictions) == 0:
        logger.warning("No valid prediction/target pairs found for overall metric calculation.")
        return {
            "overall_rmse": None,
            "overall_mae": None,
            "n_systems_included": 0,
            "n_points": 0,
            "note": "No data available for overall metric calculation"
        }

    overall_rmse = calculate_rmse(all_predictions, all_targets)
    overall_mae = calculate_mae(all_predictions, all_targets)

    return {
        "overall_rmse": overall_rmse,
        "overall_mae": overall_mae,
        "n_systems_included": len(validation_results),
        "n_points": len(all_predictions)
    }


def save_metrics(metrics: Dict[str, Any]) -> None:
    """Save computed metrics to JSON file."""
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {OUTPUT_PATH}")


def main():
    """Main entry point for T055b."""
    logger.info("Starting T055b: Compute RMSE/MAE for binary validation")

    try:
        validation_results = load_validation_results()
        logger.info(f"Loaded {len(validation_results)} validation results")

        metrics = compute_overall_metrics(validation_results)

        if metrics["overall_rmse"] is not None:
            logger.info(f"Overall RMSE: {metrics['overall_rmse']:.6f}")
            logger.info(f"Overall MAE: {metrics['overall_mae']:.6f}")
        else:
            logger.warning("Could not compute overall metrics (no valid data)")

        save_metrics(metrics)
        logger.info("T055b completed successfully")

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during metric calculation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()