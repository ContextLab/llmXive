"""
Exclusion Logic Module.
Implements the logic to exclude subjects based on trial counts and artifact removal ratios.
"""
import os
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Import robust logger
from synchrony import get_logger
from exclusion_tracker import log_exclusion, ensure_exclusions_file_exists

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
EXCLUSIONS_PATH = DATA_DIR / "exclusions.csv"

MIN_TRIALS_PER_CONDITION = 10
MAX_ARTIFACT_REMOVAL_RATIO = 0.50


def run_exclusion_check(subject_id: str, trials_per_condition: int, artifact_removal_ratio: float) -> bool:
    """
    Run exclusion check for a subject.
    Returns True if subject is excluded, False otherwise.
    """
    logger = get_logger("exclusion_logic")
    
    reason = None
    if trials_per_condition < MIN_TRIALS_PER_CONDITION:
        reason = "insufficient_trials"
    elif artifact_removal_ratio > MAX_ARTIFACT_REMOVAL_RATIO:
        reason = "excessive_artifact_removal"

    if reason:
        log_exclusion(subject_id, reason)
        logger.log("subject_excluded", subject_id=subject_id, reason=reason)
        return True
    
    logger.log("subject_included", subject_id=subject_id)
    return False


def main() -> None:
    """Main entry point."""
    logger = get_logger("exclusion_logic")
    logger.log("exclusion_logic_module_loaded")
    print("Exclusion logic module loaded.")


if __name__ == "__main__":
    main()