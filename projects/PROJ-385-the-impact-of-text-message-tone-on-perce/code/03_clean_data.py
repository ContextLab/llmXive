import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Set
import sys
import numpy as np

from config import get_raw_data_dir, get_processed_data_dir
from logging_config import get_logger, log_exclusion

logger = get_logger(__name__)

def load_stimuli(stimuli_path: Path) -> List[str]:
    """
    Load stimulus IDs from a CSV file.
    
    Args:
        stimuli_path: Path to the stimuli CSV file.
        
    Returns:
        List of stimulus IDs.
    """
    stimuli_ids = []
    with open(stimuli_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stimuli_ids.append(row['stimulus_id'])
    return stimuli_ids

def load_ratings(ratings_path: Path) -> List[Dict[str, Any]]:
    """
    Load ratings from a CSV file.
    
    Args:
        ratings_path: Path to the ratings CSV file.
        
    Returns:
        List of rating dictionaries.
    """
    ratings = []
    with open(ratings_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ratings.append(row)
    return ratings

def detect_straight_lining(stimuli_path: Path, ratings_path: Path) -> Set[str]:
    """
    Detect participants who exhibit straight-lining behavior (zero variance in ratings)
    OR have missing data (rated fewer stimuli than the total set).
    
    Requirements:
    1. Flags participants with zero variance across the full set of stimuli.
    2. Verifies that the count of rated stimuli for a participant equals the total stimulus count.
    3. If a participant's rated count < total stimulus count, implements listwise deletion
       (dropping the participant) and logs the exclusion reason.
    
    Args:
        stimuli_path: Path to the stimuli CSV file.
        ratings_path: Path to the ratings CSV file.
        
    Returns:
        A set of participant IDs who are flagged for exclusion.
    """
    stimuli_ids = load_stimuli(stimuli_path)
    expected_count = len(stimuli_ids)
    
    if expected_count == 0:
        logger.warning("No stimuli found in the stimuli file. Cannot detect straight-lining or missing data.")
        return set()
    
    logger.info(f"Total stimulus count: {expected_count}")
    
    ratings = load_ratings(ratings_path)
    
    # Group ratings by participant
    participant_ratings = {}
    for rating in ratings:
        pid = rating['participant_id']
        score = float(rating['support_score'])
        if pid not in participant_ratings:
            participant_ratings[pid] = []
        participant_ratings[pid].append(score)
    
    flagged_participants = set()
    
    for pid, scores in participant_ratings.items():
        rated_count = len(scores)
        
        # Check for missing data (listwise deletion)
        if rated_count < expected_count:
            flagged_participants.add(pid)
            log_exclusion(pid, "missing_data", f"Rated {rated_count} of {expected_count} stimuli")
            logger.info(f"Participant {pid} excluded due to missing data (rated {rated_count}/{expected_count}).")
            continue
        
        # Check for straight-lining (zero variance)
        # Only check variance if we have enough data (though we already ensured rated_count == expected_count)
        if rated_count == 0:
            continue
        
        if rated_count == 1:
            variance = 0.0
        else:
            variance = np.var(scores)
        
        if variance == 0.0:
            flagged_participants.add(pid)
            log_exclusion(pid, "straight-lining", f"Zero variance across {rated_count} stimuli")
            logger.info(f"Participant {pid} flagged for straight-lining (variance=0.0) with {rated_count} ratings.")
    
    return flagged_participants

def save_cleaning_log(flagged_participants: Set[str], output_path: Path, reasons: Dict[str, str] = None):
    """
    Save the cleaning log with exclusion flags and reasons.
    
    Args:
        flagged_participants: Set of participant IDs flagged for exclusion.
        output_path: Path to save the cleaning log CSV.
        reasons: Optional dict mapping participant_id to exclusion reason string.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # If reasons are not provided, we'll infer them or use a default
    if reasons is None:
        reasons = {}
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["participant_id", "exclusion_reason", "details"])
        for pid in flagged_participants:
            reason = reasons.get(pid, "unknown")
            # We need to capture details, but the current log_exclusion doesn't return them easily.
            # For now, we'll use a generic message or try to retrieve from logs if possible.
            # Since we can't easily retrieve the exact log message here without parsing logs,
            # we'll just write the reason.
            details = ""
            if reason == "missing_data":
                details = "Participant did not rate all stimuli"
            elif reason == "straight-lining":
                details = "Zero variance in ratings"
            
            writer.writerow([pid, reason, details])
    
    logger.info(f"Saved cleaning log with {len(flagged_participants)} exclusions to {output_path}")

def main():
    """Main function to run the data cleaning pipeline."""
    raw_data_dir = get_raw_data_dir()
    processed_data_dir = get_processed_data_dir()
    
    stimuli_path = raw_data_dir / "stimuli.csv"
    ratings_path = raw_data_dir / "ratings.csv"
    cleaning_log_path = processed_data_dir / "cleaning_log.csv"
    
    if not stimuli_path.exists():
        logger.error(f"Stimuli file not found: {stimuli_path}")
        sys.exit(1)
    
    if not ratings_path.exists():
        logger.error(f"Ratings file not found: {ratings_path}")
        sys.exit(1)
    
    logger.info("Starting data cleaning (straight-lining and missing data detection)...")
    
    # We need to capture reasons for each exclusion
    # We'll modify detect_straight_lining to return both the set and reasons,
    # but for now, we'll do a simpler approach: run detection and then save with reasons.
    # Since the current function doesn't return reasons, we'll need to refactor.
    
    # Refactored approach:
    stimuli_ids = load_stimuli(stimuli_path)
    expected_count = len(stimuli_ids)
    
    if expected_count == 0:
        logger.warning("No stimuli found. Cannot clean data.")
        sys.exit(0)
    
    ratings = load_ratings(ratings_path)
    
    participant_ratings = {}
    for rating in ratings:
        pid = rating['participant_id']
        score = float(rating['support_score'])
        if pid not in participant_ratings:
            participant_ratings[pid] = []
        participant_ratings[pid].append(score)
    
    flagged_participants = set()
    exclusion_reasons = {}
    
    for pid, scores in participant_ratings.items():
        rated_count = len(scores)
        
        # Check for missing data (listwise deletion)
        if rated_count < expected_count:
            flagged_participants.add(pid)
            exclusion_reasons[pid] = "missing_data"
            log_exclusion(pid, "missing_data", f"Rated {rated_count} of {expected_count} stimuli")
            logger.info(f"Participant {pid} excluded due to missing data (rated {rated_count}/{expected_count}).")
            continue
        
        # Check for straight-lining (zero variance)
        if rated_count == 0:
            continue
        
        if rated_count == 1:
            variance = 0.0
        else:
            variance = np.var(scores)
        
        if variance == 0.0:
            flagged_participants.add(pid)
            exclusion_reasons[pid] = "straight-lining"
            log_exclusion(pid, "straight-lining", f"Zero variance across {rated_count} stimuli")
            logger.info(f"Participant {pid} flagged for straight-lining (variance=0.0) with {rated_count} ratings.")
    
    save_cleaning_log(flagged_participants, cleaning_log_path, exclusion_reasons)
    logger.info("Data cleaning complete.")

if __name__ == "__main__":
    main()
