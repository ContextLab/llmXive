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
    Add explicit "Surrogate Model" disclaimer to training logs and generalization metrics.
    
    This satisfies T022a by ensuring the metadata key exists in both output files.
    """
    # Default paths if not provided
    if training_logs_path is None:
        training_logs_path = Path("data/results/training_logs.json")
    if generalization_metrics_path is None:
        generalization_metrics_path = Path("data/results/generalization_metrics.json")

    # Process training logs
    if training_logs_path.exists():
        try:
            data = load_json_file(training_logs_path)
            # Ensure metadata key exists
            if "metadata" not in data:
                data["metadata"] = {}
            data["metadata"]["surrogate_disclaimer"] = SURROGATE_DISCLAIMER
            save_json_file(training_logs_path, data)
            logger.info(f"Updated surrogate disclaimer in {training_logs_path}")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON in {training_logs_path}")
            raise
    else:
        logger.warning(f"Training logs file not found at {training_logs_path}")

    # Process generalization metrics
    if generalization_metrics_path.exists():
        try:
            data = load_json_file(generalization_metrics_path)
            # Ensure metadata key exists
            if "metadata" not in data:
                data["metadata"] = {}
            data["metadata"]["surrogate_disclaimer"] = SURROGATE_DISCLAIMER
            save_json_file(generalization_metrics_path, data)
            logger.info(f"Updated surrogate disclaimer in {generalization_metrics_path}")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON in {generalization_metrics_path}")
            raise
    else:
        logger.warning(f"Generalization metrics file not found at {generalization_metrics_path}")

def main():
    """Entry point for adding surrogate model disclaimers to result files."""
    parser = argparse.ArgumentParser(
        description="Add surrogate model disclaimer to training logs and generalization metrics."
    )
    parser.add_argument(
        "--training-logs",
        type=Path,
        default=None,
        help="Path to training logs JSON file (default: data/results/training_logs.json)"
    )
    parser.add_argument(
        "--generalization-metrics",
        type=Path,
        default=None,
        help="Path to generalization metrics JSON file (default: data/results/generalization_metrics.json)"
    )
    args = parser.parse_args()

    run_success_criteria_assertion(
        training_logs_path=args.training_logs,
        generalization_metrics_path=args.generalization_metrics,
    )

if __name__ == "__main__":
    main()
