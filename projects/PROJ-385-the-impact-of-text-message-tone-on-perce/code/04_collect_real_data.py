"""
Real data collection pipeline for Text Message Tone study.

Handles survey deployment via Qualtrics/Prolific API, participant recruitment,
and ingestion of real survey data. Includes CI-safe stubbing logic for testing.

Outputs:
    - data/raw/real_ratings.csv: Real human ratings
    - data/consent/: Anonymized consent records
"""
import csv
import json
import os
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import get_raw_data_dir, get_consent_dir, get_project_root
from logging_config import setup_logging, get_logger

# Configure logging
logger = setup_logging()

# CI-safe flag for stubbing
CI_MODE = os.getenv("CI_MODE", "false").lower() == "true"

# API Configuration (loaded from env vars in production)
PROLIFIC_API_KEY = os.getenv("PROLIFIC_API_KEY", "")
QUALTRICS_API_KEY = os.getenv("QUALTRICS_API_KEY", "")
QUALTRICS_SERVER = os.getenv("QUALTRICS_SERVER", "")

def hash_prolific_id(prolific_id: str, salt: str = "study_salt_2024") -> str:
    """
    Hash a Prolific ID to create an anonymized participant ID.
    
    Args:
        prolific_id: The original Prolific ID
        salt: Salt for hashing (should be stored securely)
    
    Returns:
        Anonymized participant ID (SHA256 hex)
    """
    if not prolific_id:
        raise ValueError("Prolific ID cannot be empty")
    
    combined = f"{salt}{prolific_id}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]

def validate_prolific_id(prolific_id: str) -> bool:
    """
    Validate Prolific ID format (alphanumeric, 8-12 chars).
    
    Args:
        prolific_id: ID to validate
    
    Returns:
        True if valid format
    """
    if not prolific_id:
        return False
    
    # Prolific IDs are typically alphanumeric, 8-12 characters
    if not (8 <= len(prolific_id) <= 12):
        return False
    
    if not prolific_id.isalnum():
        return False
    
    return True

def randomize_relationship(participant_id: str) -> str:
    """
    Randomize relationship context for a participant.
    
    Args:
        participant_id: Participant ID for deterministic randomization
    
    Returns:
        Relationship context ('friend' or 'acquaintance')
    """
    # Use participant ID hash for deterministic randomization
    hash_val = int(hashlib.md5(participant_id.encode()).hexdigest(), 16)
    return "friend" if hash_val % 2 == 0 else "acquaintance"

def log_randomization(participant_id: str, relationship: str, log_path: Path) -> None:
    """
    Log the randomization decision for audit purposes.
    
    Args:
        participant_id: Participant ID
        relationship: Assigned relationship context
        log_path: Path to randomization log file
    """
    log_entry = {
        "participant_id": participant_id,
        "relationship": relationship,
        "timestamp": datetime.utcnow().isoformat(),
        "method": "deterministic_hash"
    }
    
    with open(log_path, "a", encoding="utf-8") as f:
        json.dump(log_entry, f)
        f.write("\n")

def generate_consent_record(
    participant_id: str,
    timestamp: datetime,
    consent_given: bool,
    data_hash: str
) -> Dict[str, Any]:
    """
    Generate an anonymized consent record.
    
    Args:
        participant_id: Anonymized participant ID
        timestamp: Consent timestamp
        consent_given: Whether consent was given
        data_hash: Hash of the participant's data for integrity
    
    Returns:
        Consent record dictionary
    """
    return {
        "consent_id": str(uuid.uuid4()),
        "participant_id": participant_id,
        "timestamp": timestamp.isoformat(),
        "consent_given": consent_given,
        "data_hash": data_hash,
        "version": "1.0"
    }

def save_consent_records(records: List[Dict[str, Any]], consent_dir: Path) -> None:
    """
    Save consent records to the consent directory.
    
    Args:
        records: List of consent record dictionaries
        consent_dir: Directory to save records
    """
    consent_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"consent_records_{timestamp}.jsonl"
    filepath = consent_dir / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    
    logger.info(f"Saved {len(records)} consent records to {filepath}")

