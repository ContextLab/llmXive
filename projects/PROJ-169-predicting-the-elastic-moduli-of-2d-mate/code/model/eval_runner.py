import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

SURROGATE_DISCLAIMER = (
    "These results are ML interpolations of DFT data, not first-principles solutions."
)

# Success criteria threshold for inter-family generalization (MAPE %)
# This value is derived from the project's success criteria (SC-002)
GENERALIZATION_MAPE_THRESHOLD = 15.0

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(path: Path, data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved JSON to {path}")

def run_success_criteria_assertion(
    training_logs_path: Optional[Path] = None,
    generalization_metrics_path: Optional[Path] = None,
) -> None:
    """
    Validate success criteria against generalization metrics and log pass/fail status.
    
    This task (T019a) requires:
    1. Reading generalization metrics (specifically inter-family MAPE)
    2. Comparing against a threshold (15% MAPE)
    3. Logging the result to data/results/generalization_metrics.json
    4. NOT halting execution on failure (just log status)
    
    Also ensures the surrogate disclaimer is present in the output.
    """
    # Default paths if not provided
    if generalization_metrics_path is None:
        generalization_metrics_path = Path("data/results/generalization_metrics.json")

    # If the file doesn't exist yet, we can't validate
    if not generalization_metrics_path.exists():
        logger.warning(f"Generalization metrics file not found at {generalization_metrics_path}")
        # Create a failure report
        failure_report = {
            "status": "failed",
            "reason": "generalization_metrics_file_not_found",
            "message": f"File not found: {generalization_metrics_path}",
            "metadata": {
                "surrogate_disclaimer": SURROGATE_DISCLAIMER
            }
        }
        save_json_file(generalization_metrics_path, failure_report)
        logger.error("Generalization metrics file not found. Created failure report.")
        return

    try:
        data = load_json_file(generalization_metrics_path)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {generalization_metrics_path}: {e}")
        # Create a failure report
        failure_report = {
            "status": "failed",
            "reason": "invalid_json",
            "message": str(e),
            "metadata": {
                "surrogate_disclaimer": SURROGATE_DISCLAIMER
            }
        }
        save_json_file(generalization_metrics_path, failure_report)
        return

    # Extract metrics
    intra_mape = data.get("intra_family_mape")
    inter_mape = data.get("inter_family_mape")

    # Validate against threshold
    pass_status = False
    reason = "unknown"

    if inter_mape is None:
        reason = "inter_family_mape_missing"
        logger.warning("inter_family_mape not found in metrics")
    elif intra_mape is None:
        reason = "intra_family_mape_missing"
        logger.warning("intra_family_mape not found in metrics")
    elif inter_mape <= GENERALIZATION_MAPE_THRESHOLD:
        pass_status = True
        reason = "threshold_met"
        logger.info(f"Success criteria PASSED: Inter-family MAPE ({inter_mape:.2f}%) <= Threshold ({GENERALIZATION_MAPE_THRESHOLD}%)")
    else:
        reason = "threshold_exceeded"
        logger.warning(f"Success criteria FAILED: Inter-family MAPE ({inter_mape:.2f}%) > Threshold ({GENERALIZATION_MAPE_THRESHOLD}%)")

    # Update the data with validation results
    data["validation"] = {
        "status": "pass" if pass_status else "fail",
        "threshold_mape": GENERALIZATION_MAPE_THRESHOLD,
        "reason": reason,
        "intra_family_mape": intra_mape,
        "inter_family_mape": inter_mape
    }

    # Ensure metadata key exists
    if "metadata" not in data:
        data["metadata"] = {}
    data["metadata"]["surrogate_disclaimer"] = SURROGATE_DISCLAIMER

    # Save updated data
    save_json_file(generalization_metrics_path, data)
    logger.info(f"Validation results written to {generalization_metrics_path}")

def main():
    """Entry point for validating success criteria and logging results."""
    parser = argparse.ArgumentParser(
        description="Validate success criteria against generalization metrics and log results."
    )
    parser.add_argument(
        "--generalization-metrics",
        type=Path,
        default=None,
        help="Path to generalization metrics JSON file (default: data/results/generalization_metrics.json)"
    )
    args = parser.parse_args()

    run_success_criteria_assertion(
        generalization_metrics_path=args.generalization_metrics,
    )

if __name__ == "__main__":
    main()
