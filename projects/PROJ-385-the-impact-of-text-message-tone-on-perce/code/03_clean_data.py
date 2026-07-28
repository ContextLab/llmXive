"""
Data Cleaning Module for Text Message Tone Study.

This module implements:
1. Straight-lining detection (zero variance across stimuli).
2. Missing data handling (listwise deletion for participants who did not rate all stimuli).
3. Logging of exclusions to data/processed/cleaning_log.csv.
"""
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set, Optional

# Import configuration and logging helpers from existing project files
from config import get_processed_data_dir, get_raw_data_dir
from logging_config import setup_logging, get_logger, log_exclusion

# Ensure logging is configured
logger = setup_logging()


def load_stimuli() -> List[Dict[str, Any]]:
    """
    Load stimuli from data/raw/stimuli.csv.

    Returns:
        List of dictionaries representing each stimulus row.
    """
    stimuli_path = get_raw_data_dir() / "stimuli.csv"
    if not stimuli_path.exists():
        raise FileNotFoundError(f"Stimuli file not found at {stimuli_path}. "
                                "Please run 01_generate_stimuli.py first.")

    stimuli = []
    with open(stimuli_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stimuli.append(row)
    return stimuli


def load_ratings() -> List[Dict[str, Any]]:
    """
    Load ratings from data/raw/ratings.csv.

    Returns:
        List of dictionaries representing each rating row.
    """
    ratings_path = get_raw_data_dir() / "ratings.csv"
    if not ratings_path.exists():
        raise FileNotFoundError(f"Ratings file not found at {ratings_path}. "
                                "Please run 02_simulate_ratings.py first.")

    ratings = []
    with open(ratings_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ratings.append(row)
    return ratings


def detect_straight_lining(stimuli: List[Dict[str, Any]], ratings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect straight-lining (zero variance) and missing data (listwise deletion).

    Requirements:
    1. Flags participants with zero variance across the FULL set of stimuli.
    2. Verifies that the count of rated stimuli for a participant equals the total stimulus count.
    3. If a participant's rated count < total stimulus count, implements listwise deletion.

    Args:
        stimuli: List of stimulus dictionaries.
        ratings: List of rating dictionaries.

    Returns:
        Dictionary containing:
            - excluded_participants: List of dicts with participant_id and reason.
            - kept_participants: List of participant IDs kept for analysis.
    """
    total_stimuli_count = len(stimuli)
    stimulus_ids = {s["id"] for s in stimuli}

    # Group ratings by participant
    participant_ratings: Dict[str, Dict[str, float]] = {}
    for r in ratings:
        p_id = r["participant_id"]
        if p_id not in participant_ratings:
            participant_ratings[p_id] = {}
        participant_ratings[p_id][r["stimulus_id"]] = float(r["rating"])

    excluded_participants = []
    kept_participants = []

    for p_id, rated_stimuli in participant_ratings.items():
        rated_count = len(rated_stimuli)
        rated_ids = set(rated_stimuli.keys())

        # 1. Check for missing data (Listwise Deletion)
        if rated_count < total_stimuli_count:
            missing_ids = stimulus_ids - rated_ids
            reason = f"Missing data: rated {rated_count}/{total_stimuli_count} stimuli. Missing: {sorted(missing_ids)}"
            excluded_participants.append({
                "participant_id": p_id,
                "exclusion_reason": reason,
                "timestamp": datetime.now().isoformat(),
                "variance_value": None
            })
            logger.warning(f"Participant {p_id} excluded: {reason}")
            continue

        # 2. Check for straight-lining (Zero Variance)
        # We only reach here if the participant rated ALL stimuli.
        ratings_values = list(rated_stimuli.values())
        
        # Calculate variance manually to avoid dependency on scipy/statsmodels for this check
        # Variance = sum((x - mean)^2) / N
        if len(ratings_values) > 0:
            mean_val = sum(ratings_values) / len(ratings_values)
            variance = sum((x - mean_val) ** 2 for x in ratings_values) / len(ratings_values)
        else:
            variance = 0.0

        if variance == 0:
            reason = "Straight-lining: Zero variance across all stimuli."
            excluded_participants.append({
                "participant_id": p_id,
                "exclusion_reason": reason,
                "timestamp": datetime.now().isoformat(),
                "variance_value": variance
            })
            logger.warning(f"Participant {p_id} excluded: {reason}")
        else:
            kept_participants.append(p_id)

    return {
        "excluded_participants": excluded_participants,
        "kept_participants": kept_participants,
        "total_stimuli": total_stimuli_count,
        "total_participants_initial": len(participant_ratings),
        "total_participants_kept": len(kept_participants),
        "total_participants_excluded": len(excluded_participants)
    }


def save_cleaning_log(exclusion_data: Dict[str, Any]) -> Path:
    """
    Save the cleaning log to data/processed/cleaning_log.csv.

    Args:
        exclusion_data: Dictionary returned by detect_straight_lining.

    Returns:
        Path to the saved CSV file.
    """
    output_dir = get_processed_data_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "cleaning_log.csv"

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["participant_id", "exclusion_reason", "timestamp", "variance_value"])
        writer.writeheader()
        for entry in exclusion_data["excluded_participants"]:
            writer.writerow(entry)

    logger.info(f"Cleaning log saved to {output_path}")
    return output_path


def main():
    """Main entry point for the cleaning script."""
    logger.info("Starting data cleaning pipeline (T016)...")

    try:
        # Load data
        stimuli = load_stimuli()
        ratings = load_ratings()
        logger.info(f"Loaded {len(stimuli)} stimuli and {len(ratings)} ratings.")

        # Detect issues
        results = detect_straight_lining(stimuli, ratings)

        # Save log
        save_cleaning_log(results)

        # Log summary
        logger.info(f"Cleaning complete. Excluded: {results['total_participants_excluded']}, Kept: {results['total_participants_kept']}")
        print(f"Cleaning Complete:")
        print(f"  Total Stimuli: {results['total_stimuli']}")
        print(f"  Initial Participants: {results['total_participants_initial']}")
        print(f"  Excluded: {results['total_participants_excluded']}")
        print(f"  Kept for Analysis: {results['total_participants_kept']}")
        print(f"  Log saved to: {get_processed_data_dir() / 'cleaning_log.csv'}")

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during cleaning: {e}")
        raise


if __name__ == "__main__":
    main()