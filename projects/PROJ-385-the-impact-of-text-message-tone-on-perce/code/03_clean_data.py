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
    Detect participants who exhibit straight-lining behavior (zero variance in ratings).
    
    A participant is flagged if they provide the same score for ALL stimuli they rated.
    This function checks the variance of the 'support_score' column for each participant.
    
    Args:
        stimuli_path: Path to the stimuli CSV file.
        ratings_path: Path to the ratings CSV file.
        
    Returns:
        A set of participant IDs who are flagged for straight-lining.
    """
    stimuli_ids = load_stimuli(stimuli_path)
    expected_count = len(stimuli_ids)
    
    if expected_count == 0:
        logger.warning("No stimuli found in the stimuli file. Cannot detect straight-lining.")
        return set()
    
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
        # Calculate variance
        # If a participant has fewer ratings than the total stimuli, we still check
        # the variance of the ratings they *did* provide.
        if len(scores) == 0:
            continue
        
        # If only one rating, variance is 0 (or undefined, but we treat as 0 for this check)
        if len(scores) == 1:
            variance = 0.0
        else:
            variance = np.var(scores)
        
        if variance == 0.0:
            flagged_participants.add(pid)
            logger.info(f"Participant {pid} flagged for straight-lining (variance=0.0) with {len(scores)} ratings.")
    
    return flagged_participants

def save_cleaning_log(flagged_participants: Set[str], output_path: Path):
    """
    Save the cleaning log with exclusion flags.
    
    Args:
        flagged_participants: Set of participant IDs flagged for straight-lining.
        output_path: Path to save the cleaning log CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["participant_id", "exclusion_reason"])
        for pid in flagged_participants:
            writer.writerow([pid, "straight-lining"])
    
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
    
    logger.info("Starting straight-lining detection...")
    flagged = detect_straight_lining(stimuli_path, ratings_path)
    save_cleaning_log(flagged, cleaning_log_path)
    logger.info("Straight-lining detection complete.")

if __name__ == "__main__":
    main()