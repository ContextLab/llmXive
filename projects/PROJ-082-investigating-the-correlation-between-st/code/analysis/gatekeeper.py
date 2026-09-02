"""
Gatekeeper module for the meta-analysis pipeline.

Determines whether the dataset is sufficient for quantitative analysis
or if a narrative synthesis is required based on study counts.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Import utilities from existing API surface
from utils.config import get_project_root

logger = logging.getLogger(__name__)


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """
    Load a JSON file and return its contents as a dictionary.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Dictionary containing the JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(file_path: Path, data: Dict[str, Any]) -> None:
    """
    Save a dictionary to a JSON file.

    Args:
        file_path: Path to the output JSON file.
        data: Dictionary to save.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def load_study_count(input_path: Path) -> int:
    """
    Load the study count from study_count.json.

    Args:
        input_path: Path to study_count.json.

    Returns:
        The study count (N). Returns 0 if file is missing or invalid.
    """
    try:
        data = load_json_file(input_path)
        return int(data.get('N', 0))
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Could not load study count from {input_path}: {e}")
        return 0


def load_valid_pair_count(input_path: Path) -> int:
    """
    Load the valid pair count from valid_pair_count.json.

    Args:
        input_path: Path to valid_pair_count.json.

    Returns:
        The valid pair count (N_valid). Returns 0 if file is missing or invalid.
    """
    try:
        data = load_json_file(input_path)
        return int(data.get('N_valid', 0))
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Could not load valid pair count from {input_path}: {e}")
        return 0


def run_gatekeeper(study_count_path: Path, valid_pair_count_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Evaluate study counts and determine if quantitative analysis is feasible.

    Args:
        study_count_path: Path to study_count.json.
        valid_pair_count_path: Path to valid_pair_count.json.
        output_path: Path to write gate_result.json.

    Returns:
        Dictionary containing the gate result.
    """
    n = load_study_count(study_count_path)
    n_valid = load_valid_pair_count(valid_pair_count_path)

    logger.info(f"Gatekeeper check: N={n}, N_valid={n_valid}")

    # Threshold for quantitative analysis
    THRESHOLD = 10

    if n < THRESHOLD or n_valid < THRESHOLD:
        result = {
            "status": "narrative_required",
            "reason": "Insufficient valid studies",
            "details": {
                "N": n,
                "N_valid": n_valid,
                "threshold": THRESHOLD
            }
        }
        logger.info(f"Gatekeeper result: {result['status']} - {result['reason']}")
    else:
        result = {
            "status": "quantitative_ok",
            "details": {
                "N": n,
                "N_valid": n_valid,
                "threshold": THRESHOLD
            }
        }
        logger.info(f"Gatekeeper result: {result['status']}")

    # Ensure output directory exists and save result
    save_json_file(output_path, result)
    logger.info(f"Gate result written to {output_path}")

    return result


def main():
    """Main entry point for the gatekeeper script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    project_root = get_project_root()

    # Define paths relative to project root
    study_count_path = project_root / 'data' / 'processed' / 'study_count.json'
    valid_pair_count_path = project_root / 'data' / 'processed' / 'valid_pair_count.json'
    output_path = project_root / 'data' / 'derived' / 'gate_result.json'

    try:
        result = run_gatekeeper(study_count_path, valid_pair_count_path, output_path)
        logger.info("Gatekeeper completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Gatekeeper failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())