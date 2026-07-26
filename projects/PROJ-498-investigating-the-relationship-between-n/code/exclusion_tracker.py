import csv
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from logging_setup import get_logger

# Constants for exclusion criteria
MIN_TRIALS_PER_CONDITION = 10
MAX_ARTIFACT_REMOVAL_RATIO = 0.50  # 50%

def ensure_exclusions_file_exists(exclusions_path: Path) -> None:
    """Ensure the exclusions CSV file exists with the correct header."""
    if not exclusions_path.exists():
        exclusions_path.parent.mkdir(parents=True, exist_ok=True)
        with open(exclusions_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'reason'])

def log_exclusion(exclusions_path: Path, subject_id: str, reason: str, logger: Optional[any] = None) -> None:
    """Log an exclusion to the CSV file and optionally to the logger."""
    with open(exclusions_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([subject_id, reason])
    
    if logger:
        logger.info(f"Subject {subject_id} excluded: {reason}")
    else:
        print(f"Subject {subject_id} excluded: {reason}")

def evaluate_subject_for_exclusion(
    subject_id: str,
    trials_per_condition: Dict[str, int],
    total_trials_before_ica: int,
    total_trials_after_ica: int,
    exclusions_path: Path,
    logger: Optional[any] = None
) -> bool:
    """
    Evaluate a subject for exclusion based on:
    1. Insufficient trials (<10 per condition)
    2. Excessive artifact removal (>50% of trials removed)
    
    Returns True if the subject is excluded, False otherwise.
    """
    # Check 1: Insufficient trials per condition
    for condition, count in trials_per_condition.items():
        if count < MIN_TRIALS_PER_CONDITION:
            reason = "insufficient trials"
            log_exclusion(exclusions_path, subject_id, reason, logger)
            return True

    # Check 2: Excessive artifact removal
    if total_trials_before_ica > 0:
        removed_ratio = (total_trials_before_ica - total_trials_after_ica) / total_trials_before_ica
        if removed_ratio > MAX_ARTIFACT_REMOVAL_RATIO:
            reason = "excessive artifact removal"
            log_exclusion(exclusions_path, subject_id, reason, logger)
            return True

    return False

def get_excluded_subjects(exclusions_path: Path) -> List[str]:
    """Read the exclusions file and return a list of excluded subject IDs."""
    if not exclusions_path.exists():
        return []
    
    excluded = []
    with open(exclusions_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            excluded.append(row['subject_id'])
    return excluded

def main():
    """
    Main entry point for testing the exclusion tracker.
    This script demonstrates the functionality by processing a mock subject.
    In the real pipeline, this would be called from preprocess.py or main.py.
    """
    from logging_setup import initialize_logging_and_tracking
    
    # Initialize logging and paths
    logger, exclusions_path = initialize_logging_and_tracking()
    ensure_exclusions_file_exists(exclusions_path)
    
    # Mock data for demonstration
    subject_id = "sub-001"
    trials_per_condition = {
        "switch": 8,  # Less than 10 -> should be excluded
        "stay": 15
    }
    total_before = 23
    total_after = 20  # Removed 3, ratio ~13% (not excessive, but insufficient trials will trigger)
    
    # Evaluate and log exclusion
    is_excluded = evaluate_subject_for_exclusion(
        subject_id,
        trials_per_condition,
        total_before,
        total_after,
        exclusions_path,
        logger
    )
    
    if is_excluded:
        logger.info(f"Subject {subject_id} was excluded.")
    else:
        logger.info(f"Subject {subject_id} passed exclusion checks.")
        
    # Verify the file content
    print(f"Exclusions file content at {exclusions_path}:")
    if exclusions_path.exists():
        with open(exclusions_path, 'r') as f:
            print(f.read())

if __name__ == "__main__":
    main()
