import os
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from synchrony import get_logger

# Constants defined in the spec
MIN_TRIALS_PER_CONDITION = 10
MAX_ARTIFACT_REMOVAL_RATIO = 0.50

def ensure_exclusions_file_exists(exclusions_path: Optional[Path] = None) -> Path:
    """Ensure the exclusions file exists and has a header row."""
    if exclusions_path is None:
        exclusions_path = Path("data/exclusions.csv")
    
    exclusions_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not exclusions_path.exists():
        with open(exclusions_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'reason', 'timestamp'])
    
    return exclusions_path

def log_exclusion(subject_id: str, reason: str, exclusions_path: Optional[Path] = None) -> None:
    """Log an exclusion to the CSV file."""
    if exclusions_path is None:
        exclusions_path = Path("data/exclusions.csv")
    
    ensure_exclusions_file_exists(exclusions_path)
    
    timestamp = datetime.now().isoformat()
    
    with open(exclusions_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([subject_id, reason, timestamp])

def evaluate_subject_for_exclusion(
    subject_id: str,
    trials_per_condition: Dict[str, int],
    artifact_removal_ratio: float,
    exclusions_path: Optional[Path] = None
) -> Optional[str]:
    """
    Evaluate a subject for exclusion based on trial counts and artifact removal.
    
    Returns:
        The exclusion reason string if the subject should be excluded, None otherwise.
    """
    # Check trial counts
    for condition, count in trials_per_condition.items():
        if count < MIN_TRIALS_PER_CONDITION:
            return "insufficient_trials"
    
    # Check artifact removal ratio
    if artifact_removal_ratio > MAX_ARTIFACT_REMOVAL_RATIO:
        return "excessive_artifact_removal"
    
    return None

def run_exclusion_check(
    subject_ids: List[str],
    trials_per_condition_map: Dict[str, Dict[str, int]],
    artifact_removal_map: Dict[str, float],
    exclusions_path: Optional[Path] = None
) -> Tuple[int, List[str]]:
    """
    Run exclusion checks for all subjects.
    
    Args:
        subject_ids: List of subject IDs to check.
        trials_per_condition_map: Dict mapping subject_id to dict of condition -> trial count.
        artifact_removal_map: Dict mapping subject_id to artifact removal ratio.
        exclusions_path: Path to the exclusions CSV file.
    
    Returns:
        Tuple of (valid_subject_count, list of excluded subject IDs).
    """
    if exclusions_path is None:
        exclusions_path = Path("data/exclusions.csv")
    
    ensure_exclusions_file_exists(exclusions_path)
    
    excluded_subjects = []
    valid_count = 0
    
    for subject_id in subject_ids:
        trials = trials_per_condition_map.get(subject_id, {})
        artifact_ratio = artifact_removal_map.get(subject_id, 0.0)
        
        reason = evaluate_subject_for_exclusion(
            subject_id,
            trials,
            artifact_ratio,
            exclusions_path
        )
        
        if reason:
            log_exclusion(subject_id, reason, exclusions_path)
            excluded_subjects.append(subject_id)
        else:
            valid_count += 1
    
    return valid_count, excluded_subjects

def get_excluded_subjects(exclusions_path: Optional[Path] = None) -> List[Dict[str, str]]:
    """
    Read the exclusions file and return a list of excluded subjects with reasons.
    
    Returns:
        List of dicts with keys 'subject_id' and 'reason'.
    """
    if exclusions_path is None:
        exclusions_path = Path("data/exclusions.csv")
    
    if not exclusions_path.exists():
        return []
    
    excluded = []
    with open(exclusions_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            excluded.append({
                'subject_id': row['subject_id'],
                'reason': row['reason']
            })
    
    return excluded

def main():
    """Main entry point for testing exclusion logic."""
    logger = get_logger()
    logger.log("exclusion_logic_test", operation="main")
    
    # Example usage
    test_subjects = ['sub-01', 'sub-02', 'sub-03']
    test_trials = {
        'sub-01': {'switch': 15, 'stay': 15},
        'sub-02': {'switch': 5, 'stay': 15},  # Should be excluded
        'sub-03': {'switch': 20, 'stay': 20}
    }
    test_artifacts = {
        'sub-01': 0.1,
        'sub-02': 0.1,
        'sub-03': 0.6  # Should be excluded
    }
    
    valid_count, excluded = run_exclusion_check(
        test_subjects,
        test_trials,
        test_artifacts
    )
    
    print(f"Valid subjects: {valid_count}")
    print(f"Excluded subjects: {excluded}")

if __name__ == "__main__":
    main()
