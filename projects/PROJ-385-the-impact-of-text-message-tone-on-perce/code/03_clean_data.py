import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set, Optional

from config import get_processed_data_dir, get_data_dir, get_project_root
from logging_config import setup_logging, get_logger, log_pipeline_step, log_exclusion

# Constants for straight-lining detection
STRAIGHT_LINING_THRESHOLD = 0.85  # Proportion of identical ratings to flag
MIN_RESPONSES_FOR_CHECK = 5       # Minimum responses needed to check for straight-lining

def load_stimuli(stimuli_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load stimuli data from CSV."""
    if stimuli_path is None:
        stimuli_path = get_data_dir() / "raw" / "stimuli.csv"
    
    stimuli = []
    with open(stimuli_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stimuli.append(row)
    return stimuli

def load_ratings(ratings_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load ratings data from CSV."""
    if ratings_path is None:
        ratings_path = get_processed_data_dir() / "anonymised_ratings.csv"
    
    ratings = []
    with open(ratings_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                row['rating'] = float(row['rating']) if row['rating'] else None
                row['stimulus_id'] = int(row['stimulus_id'])
                row['participant_id'] = int(row['participant_id'])
            except (ValueError, KeyError):
                pass
            ratings.append(row)
    return ratings

def detect_straight_lining(ratings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect straight-lining behavior in participant responses.
    
    Straight-lining is defined as a participant giving the same rating
    for a high proportion of their responses (above threshold).
    
    Returns a dictionary with:
    - excluded_participants: Set of participant IDs to exclude
    - exclusion_reasons: Dict mapping participant ID to reason
    - statistics: Summary stats about the detection
    """
    if not ratings:
        return {
            "excluded_participants": set(),
            "exclusion_reasons": {},
            "statistics": {
                "total_participants": 0,
                "flagged_participants": 0,
                "excluded_participants": 0
            }
        }
    
    # Group ratings by participant
    participant_ratings: Dict[int, List[float]] = {}
    for rating_row in ratings:
        pid = rating_row.get('participant_id')
        if pid is None:
            continue
        if pid not in participant_ratings:
            participant_ratings[pid] = []
        if rating_row.get('rating') is not None:
            participant_ratings[pid].append(rating_row['rating'])
    
    excluded_participants = set()
    exclusion_reasons = {}
    flagged_count = 0
    
    for pid, responses in participant_ratings.items():
        if len(responses) < MIN_RESPONSES_FOR_CHECK:
            continue
        
        # Count occurrences of each rating value
        rating_counts = {}
        for r in responses:
            rating_counts[r] = rating_counts.get(r, 0) + 1
        
        # Find the most common rating
        most_common_count = max(rating_counts.values())
        proportion = most_common_count / len(responses)
        
        if proportion >= STRAIGHT_LINING_THRESHOLD:
            excluded_participants.add(pid)
            exclusion_reasons[pid] = f"Straight-lining detected: {proportion:.1%} identical ratings ({most_common_count}/{len(responses)})"
            flagged_count += 1
    
    return {
        "excluded_participants": excluded_participants,
        "exclusion_reasons": exclusion_reasons,
        "statistics": {
            "total_participants": len(participant_ratings),
            "flagged_participants": flagged_count,
            "excluded_participants": len(excluded_participants)
        }
    }

def handle_missing_data(ratings: List[Dict[str, Any]], 
                       excluded_participants: Set[int]) -> List[Dict[str, Any]]:
    """
    Filter out ratings from excluded participants and rows with missing ratings.
    Implements listwise deletion for missing data.
    """
    cleaned = []
    for row in ratings:
        pid = row.get('participant_id')
        rating = row.get('rating')
        
        # Exclude participants flagged for straight-lining
        if pid in excluded_participants:
            continue
        
        # Exclude rows with missing ratings (listwise deletion)
        if rating is None:
            continue
        
        cleaned.append(row)
    
    return cleaned

def save_cleaning_log(exclusion_data: Dict[str, Any], 
                     output_path: Optional[Path] = None) -> Path:
    """Save the cleaning log to a JSON file."""
    if output_path is None:
        output_path = get_processed_data_dir() / "cleaning_log.json"
    
    # Convert set to list for JSON serialization
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "excluded_participants": list(exclusion_data["excluded_participants"]),
        "exclusion_reasons": exclusion_data["exclusion_reasons"],
        "statistics": exclusion_data["statistics"]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    
    return output_path

def save_cleaned_ratings(cleaned_ratings: List[Dict[str, Any]], 
                        output_path: Optional[Path] = None) -> Path:
    """Save cleaned ratings to CSV."""
    if output_path is None:
        output_path = get_processed_data_dir() / "cleaned_ratings.csv"
    
    if not cleaned_ratings:
        # Create empty file with headers
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['participant_id', 'stimulus_id', 'rating', 'relationship', 'cue_intensity'])
        return output_path
    
    # Get fieldnames from first row
    fieldnames = list(cleaned_ratings[0].keys())
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in cleaned_ratings:
            writer.writerow(row)
    
    return output_path

def main():
    """Main entry point for data cleaning pipeline."""
    logger = setup_logging()
    logger.info("Starting data cleaning pipeline (T016)")
    
    log_pipeline_step(logger, "T016", "Data Cleaning", "Starting straight-lining detection and missing data handling")
    
    # Load data
    logger.info("Loading stimuli data...")
    stimuli = load_stimuli()
    logger.info(f"Loaded {len(stimuli)} stimuli")
    
    logger.info("Loading ratings data...")
    ratings = load_ratings()
    logger.info(f"Loaded {len(ratings)} ratings")
    
    # Detect straight-lining
    logger.info("Detecting straight-lining behavior...")
    straight_lining_results = detect_straight_lining(ratings)
    
    logger.info(f"Straight-lining detection complete:")
    logger.info(f"  - Total participants: {straight_lining_results['statistics']['total_participants']}")
    logger.info(f"  - Flagged for straight-lining: {straight_lining_results['statistics']['flagged_participants']}")
    logger.info(f"  - Excluded: {straight_lining_results['statistics']['excluded_participants']}")
    
    # Log exclusions
    for pid, reason in straight_lining_results['exclusion_reasons'].items():
        log_exclusion(logger, "straight_lining", pid, reason)
    
    # Handle missing data and filter
    logger.info("Handling missing data and filtering...")
    cleaned_ratings = handle_missing_data(ratings, straight_lining_results['excluded_participants'])
    
    logger.info(f"Cleaned ratings: {len(cleaned_ratings)} rows (from {len(ratings)} original)")
    
    # Save outputs
    logger.info("Saving cleaning log...")
    log_path = save_cleaning_log(straight_lining_results)
    logger.info(f"Cleaning log saved to: {log_path}")
    
    logger.info("Saving cleaned ratings...")
    cleaned_path = save_cleaned_ratings(cleaned_ratings)
    logger.info(f"Cleaned ratings saved to: {cleaned_path}")
    
    log_pipeline_step(logger, "T016", "Data Cleaning", "Completed successfully", 
                    extra={"cleaned_rows": len(cleaned_ratings), "excluded_participants": len(straight_lining_results['excluded_participants'])})
    
    logger.info("Data cleaning pipeline completed successfully")
    return cleaned_path

if __name__ == "__main__":
    main()