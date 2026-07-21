"""
Evaluation Runner for Success Criteria Validation (Task T019a).

This script validates the success criteria for the surrogate model by calculating
the Mean Absolute Percentage Error (MAPE) against held-out families and logging
the result against the defined threshold.

It consumes:
- predictions.json (from T018b)
- split_indices.json (from T017/T013f)

It produces:
- data/results/success_criteria_validation.json
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logger import get_logger, log_operation

# Constants
MAPE_THRESHOLD = 0.15  # 15% MAPE threshold for success criteria
REQUIRED_KEYS = ["youngs_modulus", "shear_modulus", "poisson_ratio"]
PREDICTIONS_FILE = PROJECT_ROOT / "data" / "processed" / "predictions.json"
SPLIT_INDICES_FILE = PROJECT_ROOT / "data" / "processed" / "split_indices.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "results" / "success_criteria_validation.json"

# Initialize logger
logger = get_logger("eval_runner")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(path: Path, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved results to {path}")


def calculate_mape(y_true: List[float], y_pred: List[float], epsilon: float = 1e-8) -> float:
    """
    Calculate Mean Absolute Percentage Error.

    Args:
        y_true: List of true values.
        y_pred: List of predicted values.
        epsilon: Small value to avoid division by zero.

    Returns:
        MAPE as a float (0.0 to 1.0+).
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")

    if len(y_true) == 0:
        return 0.0

    errors = []
    for t, p in zip(y_true, y_pred):
        if abs(t) < epsilon:
            # Skip near-zero values to avoid infinite percentage errors
            continue
        errors.append(abs(t - p) / abs(t))

    if not errors:
        return float('nan')

    return sum(errors) / len(errors)


def run_success_criteria_assertion(
    predictions: Dict[str, Any],
    test_indices: List[int],
    mape_threshold: float = MAPE_THRESHOLD
) -> Dict[str, Any]:
    """
    Validate success criteria by calculating MAPE on test set.

    Args:
        predictions: Dictionary containing predictions and ground truth.
        test_indices: List of indices belonging to the test set.
        mape_threshold: Maximum allowed MAPE for success.

    Returns:
        Dictionary containing validation results.
    """
    logger.info(f"Running success criteria assertion with threshold: {mape_threshold}")

    # Filter predictions to test set only
    test_predictions = []
    test_ground_truth = {key: [] for key in REQUIRED_KEYS}
    test_pred_values = {key: [] for key in REQUIRED_KEYS}

    # Assuming predictions structure: {"data": [{"index": int, "targets": {...}, "predictions": {...}}, ...]}
    # Adjust based on actual structure of predictions.json from T018b
    data_list = predictions.get("data", predictions if isinstance(predictions, list) else [])

    for item in data_list:
        idx = item.get("index")
        if idx is None:
            # Try to infer index if not present, or skip
            continue

        if idx in test_indices:
            targets = item.get("targets", {})
            preds = item.get("predictions", {})

            for key in REQUIRED_KEYS:
                if key in targets and key in preds:
                    test_ground_truth[key].append(targets[key])
                    test_pred_values[key].append(preds[key])

    # Calculate MAPE for each modulus
    results = {
        "mape_threshold": mape_threshold,
        "test_sample_size": len(test_indices),
        "metrics": {},
        "passed": True,
        "disclaimer": "These results are derived from a machine learning surrogate model interpolating pre-computed DFT data. They do not represent first-principles calculations or solutions to the Schrödinger equation."
    }

    overall_mapes = []

    for key in REQUIRED_KEYS:
        y_true = test_ground_truth[key]
        y_pred = test_pred_values[key]

        if len(y_true) == 0:
            results["metrics"][key] = {
                "mape": None,
                "sample_size": 0,
                "status": "SKIPPED (No data)"
            }
            continue

        mape = calculate_mape(y_true, y_pred)
        results["metrics"][key] = {
            "mape": mape,
            "sample_size": len(y_true),
            "status": "PASS" if mape <= mape_threshold else "FAIL"
        }
        overall_mapes.append(mape)

    # Determine overall pass/fail
    # If any metric has a valid MAPE > threshold, fail
    valid_mapes = [m for m in overall_mapes if not (m is None or (isinstance(m, float) and (m != m)))] # Check for NaN
    if valid_mapes:
        max_mape = max(valid_mapes)
        results["overall_mape"] = max_mape
        results["passed"] = max_mape <= mape_threshold
        results["status"] = "SUCCESS" if results["passed"] else "FAILURE"
    else:
        results["overall_mape"] = None
        results["passed"] = False
        results["status"] = "INCONCLUSIVE (No valid metrics)"

    return results


def main() -> int:
    """Main entry point for the evaluation runner."""
    parser = argparse.ArgumentParser(description="Evaluate model success criteria")
    parser.add_argument(
        "--predictions",
        type=str,
        default=str(PREDICTIONS_FILE),
        help="Path to predictions.json"
    )
    parser.add_argument(
        "--split",
        type=str,
        default=str(SPLIT_INDICES_FILE),
        help="Path to split_indices.json"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_FILE),
        help="Path to output validation JSON"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=MAPE_THRESHOLD,
        help="MAPE threshold for success criteria"
    )

    args = parser.parse_args()

    try:
        # Load inputs
        logger.info(f"Loading predictions from {args.predictions}")
        predictions = load_json_file(Path(args.predictions))

        logger.info(f"Loading split indices from {args.split}")
        split_data = load_json_file(Path(args.split))
        # Handle potential structure variations
        test_indices = split_data.get("test_indices", split_data.get("test", []))
        if not isinstance(test_indices, list):
            raise ValueError("test_indices must be a list in split_indices.json")

        # Run validation
        validation_result = run_success_criteria_assertion(
            predictions,
            test_indices,
            args.threshold
        )

        # Save results
        save_json_file(Path(args.output), validation_result)

        # Log summary
        status = validation_result["status"]
        passed = validation_result["passed"]
        overall_mape = validation_result.get("overall_mape")

        if overall_mape is not None:
            logger.info(f"Overall MAPE: {overall_mape:.4f} (Threshold: {args.threshold})")
        else:
            logger.warning("Could not calculate overall MAPE.")

        logger.info(f"Validation Status: {status}")

        if not passed:
            logger.warning("Success criteria NOT met. Model performance is below threshold.")
            return 1
        else:
            logger.info("Success criteria MET.")
            return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during evaluation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())