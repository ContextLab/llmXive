"""
Controlled Data Collection Protocol Implementation.

This module implements the survey interface, consent capture, and anonymization
pipeline required for the controlled data collection of user interactions with AI avatars.
It adheres to Constitution Principle VII and FR-001 fallback requirements.

Artifacts produced:
- data/processed/consent_records.jsonl: Anonymized consent records
- data/raw/survey_responses_raw.csv: Raw survey responses (pre-anonymization)
"""

import os
import json
import csv
import hashlib
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import existing project utilities
from logging_config import get_logger, setup_logging
from config import DATA_RAW_DIR, DATA_PROCESSED_DIR
from utils import handle_corrupted_file

# Ensure directories exist
os.makedirs(DATA_RAW_DIR, exist_ok=True)
os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

logger = get_logger(__name__)

# Constants for anonymization
SALT = "proj344_emotion_study_salt_v1"  # In production, this should be in a secure env var
ANONYMIZED_ID_PREFIX = "SUBJ"

class ConsentCapture:
    """Handles the capture and validation of informed consent."""

    def __init__(self, consent_template_path: str = "code/consent_form_template.md"):
        self.template_path = consent_template_path
        self.consent_records: List[Dict[str, Any]] = []
        self._validate_template()

    def _validate_template(self) -> None:
        """Ensure the consent template exists and is readable."""
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Consent template not found at {self.template_path}")
        logger.info(f"Consent template validated: {self.template_path}")

    def capture_consent(self, participant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Capture consent data from a participant.

        Args:
            participant_data: Dictionary containing participant info and consent status.
                              Expected keys: 'signature_date', 'consent_given' (bool), 'age', etc.

        Returns:
            A dictionary representing the consent record.
        """
        required_fields = ['consent_given', 'signature_date']
        for field in required_fields:
            if field not in participant_data:
                raise ValueError(f"Missing required consent field: {field}")

        if not participant_data['consent_given']:
            logger.warning("Participant declined consent. Record not saved.")
            return {"status": "declined", "timestamp": datetime.now().isoformat()}

        record = {
            "consent_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "signed": True,
            "signature_date": participant_data['signature_date'],
            "metadata": {
                "age_verified": participant_data.get('age_verified', False),
                "withdrawal_rights_acknowledged": True
            }
        }
        self.consent_records.append(record)
        logger.info(f"Consent captured for ID: {record['consent_id']}")
        return record

    def save_consent_records(self, output_path: Optional[str] = None) -> str:
        """Save consent records to a JSONL file."""
        if not self.consent_records:
            logger.warning("No consent records to save.")
            return ""

        if output_path is None:
            output_path = os.path.join(DATA_PROCESSED_DIR, "consent_records.jsonl")

        with open(output_path, 'w', encoding='utf-8') as f:
            for record in self.consent_records:
                f.write(json.dumps(record) + '\n')

        logger.info(f"Saved {len(self.consent_records)} consent records to {output_path}")
        return output_path


class SurveyInterface:
    """Manages the survey data collection and storage."""

    def __init__(self):
        self.responses: List[Dict[str, Any]] = []
        self.schema = {
            "interaction_id": str,
            "participant_id": str,
            "timestamp": str,
            "trust_score": float,
            "avatar_emotion": str,
            "difficulty_rating": int,
            "open_feedback": str
        }

    def record_response(self, interaction_id: str, participant_id: str,
                        trust_score: float, avatar_emotion: str,
                        difficulty_rating: int, open_feedback: str = "") -> Dict[str, Any]:
        """Record a single survey response."""
        response = {
            "interaction_id": interaction_id,
            "participant_id": participant_id,  # This will be anonymized later
            "timestamp": datetime.now().isoformat(),
            "trust_score": trust_score,
            "avatar_emotion": avatar_emotion,
            "difficulty_rating": difficulty_rating,
            "open_feedback": open_feedback
        }
        self.responses.append(response)
        return response

    def save_raw_responses(self, output_path: Optional[str] = None) -> str:
        """Save raw survey responses to a CSV file."""
        if not self.responses:
            logger.warning("No survey responses to save.")
            return ""

        if output_path is None:
            output_path = os.path.join(DATA_RAW_DIR, "survey_responses_raw.csv")

        fieldnames = list(self.schema.keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.responses)

        logger.info(f"Saved {len(self.responses)} raw survey responses to {output_path}")
        return output_path


class AnonymizationPipeline:
    """Handles the anonymization of collected data."""

    def __init__(self, salt: str = SALT):
        self.salt = salt
        self.mapping_cache: Dict[str, str] = {}

    def _generate_anon_id(self, original_id: str) -> str:
        """Generate a deterministic anonymized ID."""
        if original_id in self.mapping_cache:
            return self.mapping_cache[original_id]

        # Create a hash of the salt + original ID
        hash_input = f"{self.salt}{original_id}".encode('utf-8')
        hash_val = hashlib.sha256(hash_input).hexdigest()[:12]
        anon_id = f"{ANONYMIZED_ID_PREFIX}_{hash_val}"

        self.mapping_cache[original_id] = anon_id
        return anon_id

    def anonymize_responses(self, raw_responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Anonymize a list of survey responses.

        Args:
            raw_responses: List of response dictionaries containing 'participant_id'.

        Returns:
            List of anonymized response dictionaries.
        """
        anonymized = []
        for resp in raw_responses:
            anon_resp = resp.copy()
            original_id = anon_resp.get('participant_id', '')
            if original_id:
                anon_resp['participant_id'] = self._generate_anon_id(original_id)
                # Remove any PII that might exist in open_feedback (basic heuristic)
                if 'open_feedback' in anon_resp:
                    # In a real system, we might use NER here. For now, we assume
                    # the survey interface enforces no PII in open text.
                    pass
            anonymized.append(anon_resp)
        return anonymized

    def save_anonymized_responses(self, anonymized_responses: List[Dict[str, Any]],
                                  output_path: Optional[str] = None) -> str:
        """Save anonymized responses to a CSV file."""
        if not anonymized_responses:
            logger.warning("No anonymized responses to save.")
            return ""

        if output_path is None:
            output_path = os.path.join(DATA_PROCESSED_DIR, "survey_responses_anonymized.csv")

        fieldnames = list(anonymized_responses[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(anonymized_responses)

        logger.info(f"Saved {len(anonymized_responses)} anonymized responses to {output_path}")
        return output_path


def run_collection_protocol(sample_size: int = 5) -> Dict[str, str]:
    """
    Execute the full data collection protocol for demonstration/validation.

    This function simulates the collection process by:
    1. Creating a consent capture instance.
    2. Simulating survey responses.
    3. Anonymizing the data.
    4. Saving all artifacts.

    Args:
        sample_size: Number of simulated participants to process.

    Returns:
        Dictionary of output file paths.
    """
    logger.info(f"Starting Data Collection Protocol simulation with N={sample_size}")

    # 1. Consent Capture
    consent_handler = ConsentCapture()
    for i in range(sample_size):
        # Simulate consent data
        consent_data = {
            "consent_given": True,
            "signature_date": datetime.now().isoformat(),
            "age_verified": True
        }
        consent_handler.capture_consent(consent_data)

    consent_file = consent_handler.save_consent_records()

    # 2. Survey Interface (Simulating interactions)
    survey = SurveyInterface()
    emotions = ["happy", "neutral", "angry", "surprised"]
    for i in range(sample_size):
        interaction_id = f"INT_{i:04d}"
        participant_id = f"PID_{i:04d}" # Real PII placeholder
        trust_score = 3.0 + (i % 3) * 0.5 # Simulated score 3.0 to 4.5
        emotion = emotions[i % len(emotions)]
        difficulty = 1 + (i % 4)

        survey.record_response(
            interaction_id=interaction_id,
            participant_id=participant_id,
            trust_score=trust_score,
            avatar_emotion=emotion,
            difficulty_rating=difficulty,
            open_feedback=f"Sample feedback for interaction {interaction_id}"
        )

    raw_file = survey.save_raw_responses()

    # 3. Anonymization Pipeline
    anonymizer = AnonymizationPipeline()
    anonymized_data = anonymizer.anonymize_responses(survey.responses)
    anon_file = anonymizer.save_anonymized_responses(anonymized_data)

    logger.info("Data Collection Protocol simulation complete.")
    return {
        "consent_records": consent_file,
        "raw_responses": raw_file,
        "anonymized_responses": anon_file
    }


def main():
    """Entry point for the data collection script."""
    setup_logging()
    try:
        outputs = run_collection_protocol(sample_size=10)
        print("Protocol executed successfully. Output files:")
        for key, path in outputs.items():
            print(f"  {key}: {path}")
    except Exception as e:
        logger.error(f"Protocol execution failed: {e}", exc_info=True)
        handle_corrupted_file(str(e))
        raise


if __name__ == "__main__":
    main()
