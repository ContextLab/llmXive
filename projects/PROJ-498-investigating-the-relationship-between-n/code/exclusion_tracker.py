import csv
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from logging_setup import get_logger

EXCLUSIONS_FILE = "data/exclusions.csv"

def ensure_exclusions_file_exists() -> None:
    """Ensure the exclusions CSV file exists with the correct header."""
    path = Path(EXCLUSIONS_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'reason'])

def log_exclusion(subject_id: str, reason: str) -> None:
    """
    Log an exclusion to the CSV file.
    
    Args:
        subject_id: The ID of the excluded subject.
        reason: The reason for exclusion (e.g., "insufficient trials", "excessive artifact removal").
    """
    ensure_exclusions_file_exists()
    logger = get_logger()
    logger.info(f"Excluding subject {subject_id}: {reason}")
    
    with open(EXCLUSIONS_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([subject_id, reason])

def evaluate_subject_for_exclusion(
    subject_id: str, 
    n_trials_per_condition: Dict[str, int], 
    total_trials_initial: int, 
  ) -> Optional[str]:
    """
    Evaluate a subject for exclusion based on trial counts and artifact removal rates.
    
    Criteria:
    - Exclude if <10 valid trials for ANY condition (reason: "insufficient trials")
    - Exclude if >50% of initial trials were removed as artifacts (reason: "excessive artifact removal")
    
    Args:
        subject_id: The subject identifier.
        n_trials_per_condition: Dictionary mapping condition names to valid trial counts.
        total_trials_initial: The number of trials before artifact removal.
        
    Returns:
        The exclusion reason string if the subject should be excluded, None otherwise.
    """
    # Check for insufficient trials (< 10 in any condition)
    for condition, count in n_trials_per_condition.items():
        if count < 10:
            return "insufficient trials"
    
    # Check for excessive artifact removal (> 50%)
    if total_trials_initial > 0:
        # Calculate how many trials remain
        total_trials_final = sum(n_trials_per_condition.values())
        removed_trials = total_trials_initial - total_trials_final
        removal_rate = removed_trials / total_trials_initial
        
        if removal_rate > 0.50:
            return "excessive artifact removal"
    
    return None

def get_excluded_subjects() -> List[Tuple[str, str]]:
    """
    Read the exclusions file and return a list of (subject_id, reason) tuples.
    
    Returns:
        List of tuples containing subject ID and exclusion reason.
    """
    if not os.path.exists(EXCLUSIONS_FILE):
        return []
        
    exclusions = []
    with open(EXCLUSIONS_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exclusions.append((row['subject_id'], row['reason']))
    return exclusions

def main():
    """
    Main entry point for testing the exclusion tracker.
    This is a simple test to verify the file structure and logging.
    """
    logger = get_logger()
    logger.info("Testing exclusion tracker...")
    
    # Ensure file exists
    ensure_exclusions_file_exists()
    
    # Log a test exclusion
    log_exclusion("test_subject_001", "insufficient trials")
    
    # Verify it was logged
    excluded = get_excluded_subjects()
    if excluded:
        logger.info(f"Successfully logged exclusion: {excluded[-1]}")
    else:
        logger.error("Failed to log exclusion.")

if __name__ == "__main__":
    main()
