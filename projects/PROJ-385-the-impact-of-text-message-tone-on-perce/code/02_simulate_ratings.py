import csv
import json
import os
import random
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_raw_data_dir, get_consent_dir, get_processed_data_dir
from logging_config import get_logger, log_pipeline_step

logger = get_logger(__name__)

# Relationship contexts to be randomized
RELATIONSHIP_CONTEXTS = ["friend", "acquaintance"]

def load_power_analysis_results() -> int:
    """Load the target sample size N from the power analysis results."""
    processed_dir = get_processed_data_dir()
    path = processed_dir / "power_analysis_results.json"
    if not path.exists():
        raise FileNotFoundError(f"Power analysis results not found at {path}. Run T009 first.")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if 'target_n' not in data:
        raise ValueError("Power analysis results missing 'target_n' key.")
    
    return data['target_n']

def generate_prolific_id() -> str:
    """Generate a mock Prolific ID in the format: 8 characters alphanumeric."""
    # Prolific IDs are typically 8 characters, alphanumeric
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    return "".join(random.choices(chars, k=8))

def validate_prolific_id(pid: str) -> bool:
    """Validate that a Prolific ID matches the expected format."""
    pattern = r'^[0-9a-z]{8}$'
    return bool(re.match(pattern, pid))

def simulate_rating(stimulus_id: str, participant_id: str, relationship: str) -> Dict[str, Any]:
    """Simulate a single rating for a stimulus by a participant."""
    # Simulate a Likert score (1-7) with some randomness
    # In a real scenario, this would depend on stimulus features and relationship
    score = random.randint(1, 7)
    
    return {
        "participant_id": participant_id,
        "stimulus_id": stimulus_id,
        "relationship_context": relationship,
        "rating_score": score,
        "timestamp": "2023-10-27T10:00:00Z"  # Fixed timestamp for reproducibility
    }

def generate_ratings(target_n: int, stimuli: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate ratings for all participants and stimuli."""
    ratings = []
    stimuli_ids = [s['stimulus_id'] for s in stimuli]
    
    for _ in range(target_n):
        pid = generate_prolific_id()
        # Randomize relationship context for this participant
        relationship = random.choice(RELATIONSHIP_CONTEXTS)
        
        for stimulus_id in stimuli_ids:
            rating = simulate_rating(stimulus_id, pid, relationship)
            ratings.append(rating)
    
    return ratings

def log_randomization(participant_id: str, relationship: str, log_file: Path) -> None:
    """Log the randomized relationship context for a participant."""
    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([participant_id, relationship])

def save_ratings(ratings: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the generated ratings to a CSV file."""
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True)
    
    fieldnames = ["participant_id", "stimulus_id", "relationship_context", "rating_score", "timestamp"]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ratings)
    
    logger.info(f"Saved {len(ratings)} ratings to {output_path}")

def generate_mock_consent_log(participant_ids: List[str], output_path: Path) -> None:
    """Generate a mock consent log for simulated participants."""
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True)
    
    fieldnames = ["participant_id", "consent_timestamp", "consent_version"]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for pid in participant_ids:
            writer.writerow({
                "participant_id": pid,
                "consent_timestamp": "2023-10-27T09:00:00Z",
                "consent_version": "1.0"
            })
    
    logger.info(f"Generated mock consent log for {len(participant_ids)} participants at {output_path}")

def load_stimuli(stimuli_path: Path) -> List[Dict[str, Any]]:
    """Load stimuli from a CSV file."""
    if not stimuli_path.exists():
        raise FileNotFoundError(f"Stimuli file not found at {stimuli_path}. Run T013 first.")
    
    stimuli = []
    with open(stimuli_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stimuli.append(row)
    
    return stimuli

def main():
    """Main function to run the mock Prolific data collection simulation."""
    log_pipeline_step("START_SIMULATE_RATINGS")
    
    # Load power analysis results
    target_n = load_power_analysis_results()
    logger.info(f"Target sample size N: {target_n}")
    
    # Load stimuli
    raw_dir = get_raw_data_dir()
    stimuli_path = raw_dir / "stimuli.csv"
    stimuli = load_stimuli(stimuli_path)
    logger.info(f"Loaded {len(stimuli)} stimuli")
    
    # Generate ratings
    ratings = generate_ratings(target_n, stimuli)
    
    # Save ratings
    ratings_path = raw_dir / "ratings.csv"
    save_ratings(ratings, ratings_path)
    
    # Generate participant list for consent log
    participant_ids = list(set(r['participant_id'] for r in ratings))
    
    # Generate mock consent log
    consent_path = get_consent_dir() / "mock_consent_log.csv"
    generate_mock_consent_log(participant_ids, consent_path)
    
    log_pipeline_step("END_SIMULATE_RATINGS")
    logger.info("Mock data collection simulation completed successfully.")

if __name__ == "__main__":
    main()
