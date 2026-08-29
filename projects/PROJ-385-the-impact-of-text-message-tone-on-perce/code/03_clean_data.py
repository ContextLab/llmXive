import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from config import get_processed_data_dir, get_raw_data_dir
from logging_config import setup_logging, get_logger, log_exclusion

def load_ratings():
    """Load anonymised ratings from the processed directory."""
    input_path = get_processed_data_dir() / "anonymised_ratings.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows, reader.fieldnames

def detect_straight_lining(ratings):
    """
    Detect participants with zero variance across all stimuli.
    Returns a set of participant_ids to exclude.
    """
    if not ratings:
        return set()
    
    participant_scores = {}
    for row in ratings:
        pid = row.get('participant_id')
        score = row.get('score')
        if pid is None or score is None:
            continue
        
        if pid not in participant_scores:
            participant_scores[pid] = []
        try:
            participant_scores[pid].append(float(score))
        except ValueError:
            continue
    
    straight_liners = set()
    for pid, scores in participant_scores.items():
        if len(scores) < 2:
            # Cannot compute variance with fewer than 2 points, 
            # but if they have ratings, we check variance.
            # If they have only 1 rating, variance is 0 by definition of a single point?
            # Strictly, variance requires n>=2. We'll flag if n>=2 and variance is 0.
            continue
        
        mean_val = sum(scores) / len(scores)
        variance = sum((x - mean_val) ** 2 for x in scores) / len(scores)
        
        if variance == 0:
            straight_liners.add(pid)
    
    return straight_liners

def handle_missing_data(ratings):
    """
    Identify participants with missing ratings (i.e., not rated all stimuli).
    Returns a set of participant_ids to exclude.
    """
    if not ratings:
        return set()
    
    # Determine the set of all stimulus IDs present in the data
    all_stimuli = set()
    participant_stimuli = {}
    
    for row in ratings:
        pid = row.get('participant_id')
        stim_id = row.get('stimulus_id')
        
        if pid and stim_id:
            all_stimuli.add(stim_id)
            if pid not in participant_stimuli:
                participant_stimuli[pid] = set()
            participant_stimuli[pid].add(stim_id)
    
    total_stimuli_count = len(all_stimuli)
    if total_stimuli_count == 0:
        return set()
    
    missing_participants = set()
    for pid, stimuli_set in participant_stimuli.items():
        if len(stimuli_set) < total_stimuli_count:
            missing_participants.add(pid)
    
    return missing_participants

def save_cleaned_ratings(cleaned_ratings, fieldnames):
    """Save the cleaned dataset to disk."""
    output_path = get_processed_data_dir() / "cleaned_ratings.csv"
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_ratings)
    logging.info(f"Cleaned ratings saved to {output_path}")
    return output_path

def save_cleaning_log(excluded_ids, reasons):
    """Save a log of excluded participants and reasons."""
    output_path = get_processed_data_dir() / "cleaning_log.json"
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "excluded_participants": [
            {"participant_id": pid, "reason": reasons.get(pid, "unknown")}
            for pid in excluded_ids
        ]
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    logging.info(f"Cleaning log saved to {output_path}")

def save_excluded_participants(excluded_ids):
    """Save the list of excluded participant IDs to a CSV."""
    output_path = get_processed_data_dir() / "excluded_participants.csv"
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["participant_id"])
        for pid in excluded_ids:
            writer.writerow([pid])
    logging.info(f"Excluded participants saved to {output_path}")

def main():
    setup_logging()
    logger = get_logger()
    logger.info("Starting data cleaning pipeline (T016b: Listwise Deletion)")

    try:
        # Load data
        ratings, fieldnames = load_ratings()
        logger.info(f"Loaded {len(ratings)} ratings.")

        # 1. Detect straight-lining
        straight_liners = detect_straight_lining(ratings)
        logger.info(f"Detected {len(straight_liners)} straight-lining participants.")

        # 2. Detect missing ratings
        missing_ratings = handle_missing_data(ratings)
        logger.info(f"Detected {len(missing_ratings)} participants with missing ratings.")

        # Combine exclusions
        all_excluded = straight_liners.union(missing_ratings)
        reasons = {}
        for pid in straight_liners:
            reasons[pid] = "straight_lining"
        for pid in missing_ratings:
            if pid in reasons:
                reasons[pid] = "straight_lining, missing_ratings"
            else:
                reasons[pid] = "missing_ratings"

        if all_excluded:
            logger.warning(f"Excluding {len(all_excluded)} participants due to data quality issues.")
            for pid in all_excluded:
                log_exclusion(pid, reasons[pid])
        else:
            logger.info("No participants excluded.")

        # Perform listwise deletion
        cleaned_ratings = [
            row for row in ratings 
            if row.get('participant_id') not in all_excluded
        ]

        # Save outputs
        save_cleaned_ratings(cleaned_ratings, fieldnames)
        save_cleaning_log(all_excluded, reasons)
        save_excluded_participants(all_excluded)

        logger.info("Data cleaning pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during data cleaning: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())