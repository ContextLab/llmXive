"""
Informed Consent Flow Implementation with IRB Approval Verification.

This module handles the collection, verification, and logging of informed consent
from participants before they begin the experiment. It verifies that the IRB
approval ID matches the configuration and logs the consent event.
"""
import os
import sys
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Import from existing project modules
from config.settings import load_irb_config, get_env_var
from logs.experiment import log_consent, setup_experiment_logger

# Constants
CONSENT_REQUIRED_VERSION = "1.0"
CONSENT_FILE_NAME = "consent_record.json"
CONSENT_LOG_NAME = "consent_log.jsonl"

class ConsentError(Exception):
    """Custom exception for consent flow errors."""
    pass

class IRBVerificationError(ConsentError):
    """Raised when IRB approval verification fails."""
    pass

class ConsentExpiredError(ConsentError):
    """Raised when consent is expired or invalid."""
    pass

def get_irb_approval_id() -> str:
    """
    Retrieve the expected IRB approval ID from configuration.

    Returns:
        str: The configured IRB approval ID.

    Raises:
        ConsentError: If IRB configuration is missing or invalid.
    """
    try:
        config = load_irb_config()
        irb_id = config.get("approval_id")
        if not irb_id:
            raise ConsentError("IRB approval ID not found in configuration.")
        return irb_id
    except Exception as e:
        raise ConsentError(f"Failed to load IRB configuration: {e}")

def verify_irb_approval(provided_irb_id: str) -> Tuple[bool, str]:
    """
    Verify that the provided IRB approval ID matches the configured one.

    Args:
        provided_irb_id: The IRB ID provided by the participant or system.

    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    expected_id = get_irb_approval_id()
    if provided_irb_id == expected_id:
        return True, "IRB approval verified successfully."
    else:
        return False, f"IRB approval ID mismatch. Expected: {expected_id}, Got: {provided_irb_id}"

def generate_consent_hash(participant_id: str, irb_id: str, timestamp: datetime) -> str:
    """
    Generate a unique hash for the consent record to ensure integrity.

    Args:
        participant_id: Unique identifier for the participant.
        irb_id: The IRB approval ID.
        timestamp: The timestamp of consent.

    Returns:
        str: SHA-256 hash of the consent data.
    """
    data = f"{participant_id}:{irb_id}:{timestamp.isoformat()}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def collect_consent(
    participant_id: str,
    irb_approval_id: str,
    version: str = CONSENT_REQUIRED_VERSION,
    additional_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Collect and validate informed consent from a participant.

    This function:
    1. Verifies the IRB approval ID.
    2. Records the consent with a timestamp.
    3. Generates a consent hash for integrity.
    4. Logs the consent event.

    Args:
        participant_id: Unique identifier for the participant.
        irb_approval_id: The IRB approval ID provided by the participant.
        version: The version of the consent form.
        additional_data: Optional additional data to include in the record.

    Returns:
        Dict[str, Any]: The complete consent record.

    Raises:
        IRBVerificationError: If IRB approval verification fails.
        ConsentError: If consent collection fails.
    """
    # Verify IRB approval
    is_valid, message = verify_irb_approval(irb_approval_id)
    if not is_valid:
        raise IRBVerificationError(message)

    # Record timestamp in UTC
    timestamp = datetime.now(timezone.utc)

    # Generate consent hash
    consent_hash = generate_consent_hash(participant_id, irb_approval_id, timestamp)

    # Build consent record
    consent_record = {
        "participant_id": participant_id,
        "irb_approval_id": irb_approval_id,
        "consent_version": version,
        "timestamp_utc": timestamp.isoformat(),
        "consent_hash": consent_hash,
        "status": "consented",
        "additional_data": additional_data or {}
    }

    # Log the consent event
    logger = setup_experiment_logger()
    log_consent(logger, participant_id, irb_approval_id, timestamp, consent_hash)

    return consent_record

def save_consent_record(
    consent_record: Dict[str, Any],
    output_dir: Optional[str] = None
) -> Path:
    """
    Save the consent record to a file.

    Args:
        consent_record: The consent record to save.
        output_dir: Directory to save the record. Defaults to data/consent/.

    Returns:
        Path: Path to the saved file.
    """
    if output_dir is None:
        output_dir = "data/consent"

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    participant_id = consent_record["participant_id"]
    timestamp = consent_record["timestamp_utc"].replace(":", "-").replace(".", "-")
    filename = f"consent_{participant_id}_{timestamp}.json"
    file_path = output_path / filename

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(consent_record, f, indent=2)

    return file_path

def load_consent_record(participant_id: str, consent_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load a consent record for a specific participant.

    Args:
        participant_id: The participant ID to search for.
        consent_dir: Directory containing consent records.

    Returns:
        Optional[Dict[str, Any]]: The consent record if found, None otherwise.
    """
    if consent_dir is None:
        consent_dir = "data/consent"

    consent_path = Path(consent_dir)
    if not consent_path.exists():
        return None

    for file_path in consent_path.glob(f"consent_{participant_id}_*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                record = json.load(f)
                if record.get("participant_id") == participant_id:
                    return record
        except (json.JSONDecodeError, IOError):
            continue

    return None

def is_participant_consented(participant_id: str, consent_dir: Optional[str] = None) -> bool:
    """
    Check if a participant has provided valid consent.

    Args:
        participant_id: The participant ID to check.
        consent_dir: Directory containing consent records.

    Returns:
        bool: True if consented, False otherwise.
    """
    record = load_consent_record(participant_id, consent_dir)
    if record is None:
        return False

    return record.get("status") == "consented"

def main():
    """
    Main entry point for testing the consent flow.
    This function demonstrates the consent collection and verification process.
    """
    # Example usage
    print("Starting Informed Consent Flow Test...")

    # Simulate participant data
    test_participant_id = "P001_TEST"
    test_irb_id = get_irb_approval_id()  # Use configured ID for testing

    try:
        # Collect consent
        consent_record = collect_consent(
            participant_id=test_participant_id,
            irb_approval_id=test_irb_id,
            version=CONSENT_REQUIRED_VERSION,
            additional_data={"test_mode": True}
        )

        print(f"Consent collected successfully for {test_participant_id}")
        print(f"Consent Hash: {consent_record['consent_hash']}")

        # Save record
        saved_path = save_consent_record(consent_record)
        print(f"Consent record saved to: {saved_path}")

        # Verify loading
        loaded_record = load_consent_record(test_participant_id)
        if loaded_record:
            print("Consent record loaded successfully.")
            print(f"Status: {loaded_record['status']}")
        else:
            print("Failed to load consent record.")

        # Check consent status
        if is_participant_consented(test_participant_id):
            print("Participant is consented.")
        else:
            print("Participant is NOT consented.")

    except IRBVerificationError as e:
        print(f"IRB Verification Failed: {e}")
        sys.exit(1)
    except ConsentError as e:
        print(f"Consent Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}")
        sys.exit(1)

    print("Informed Consent Flow Test Complete.")

if __name__ == "__main__":
    main()