"""
Exclusion Tracker Module.
Manages the tracking of excluded subjects based on data quality or quantity.
"""
import csv
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import the robust logger
from synchrony import get_logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
EXCLUSIONS_PATH = DATA_DIR / "exclusions.csv"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def ensure_exclusions_file_exists() -> None:
    """Ensure the exclusions CSV file exists with headers."""
    if not EXCLUSIONS_PATH.exists():
        with open(EXCLUSIONS_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'reason', 'timestamp'])


def log_exclusion(subject_id: str, reason: str) -> None:
    """Log an exclusion event."""
    ensure_exclusions_file_exists()
    timestamp = datetime.utcnow().isoformat()
    with open(EXCLUSIONS_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([subject_id, reason, timestamp])


def evaluate_subject_for_exclusion(subject_id: str, trials_per_condition: int, artifact_ratio: float) -> Optional[str]:
    """
    Evaluate a subject for exclusion based on trial count and artifact ratio.
    Returns reason string if excluded, None otherwise.
    """
    MIN_TRIALS = 10
    MAX_ARTIFACT_RATIO = 0.50

    if trials_per_condition < MIN_TRIALS:
        return "insufficient_trials"
    
    if artifact_ratio > MAX_ARTIFACT_RATIO:
        return "excessive_artifact_removal"
    
    return None


def get_excluded_subjects() -> List[str]:
    """Retrieve list of excluded subject IDs."""
    ensure_exclusions_file_exists()
    excluded = []
    with open(EXCLUSIONS_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            excluded.append(row['subject_id'])
    return excluded


def main() -> None:
    """Main entry point."""
    logger = get_logger("exclusion_tracker")
    logger.log("exclusion_tracker_initialized")
    print("Exclusion tracker module loaded.")


if __name__ == "__main__":
    main()
