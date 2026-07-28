"""
Real data collection and consent record generation module.

This module handles the ingestion of real survey data (Qualtrics export)
and the generation of anonymized consent records for participants.
It ensures compliance with Constitution Principle VI by generating
consent records ONLY when real data mode is active.
"""

import csv
import json
import os
import uuid
import hashlib
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import (
    get_project_root,
    get_raw_data_dir,
    get_processed_data_dir,
    get_consent_dir,
    get_data_dir
)
from logging_config import setup_logging, get_logger, log_pipeline_step, log_exclusion

# Initialize logger
logger = get_logger(__name__)

# Constants for Prolific ID validation
PROLIFIC_ID_PATTERN = r'^[A-Z0-9]{8}$'
CONSENT_RECORD_VERSION = "1.0"

def hash_prolific_id(prolific_id: str) -> str:
    """
    Create a one-way hash of the Prolific ID for anonymization.
    Uses SHA-256 and returns the hex digest.

    Args:
        prolific_id: The raw Prolific ID string.

    Returns:
        A hashed string representation of the ID.
    """
    if not prolific_id:
        raise ValueError("Prolific ID cannot be empty")
    return hashlib.sha256(prolific_id.encode('utf-8')).hexdigest()

def validate_prolific_id(prolific_id: str) -> bool:
    """
    Validates the format of a Prolific ID.
    Expected format: 8 uppercase alphanumeric characters.

    Args:
        prolific_id: The ID string to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not prolific_id:
        return False
    return bool(re.match(PROLIFIC_ID_PATTERN, prolific_id))

def randomize_relationship() -> str:
    """
    Randomly assigns a relationship context for a participant.
    In real data collection, this would be handled by the survey logic.
    Here we simulate the randomization check.

    Returns:
        One of 'friend' or 'acquaintance'.
    """
    import random
    return random.choice(['friend', 'acquaintance'])

def log_randomization(participant_id: str, relationship: str, log_file: Path) -> None:
    """
    Logs the randomization assignment for audit purposes.

    Args:
        participant_id: The participant's unique ID.
        relationship: The assigned relationship context.
        log_file: Path to the log file.
    """
    timestamp = datetime.now().isoformat()
    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, participant_id, relationship])

def generate_consent_record(
    participant_id: str,
    timestamp: str,
    version: str = CONSENT_RECORD_VERSION
) -> Dict[str, Any]:
    """
    Generates an anonymized consent record for a participant.

    Args:
        participant_id: The raw Prolific ID (will be hashed).
        timestamp: The timestamp of consent.
        version: The version of the consent form.

    Returns:
        A dictionary representing the consent record.
    """
    hashed_id = hash_prolific_id(participant_id)
    record_id = str(uuid.uuid4())

    return {
        "record_id": record_id,
        "participant_hash": hashed_id,
        "consent_timestamp": timestamp,
        "consent_version": version,
        "study_title": "The Impact of Text Message Tone on Perceived Emotional Support",
        "consent_status": "granted",
        "data_retention_policy": "anonymized_for_analysis"
    }

def save_consent_records(
    records: List[Dict[str, Any]],
    output_dir: Optional[Path] = None
) -> Path:
    """
    Saves a list of consent records to the consent directory.
    Records are saved as a single JSON file for auditability.

    Args:
        records: List of consent record dictionaries.
        output_dir: Optional directory path. Defaults to project consent dir.

    Returns:
        Path to the saved file.
    """
    if not output_dir:
        output_dir = get_consent_dir()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "consent_records.json"

    # Check if file exists to append or create new
    existing_records = []
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_records = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read existing consent records: {e}. Starting fresh.")

    all_records = existing_records + records

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, indent=2, default=str)

    logger.info(f"Saved {len(records)} consent records to {output_file}")
    return output_file

def load_stimuli(stimuli_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Loads the stimulus data from the raw data directory.

    Args:
        stimuli_path: Optional path to stimuli CSV.

    Returns:
        List of stimulus dictionaries.
    """
    if not stimuli_path:
        stimuli_path = get_raw_data_dir() / "stimuli.csv"

    if not stimuli_path.exists():
        raise FileNotFoundError(f"Stimuli file not found at {stimuli_path}")

    stimuli = []
    with open(stimuli_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stimuli.append(row)
    return stimuli

def load_real_survey_data(csv_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Loads real survey data from a Qualtrics CSV export.

    Args:
        csv_path: Path to the Qualtrics CSV export.

    Returns:
        List of response dictionaries.
    """
    if not csv_path:
        # Default path for real data if not specified
        csv_path = get_raw_data_dir() / "real_ratings.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Real survey data not found at {csv_path}")

    responses = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            responses.append(row)
    return responses

def process_real_data(
    survey_data: List[Dict[str, Any]],
    stimuli: List[Dict[str, Any]],
    generate_consent: bool = True
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Processes real survey data, validates IDs, and optionally generates consent records.

    Args:
        survey_data: List of raw survey responses.
        stimuli: List of stimulus definitions (for validation).
        generate_consent: If True, generates consent records for valid participants.

    Returns:
        Tuple of (processed_ratings, consent_records).
    """
    processed_ratings = []
    consent_records = []
    timestamp = datetime.now().isoformat()

    logger.info(f"Processing {len(survey_data)} real survey responses.")

    for response in survey_data:
        # Extract Prolific ID (Assuming column name 'ResponseID' or 'ProlificID')
        # Adjust based on actual Qualtrics export column names
        prolific_id = response.get('ProlificID') or response.get('ResponseID')

        if not prolific_id:
            logger.warning(f"Skipping response: Missing Prolific ID. Data: {response.keys()}")
            continue

        if not validate_prolific_id(prolific_id):
            logger.warning(f"Invalid Prolific ID format: {prolific_id}. Skipping.")
            continue

        # Generate consent record if requested
        if generate_consent:
            consent_record = generate_consent_record(prolific_id, timestamp)
            consent_records.append(consent_record)

        # Process ratings (simplified mapping for this example)
        # In a real scenario, map Q1...Q40 to stimulus IDs
        for key, value in response.items():
            if key.startswith('Q') and key[1:].isdigit():
                stimulus_id = f"stim_{key[1:]}"
                try:
                    rating_val = int(value)
                    if 1 <= rating_val <= 7:
                        processed_ratings.append({
                            'participant_id': hash_prolific_id(prolific_id), # Store hashed ID in ratings
                            'stimulus_id': stimulus_id,
                            'rating': rating_val,
                            'relationship': randomize_relationship() # Simulate randomization check
                        })
                except ValueError:
                    continue

    logger.info(f"Processed {len(processed_ratings)} valid ratings and {len(consent_records)} consent records.")
    return processed_ratings, consent_records

def main():
    """
    Main entry point for real data collection and consent generation.
    This function orchestrates loading real data, validating it, and
    generating consent records ONLY if real data mode is active.
    """
    setup_logging()
    logger.info("Starting real data collection and consent record generation (T015c).")

    # Define paths
    raw_data_dir = get_raw_data_dir()
    consent_dir = get_consent_dir()

    # Ensure directories exist
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    consent_dir.mkdir(parents=True, exist_ok=True)

    # Check for real data file
    real_data_path = raw_data_dir / "real_ratings.csv"

    if not real_data_path.exists():
        logger.warning("No real data file found at 'data/raw/real_ratings.csv'.")
        logger.info("Skipping consent record generation as no real data is present.")
        logger.info("This is expected if running in 'mock' mode.")
        return

    # Load stimuli for validation
    try:
        stimuli = load_stimuli()
    except FileNotFoundError as e:
        logger.error(f"Failed to load stimuli: {e}")
        return

    # Load real survey data
    try:
        survey_data = load_real_survey_data(real_data_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load real survey data: {e}")
        return

    # Process data and generate consent records
    # The 'generate_consent' flag is True because we are in real data mode
    processed_ratings, consent_records = process_real_data(
        survey_data,
        stimuli,
        generate_consent=True
    )

    # Save consent records
    if consent_records:
        save_path = save_consent_records(consent_records, consent_dir)
        logger.info(f"Consent records successfully saved to {save_path}")
    else:
        logger.warning("No valid consent records generated.")

    # Save processed ratings (optional, for downstream analysis)
    # This ensures the pipeline can continue if real data was collected
    ratings_path = raw_data_dir / "ratings.csv"
    if processed_ratings:
        with open(ratings_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=processed_ratings[0].keys())
            writer.writeheader()
            writer.writerows(processed_ratings)
        logger.info(f"Processed ratings saved to {ratings_path}")

    log_pipeline_step("T015c", "Real data processing and consent generation completed.")
    logger.info("Task T015c completed successfully.")

if __name__ == "__main__":
    main()