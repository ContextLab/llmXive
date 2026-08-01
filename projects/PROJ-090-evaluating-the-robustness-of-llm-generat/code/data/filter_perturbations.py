"""
Filter perturbation candidates based on semantic similarity scores.

This module implements the filtering logic for User Story 1 (T018).
It reads the validated candidates from T016, retains only those with
raw_score > 0.95 (FR-003), and writes the primary dataset.

If the yield is insufficient (zero candidates), it logs a critical error
to data/logs/halt_report.json with reason "ZERO_YIELD" and exits with code 1.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_directories, get_config_dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
THRESHOLD = 0.95  # FR-003: Semantic similarity threshold
INPUT_PATH = Path("data/processed/perturbation_candidates_validated.json")
OUTPUT_PATH = Path("data/processed/perturbation_candidates.json")
HALT_REPORT_PATH = Path("data/logs/halt_report.json")

def load_raw_candidates(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the validated candidates from the input JSON file.

    Args:
        input_path: Path to the validated candidates JSON file.

    Returns:
        List of candidate dictionaries.

    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    logger.info(f"Loading validated candidates from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a list of candidates in {input_path}, got {type(data)}")

    logger.info(f"Loaded {len(data)} candidates")
    return data

def filter_candidates(candidates: List[Dict[str, Any]], threshold: float = THRESHOLD) -> List[Dict[str, Any]]:
    """
    Filter candidates based on semantic similarity score.

    Retains all candidates with raw_score > threshold.

    Args:
        candidates: List of candidate dictionaries.
        threshold: Minimum semantic similarity score (default 0.95).

    Returns:
        List of filtered candidates.
    """
    logger.info(f"Filtering candidates with threshold > {threshold}")
    filtered = [
        c for c in candidates
        if c.get('raw_score', 0.0) > threshold
    ]
    logger.info(f"Filtered from {len(candidates)} to {len(filtered)} candidates")
    return filtered

def save_filtered_results(candidates: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the filtered candidates to the output JSON file.

    Args:
        candidates: List of filtered candidate dictionaries.
        output_path: Path to the output JSON file.
    """
    logger.info(f"Saving {len(candidates)} filtered candidates to {output_path}")
    ensure_directories([output_path])
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)
    logger.info("Successfully saved filtered candidates")

def save_halt_report(reason: str, output_path: Path) -> None:
    """
    Save a halt report indicating a critical failure.

    Args:
        reason: The reason for the halt (e.g., "ZERO_YIELD").
        output_path: Path to the halt report JSON file.
    """
    logger.critical(f"Halt condition triggered: {reason}")
    ensure_directories([output_path])
    report = {
        "reason": reason,
        "timestamp": str(Path(output_path).stat().st_mtime),
        "details": "No candidates met the semantic similarity threshold."
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Halt report saved to {output_path}")

def main() -> int:
    """
    Main entry point for the filtering pipeline.

    Returns:
        0 on success, 1 on failure (halt condition).
    """
    try:
        # Ensure directories exist
        ensure_directories([OUTPUT_PATH, HALT_REPORT_PATH])

        # Load validated candidates
        if not INPUT_PATH.exists():
            logger.error(f"Input file not found: {INPUT_PATH}")
            # If input doesn't exist, we can't filter, so treat as zero yield
            save_halt_report("INPUT_NOT_FOUND", HALT_REPORT_PATH)
            return 1

        candidates = load_raw_candidates(INPUT_PATH)

        if len(candidates) == 0:
            logger.warning("No candidates found in input file.")
            save_halt_report("ZERO_YIELD", HALT_REPORT_PATH)
            return 1

        # Filter candidates
        filtered = filter_candidates(candidates, THRESHOLD)

        if len(filtered) == 0:
            logger.critical("Zero candidates retained after filtering. Halt condition triggered.")
            save_halt_report("ZERO_YIELD", HALT_REPORT_PATH)
            return 1

        # Save filtered results
        save_filtered_results(filtered, OUTPUT_PATH)

        logger.info(f"Filtering complete. {len(filtered)} candidates retained.")
        return 0

    except Exception as e:
        logger.exception(f"Unexpected error during filtering: {e}")
        # On unexpected error, also trigger halt
        save_halt_report(f"UNEXPECTED_ERROR: {str(e)}", HALT_REPORT_PATH)
        return 1

if __name__ == "__main__":
    sys.exit(main())
