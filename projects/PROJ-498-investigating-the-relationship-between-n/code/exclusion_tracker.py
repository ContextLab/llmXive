"""
Exclusion Tracker for T017.
Manages the exclusions CSV file and provides utilities to log exclusions.
"""
import csv
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import from the project's logging module
from synchrony import get_logger

logger = get_logger(__name__)

def ensure_exclusions_file_exists(exclusions_path: Path) -> None:
    """Ensure the exclusions CSV file exists with the correct header."""
    if not exclusions_path.exists():
        exclusions_path.parent.mkdir(parents=True, exist_ok=True)
        with open(exclusions_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'reason'])
        logger.log("ensure_exclusions_file_exists", path=str(exclusions_path))

def log_exclusion(exclusions_path: Path, subject_id: str, reason: str) -> None:
    """Append an exclusion record to the CSV."""
    ensure_exclusions_file_exists(exclusions_path)
    with open(exclusions_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([subject_id, reason])
    logger.log("log_exclusion", subject_id=subject_id, reason=reason)

def evaluate_subject_for_exclusion(
    subject_id: str,
    trials_per_condition: Dict[str, int],
    total_trials: int,
    artifact_removed_count: int
) -> Tuple[bool, Optional[str]]:
    """
    Evaluate a subject for exclusion based on T017 criteria.

    Args:
        subject_id: The subject identifier.
        trials_per_condition: Dict mapping condition names to trial counts.
        total_trials: Total number of trials before artifact removal.
        artifact_removed_count: Number of trials removed due to artifacts.

    Returns:
        Tuple of (is_excluded, reason). If not excluded, reason is None.
    """
    MIN_TRIALS_PER_CONDITION = 10
    MAX_ARTIFACT_REMOVAL_RATIO = 0.50

    # Check for insufficient trials per condition
    for condition, count in trials_per_condition.items():
        if count < MIN_TRIALS_PER_CONDITION:
            logger.log(
                "evaluate_subject_for_exclusion",
                subject_id=subject_id,
                reason="insufficient_trials",
                condition=condition,
                count=count,
                threshold=MIN_TRIALS_PER_CONDITION
            )
            return True, "insufficient trials"

    # Check for excessive artifact removal
    if total_trials > 0:
        removal_ratio = artifact_removed_count / total_trials
        if removal_ratio > MAX_ARTIFACT_REMOVAL_RATIO:
            logger.log(
                "evaluate_subject_for_exclusion",
                subject_id=subject_id,
                reason="excessive_artifact_removal",
                ratio=removal_ratio,
                threshold=MAX_ARTIFACT_REMOVAL_RATIO
            )
            return True, "excessive artifact removal"

    return False, None

def get_excluded_subjects(exclusions_path: Path) -> List[Dict]:
    """Read the exclusions file and return a list of excluded subjects."""
    if not exclusions_path.exists():
        return []

    excluded = []
    with open(exclusions_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            excluded.append(row)
    return excluded

def main():
    """
    Main entry point for exclusion tracker.
    """
    exclusions_path = Path("data/exclusions.csv")
    print(f"Exclusion tracker initialized. Output file: {exclusions_path}")
    return 0

if __name__ == "__main__":
    main()