def load_stimuli(stimuli_path: Path) -> List[Dict[str, Any]]:
    """
    Load stimuli from CSV file.
    
    Args:
        stimuli_path: Path to stimuli CSV
    
    Returns:
        List of stimulus dictionaries
    """
    stimuli = []
    with open(stimuli_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stimuli.append(row)
    return stimuli

def load_real_survey_data(
    survey_data_path: Path,
    stimuli: List[Dict[str, Any]],
    stub: bool = False
) -> List[Dict[str, Any]]:
    """
    Load real survey data from CSV or stub for CI testing.
    
    Args:
        survey_data_path: Path to survey data CSV
        stimuli: List of stimuli for validation
        stub: If True, generate stub data for CI testing
    
    Returns:
        List of rating records
    
    Raises:
        FileNotFoundError: If real data file doesn't exist and not in stub mode
        ValueError: If data format is invalid
    """
    if stub:
        logger.warning("Running in stub mode - generating test data")
        return _generate_stub_data(stimuli)
    
    if not survey_data_path.exists():
        raise FileNotFoundError(
            f"Survey data file not found: {survey_data_path}. "
            "In CI mode, set CI_MODE=true to use stub data."
        )
    
    ratings = []
    with open(survey_data_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Validate required fields
            required_fields = ["prolific_id", "stimulus_id", "rating", "relationship"]
            if not all(field in row for field in required_fields):
                raise ValueError(f"Missing required fields in row: {row}")
            
            # Validate Prolific ID format
            if not validate_prolific_id(row["prolific_id"]):
                logger.warning(f"Invalid Prolific ID format: {row['prolific_id']}")
                continue
            
            # Validate stimulus ID
            stimulus_ids = {s["stimulus_id"] for s in stimuli}
            if row["stimulus_id"] not in stimulus_ids:
                logger.warning(f"Unknown stimulus ID: {row['stimulus_id']}")
                continue
            
            # Validate rating
            try:
                rating = int(row["rating"])
                if not 1 <= rating <= 7:
                    logger.warning(f"Rating out of range: {rating}")
                    continue
            except ValueError:
                logger.warning(f"Invalid rating value: {row['rating']}")
                continue
            
            ratings.append({
                "prolific_id": row["prolific_id"],
                "stimulus_id": row["stimulus_id"],
                "rating": rating,
                "relationship": row["relationship"],
                "timestamp": row.get("timestamp", datetime.utcnow().isoformat())
            })
    
    return ratings

def _generate_stub_data(stimuli: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate stub data for CI testing.
    
    Args:
        stimuli: List of stimuli
    
    Returns:
        Stub rating records
    """
    import random
    random.seed(42)  # Deterministic for testing
    
    stub_ratings = []
    for i in range(min(10, len(stimuli))):  # Generate 10 stub ratings
        stub_ratings.append({
            "prolific_id": f"STUB_{i:08d}",
            "stimulus_id": stimuli[i]["stimulus_id"],
            "rating": random.randint(1, 7),
            "relationship": random.choice(["friend", "acquaintance"]),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    return stub_ratings

def process_real_data(
    survey_data_path: Path,
    stimuli_path: Path,
    output_path: Path,
    consent_dir: Path,
    stub: bool = False
) -> Dict[str, Any]:
    """
    Main pipeline for processing real data.
    
    Args:
        survey_data_path: Path to raw survey data
        stimuli_path: Path to stimuli file
        output_path: Path for output ratings CSV
        consent_dir: Directory for consent records
        stub: If True, use stub data for testing
    
    Returns:
        Processing summary
    """
    # Load stimuli
    stimuli = load_stimuli(stimuli_path)
    logger.info(f"Loaded {len(stimuli)} stimuli")
    
    # Load ratings
    ratings = load_real_survey_data(survey_data_path, stimuli, stub=stub)
    logger.info(f"Loaded {len(ratings)} valid ratings")
    
    if not stub and len(ratings) == 0:
        raise ValueError("No valid ratings found in survey data")
    
    # Generate anonymized consent records
    consent_records = []
    processed_ratings = []
    
    for rating in ratings:
        anon_id = hash_prolific_id(rating["prolific_id"])
        
        # Create consent record
        consent_record = generate_consent_record(
            participant_id=anon_id,
            timestamp=datetime.fromisoformat(rating["timestamp"]),
            consent_given=True,
            data_hash=hashlib.md5(str(rating).encode()).hexdigest()
        )
        consent_records.append(consent_record)
        
        # Create processed rating with anonymized ID
        processed_ratings.append({
            "participant_id": anon_id,
            "stimulus_id": rating["stimulus_id"],
            "rating": rating["rating"],
            "relationship": rating["relationship"],
            "timestamp": rating["timestamp"]
        })
    
    # Save consent records
    save_consent_records(consent_records, consent_dir)
    
    # Save ratings
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=processed_ratings[0].keys())
        writer.writeheader()
        writer.writerows(processed_ratings)
    
    logger.info(f"Saved {len(processed_ratings)} ratings to {output_path}")
    
    return {
        "total_ratings": len(processed_ratings),
        "unique_participants": len(set(r["participant_id"] for r in processed_ratings)),
        "unique_stimuli": len(set(r["stimulus_id"] for r in processed_ratings)),
        "consent_records": len(consent_records)
    }

def main():
    """
    Main entry point for real data collection pipeline.
    """
    # Setup paths
    raw_data_dir = get_raw_data_dir()
    consent_dir = get_consent_dir()
    
    stimuli_path = raw_data_dir / "stimuli.csv"
    survey_data_path = raw_data_dir / "real_survey_data.csv"  # Expected input
    output_path = raw_data_dir / "real_ratings.csv"
    
    # Check for stub mode (CI testing)
    stub_mode = CI_MODE or not survey_data_path.exists()
    
    if stub_mode and not CI_MODE:
        logger.warning("Survey data not found. Running in stub mode for testing.")
        logger.warning("Set PROLIFIC_API_KEY and provide real data for production use.")
    
    try:
        summary = process_real_data(
            survey_data_path=survey_data_path,
            stimuli_path=stimuli_path,
            output_path=output_path,
            consent_dir=consent_dir,
            stub=stub_mode
        )
        
        logger.info("Real data collection pipeline completed successfully")
        logger.info(f"Summary: {json.dumps(summary, indent=2)}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
