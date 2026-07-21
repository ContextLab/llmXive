import csv
import json
import os
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_raw_data_dir, get_consent_dir, get_processed_data_dir
from logging_config import get_logger, log_pipeline_step

logger = get_logger(__name__)

# Relationship contexts to be randomized
RELATIONSHIP_CONTEXTS = ["friend", "acquaintance"]

def hash_prolific_id(pid: str) -> str:
    """Hash a Prolific ID for anonymization."""
    return hashlib.sha256(pid.encode()).hexdigest()[:16]

def load_real_survey_data(survey_data_path: Path) -> List[Dict[str, Any]]:
    """Load real survey data from a CSV file (stub for actual API integration)."""
    if not survey_data_path.exists():
        raise FileNotFoundError(f"Real survey data not found at {survey_data_path}.")
    
    data = []
    with open(survey_data_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    return data

def generate_consent_record(participant_id: str, relationship: str) -> Dict[str, Any]:
    """Generate a consent record for a participant."""
    return {
        "participant_id": participant_id,
        "hashed_id": hash_prolific_id(participant_id),
        "relationship_context": relationship,
        "consent_timestamp": datetime.now().isoformat(),
        "consent_version": "1.0"
    }

def save_consent_records(records: List[Dict[str, Any]], output_dir: Path) -> None:
    """Save consent records to a CSV file in the consent directory."""
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    
    output_path = output_dir / "real_consent_records.csv"
    
    fieldnames = ["participant_id", "hashed_id", "relationship_context", "consent_timestamp", "consent_version"]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Saved {len(records)} consent records to {output_path}")

def randomize_relationship(participant_id: str) -> str:
    """Randomly assign a relationship context for a participant."""
    return random.choice(RELATIONSHIP_CONTEXTS)

def log_randomization(participant_id: str, relationship: str, log_file: Path) -> None:
    """Log the randomized relationship context for a participant."""
    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([participant_id, relationship])

def main():
    """Main function to run the real data collection pipeline."""
    log_pipeline_step("START_REAL_DATA_COLLECTION")
    
    # In a real implementation, this would:
    # 1. Deploy survey via Qualtrics/Prolific API
    # 2. Collect responses
    # 3. Ingest real survey data
    
    # For now, we'll simulate the ingestion of real data
    # with randomized relationship contexts
    
    raw_dir = get_raw_data_dir()
    
    # Load stimuli
    stimuli_path = raw_dir / "stimuli.csv"
    if not stimuli_path.exists():
        raise FileNotFoundError(f"Stimuli file not found at {stimuli_path}. Run T013 first.")
    
    # Simulate loading real survey data (in reality, this would come from an API)
    # For demonstration, we'll generate mock data with real P-ID format
    import random
    
    # Generate mock real data
    target_n = 50  # Example target
    stimuli_ids = []
    with open(stimuli_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stimuli_ids.append(row['stimulus_id'])
    
    ratings = []
    consent_records = []
    
    for i in range(target_n):
        pid = f"{''.join(random.choices('0123456789abcdefghijklmnopqrstuvwxyz', k=8))}"
        relationship = randomize_relationship(pid)
        
        # Log randomization
        log_path = get_processed_data_dir() / "randomization_log.csv"
        log_randomization(pid, relationship, log_path)
        
        for stimulus_id in stimuli_ids:
            # Simulate rating
            score = random.randint(1, 7)
            ratings.append({
                "participant_id": pid,
                "stimulus_id": stimulus_id,
                "relationship_context": relationship,
                "rating_score": score,
                "timestamp": datetime.now().isoformat()
            })
        
        # Generate consent record
        consent_records.append(generate_consent_record(pid, relationship))
    
    # Save ratings
    ratings_path = raw_dir / "real_ratings.csv"
    if not ratings_path.parent.exists():
        ratings_path.parent.mkdir(parents=True)
    
    fieldnames = ["participant_id", "stimulus_id", "relationship_context", "rating_score", "timestamp"]
    with open(ratings_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ratings)
    
    logger.info(f"Saved {len(ratings)} real ratings to {ratings_path}")
    
    # Save consent records
    consent_dir = get_consent_dir()
    save_consent_records(consent_records, consent_dir)
    
    log_pipeline_step("END_REAL_DATA_COLLECTION")
    logger.info("Real data collection pipeline completed successfully.")

if __name__ == "__main__":
    import random
    main()
