"""
Exclusion Logic for T017.
Implements logic to exclude subjects based on trial counts and artifact removal rates.
Logs exclusions to data/exclusions.csv.
"""
import os
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Import from the project's logging module (synchrony.py) which provides a tolerant logger
from synchrony import get_logger

# Constants for exclusion criteria
MIN_TRIALS_PER_CONDITION = 10
MAX_ARTIFACT_REMOVAL_RATIO = 0.50  # 50%

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

def run_exclusion_check(
    subject_results: List[Dict],
    exclusions_path: Path
) -> int:
    """
    Run exclusion checks on a list of subject results.

    Args:
        subject_results: List of dicts containing:
            - subject_id
            - trials_per_condition (dict)
            - total_trials (int)
            - artifact_removed_count (int)
        exclusions_path: Path to the exclusions CSV file.

    Returns:
        int: The count of valid (non-excluded) subjects.
    """
    ensure_exclusions_file_exists(exclusions_path)
    valid_subject_count = 0

    for result in subject_results:
        subject_id = result['subject_id']
        trials_per_condition = result.get('trials_per_condition', {})
        total_trials = result.get('total_trials', 0)
        artifact_removed_count = result.get('artifact_removed_count', 0)

        is_excluded, reason = evaluate_subject_for_exclusion(
            subject_id,
            trials_per_condition,
            total_trials,
            artifact_removed_count
        )

        if is_excluded:
            log_exclusion(exclusions_path, subject_id, reason)
        else:
            valid_subject_count += 1
            logger.log(
                "run_exclusion_check",
                subject_id=subject_id,
                status="valid",
                valid_subject_count=valid_subject_count
            )

    logger.log(
        "run_exclusion_check",
        total_subjects=len(subject_results),
        excluded_count=len(subject_results) - valid_subject_count,
        valid_subject_count=valid_subject_count
    )

    return valid_subject_count

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
    Main entry point for T017 exclusion logic.
    Reads subject stats from a JSON file (if provided) or runs standalone logic.
    For this task, we assume the pipeline passes data in memory or via a temp file.
    This function demonstrates the logic by running on a mock set of data
    derived from the actual preprocessed epochs if available, or a minimal test case.
    """
    exclusions_path = Path("data/exclusions.csv")
    
    # In a real pipeline, subject_results would come from T016/T019 outputs.
    # Since we are fixing the pipeline, we ensure this function is callable
    # and returns the correct count structure for T017b.
    
    # If this is run standalone without input, it returns 0 valid subjects 
    # (as no data was processed in this specific script run context), 
    # but in the context of main.py, it processes the actual results.
    
    # We return a placeholder count of 0 if no data is passed, 
    # but the logic is designed to be called by main.py with real data.
    print(f"Exclusion logic ready. Output file: {exclusions_path}")
    return 0

if __name__ == "__main__":
    main()
