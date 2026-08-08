"""
Exclusion Logic Module for T017.
Implements logic to exclude subjects based on trial counts and artifact removal rates.
"""
import os
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Import from existing API surface
from exclusion_tracker import log_exclusion, ensure_exclusions_file_exists
from logging_setup import get_logger

logger = get_logger(__name__)

MIN_TRIALS_PER_CONDITION = 10
MAX_ARTIFACT_REMOVAL_RATIO = 0.50  # 50%

def run_exclusion_check(subject_id: str, min_trials: int, artifact_ratio: float) -> Optional[Dict[str, str]]:
    """
    Central logic to determine exclusion and log it.
    
    Args:
        subject_id: Subject ID.
        min_trials: Minimum trials found in any condition.
        artifact_ratio: Ratio of trials removed (0.0 to 1.0).
    
    Returns:
        Dict with reason if excluded, None otherwise.
    """
    reason = None

    if min_trials < MIN_TRIALS_PER_CONDITION:
        reason = "insufficient_trials"
    elif artifact_ratio > MAX_ARTIFACT_REMOVAL_RATIO:
        reason = "excessive_artifact_removal"

    if reason:
        log_exclusion(subject_id, reason)
        logger.warning(f"Subject {subject_id} excluded: {reason}")
        return {"subject_id": subject_id, "reason": reason}
    
    return None

def main():
    """
    Entry point to demonstrate the exclusion logic.
    """
    ensure_exclusions_file_exists()
    logger.info("Exclusion logic module loaded.")
    logger.info(f"Thresholds: Min Trials={MIN_TRIALS_PER_CONDITION}, Max Artifact Ratio={MAX_ARTIFACT_REMOVAL_RATIO}")

if __name__ == "__main__":
    main()
