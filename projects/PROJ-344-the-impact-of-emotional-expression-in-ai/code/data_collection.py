"""
Controlled Data Collection Protocol Module.

Implements the survey interface, consent capture, and anonymization pipeline
for the study on emotional expression in AI avatars.
"""
import os
import json
import csv
import hashlib
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Import project logging
from logging_config import get_logger

# Ensure output directories exist
DATA_DIR = Path("data/raw")
ANONYMIZED_DIR = Path("data/processed")
DATA_DIR.mkdir(parents=True, exist_ok=True)
ANONYMIZED_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)


class ConsentCapture:
    """
    Handles the capture, storage, and verification of participant consent.
    """

    def __init__(self, consent_template_path: str = "code/consent_form_template.md"):
        self.template_path = consent_template_path
        self.consent_records: List[Dict[str, Any]] = []
        self.logger = get_logger(self.__class__.__name__)

        if not os.path.exists(consent_template_path):
            raise FileNotFoundError(f"Consent template not found at {consent_template_path}")

    def capture_consent(self, participant_id: str, signature_data: Dict[str, Any]) -> bool:
        """
        Capture and validate consent for a specific participant.

        Args:
            participant_id: Unique ID for the participant.
            signature_data: Dict containing 'signature_type', 'timestamp', 'ip_address' (if applicable).

        Returns:
            bool: True if consent is successfully captured and logged.
        """
        timestamp = datetime.now().isoformat()
        
        record = {
            "participant_id": participant_id,
            "consent_version": "1.0", # Version of the template used
            "timestamp": timestamp,
            "signature_data": signature_data,
            "status": "active"
        }

        # Log the event
        self.logger.info(f"Consent captured for participant: {participant_id}")
        self.consent_records.append(record)
        return True

    def verify_consent(self, participant_id: str) -> bool:
        """
        Verify if a participant has active consent.

        Args:
            participant_id: The ID to check.

        Returns:
            bool: True if consent exists and is active.
        """
        for record in self.consent_records:
            if record["participant_id"] == participant_id and record["status"] == "active":
                return True
        return False

    def export_consent_log(self, output_path: Optional[str] = None) -> str:
        """
        Export consent logs to a secure JSON file.
        """
        if not output_path:
            output_path = str(DATA_DIR / "consent_log.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.consent_records, f, indent=2, default=str)
        
        self.logger.info(f"Consent log exported to {output_path}")
        return output_path


class SurveyInterface:
    """
    Manages the presentation of survey questions and collection of responses.
    This class simulates the interface logic that would be used in a web or CLI application.
    """

    def __init__(self):
        self.questions = self._load_survey_template()
        self.responses: List[Dict[str, Any]] = []
        self.logger = get_logger(self.__class__.__name__)

    def _load_survey_template(self) -> List[Dict[str, Any]]:
        """
        Loads the standard survey questions for the study.
        Returns a list of question dictionaries.
        """
        return [
            {
                "id": "Q1",
                "text": "How trustworthy did you find the AI avatar during the interaction?",
                "type": "scale",
                "scale_range": (1, 7),
                "scale_labels": {"1": "Not Trustworthy", "7": "Very Trustworthy"}
            },
            {
                "id": "Q2",
                "text": "How natural did the emotional expressions appear?",
                "type": "scale",
                "scale_range": (1, 7),
                "scale_labels": {"1": "Very Artificial", "7": "Very Natural"}
            },
            {
                "id": "Q3",
                "text": "How comfortable did you feel interacting with the avatar?",
                "type": "scale",
                "scale_range": (1, 7),
                "scale_labels": {"1": "Very Uncomfortable", "7": "Very Comfortable"}
            },
            {
                "id": "Q4",
                "text": "Which emotion did you perceive the avatar to be expressing?",
                "type": "multiple_choice",
                "options": ["Happy", "Sad", "Angry", "Neutral", "Surprised", "Fearful"]
            }
        ]

    def get_questions(self) -> List[Dict[str, Any]]:
        """Returns the list of survey questions."""
        return self.questions

    def collect_response(self, participant_id: str, interaction_id: str, answers: Dict[str, Any]) -> bool:
        """
        Collects a set of responses for a specific interaction.

        Args:
            participant_id: Unique ID of the participant.
            interaction_id: Unique ID of the interaction/session.
            answers: Dict mapping question ID to the answer.

        Returns:
            bool: True if response was successfully recorded.
        """
        # Validate answers against questions
        for q in self.questions:
            if q["id"] not in answers:
                self.logger.warning(f"Missing answer for question {q['id']}")
        
        response_record = {
            "participant_id": participant_id,
            "interaction_id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "answers": answers
        }

        self.responses.append(response_record)
        self.logger.info(f"Response collected for interaction {interaction_id}")
        return True

    def export_responses(self, output_path: Optional[str] = None) -> str:
        """
        Exports collected survey responses to a CSV file.
        """
        if not output_path:
            output_path = str(DATA_DIR / "survey_responses_raw.csv")

        if not self.responses:
            self.logger.warning("No responses to export.")
            return output_path

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header
            header = ["participant_id", "interaction_id", "timestamp"] + [q["id"] for q in self.questions]
            writer.writerow(header)

            for resp in self.responses:
                row = [
                    resp["participant_id"],
                    resp["interaction_id"],
                    resp["timestamp"]
                ]
                for q in self.questions:
                    row.append(resp["answers"].get(q["id"], ""))
                writer.writerow(row)

        self.logger.info(f"Survey responses exported to {output_path}")
        return output_path


class AnonymizationPipeline:
    """
    Handles the anonymization of collected data (PII removal, hashing IDs).
    """

    def __init__(self, salt: str = "project_salt_v1"):
        self.salt = salt
        self.mapping_store: Dict[str, str] = {} # Maps real IDs to anonymized IDs
        self.logger = get_logger(self.__class__.__name__)

    def _hash_id(self, original_id: str) -> str:
        """
        Creates a deterministic hash for an ID using a salt.
        """
        salted_string = f"{self.salt}:{original_id}"
        return hashlib.sha256(salted_string.encode('utf-8')).hexdigest()[:16]

    def anonymize_participant_id(self, original_id: str) -> str:
        """
        Returns an anonymized ID for a participant.
        """
        if original_id not in self.mapping_store:
            self.mapping_store[original_id] = self._hash_id(original_id)
        return self.mapping_store[original_id]

    def process_survey_responses(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Reads raw survey responses, anonymizes participant IDs, and saves to new file.
        """
        if not output_path:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_anonymized{ext}"

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                original_pid = row.get("participant_id", "")
                if original_pid:
                    row["participant_id"] = self.anonymize_participant_id(original_pid)
                writer.writerow(row)

        self.logger.info(f"Anonymized survey data saved to {output_path}")
        return output_path

    def process_media_metadata(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Processes metadata associated with media files to remove PII.
        """
        if not output_path:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_anonymized{ext}"
        
        # Assuming JSON input for metadata
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            for item in data:
                if "participant_id" in item:
                    item["participant_id"] = self.anonymize_participant_id(item["participant_id"])
        elif isinstance(data, dict):
            if "participant_id" in data:
                data["participant_id"] = self.anonymize_participant_id(data["participant_id"])

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Anonymized media metadata saved to {output_path}")
        return output_path


def run_collection_protocol(
    consent_template_path: str,
    survey_questions: List[Dict[str, Any]],
    raw_data_path: str
) -> Dict[str, str]:
    """
    Orchestrates the full data collection protocol:
    1. Initialize Consent Capture.
    2. Initialize Survey Interface.
    3. Initialize Anonymization Pipeline.
    4. Process raw data (simulated here by loading and cleaning).
    5. Export results.

    This function is designed to be called by the main entry point or an external orchestrator.
    """
    logger.info("Starting Controlled Data Collection Protocol.")

    # 1. Consent
    consent = ConsentCapture(consent_template_path)
    # Simulate capturing consent for a test participant
    consent.capture_consent("TEST_001", {"type": "digital", "timestamp": datetime.now().isoformat()})
    consent_path = consent.export_consent_log()

    # 2. Survey
    survey = SurveyInterface()
    # Simulate collecting a response
    survey.collect_response(
        "TEST_001", 
        "INT_001", 
        {"Q1": 6, "Q2": 5, "Q3": 6, "Q4": "Happy"}
    )
    survey_raw_path = survey.export_responses()

    # 3. Anonymization
    anon = AnonymizationPipeline()
    survey_anon_path = anon.process_survey_responses(survey_raw_path)

    logger.info("Protocol execution complete.")
    return {
        "consent_log": consent_path,
        "survey_raw": survey_raw_path,
        "survey_anonymized": survey_anon_path
    }


def main():
    """
    Main entry point for running the data collection protocol locally.
    """
    logger.info("Running data_collection.py main entry point.")
    
    try:
        results = run_collection_protocol(
            consent_template_path="code/consent_form_template.md",
            survey_questions=[], # Loaded internally by SurveyInterface
            raw_data_path="data/raw" # Placeholder for future raw media paths
        )
        
        print("Data Collection Protocol Completed Successfully.")
        print(f"Artifacts generated:")
        for key, path in results.items():
            print(f"  - {key}: {path}")
            
    except Exception as e:
        logger.error(f"Protocol failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
