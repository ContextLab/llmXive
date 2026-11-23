"""
Consent Verification Script (T009).

Verifies the existence and validity of consent provenance metadata
at data/consent/provenance.json.

Required keys:
  - irb_number
  - expiration_date
  - consent_form_version
  - participant_count_limit

Exit codes:
  0: Valid provenance file exists with all required keys.
  1: File missing or missing required keys (template generated).
  2: File exists but contains invalid keys (schema mismatch).
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Local imports based on project API surface
from config import get_consent_dir
from logging_config import setup_logging, get_logger

# Define required keys
REQUIRED_KEYS = [
    "irb_number",
    "expiration_date",
    "consent_form_version",
    "participant_count_limit"
]

def get_provenance_path() -> Path:
    """Return the path to the provenance.json file."""
    consent_dir = get_consent_dir()
    return consent_dir / "provenance.json"

def generate_template(path: Path) -> None:
    """Generate a template provenance.json file with placeholder values."""
    template = {
        "irb_number": "IRB-2023-XXXX (Replace with actual number)",
        "expiration_date": "YYYY-MM-DD (Replace with expiration date)",
        "consent_form_version": "v1.0.0 (Replace with actual version)",
        "participant_count_limit": 100,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "notes": "This is a template. Please update with actual IRB details before data collection."
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2)

    logger = get_logger()
    logger.warning(f"Template generated at: {path}")
    logger.warning("Please update the file with valid IRB details.")

def verify_consent() -> int:
    """
    Verify the consent provenance file.

    Returns:
        0: Success (valid file)
        1: Missing file or missing keys (template generated)
        2: Invalid keys (schema mismatch)
    """
    path = get_provenance_path()
    logger = get_logger()

    logger.info(f"Checking consent provenance at: {path}")

    if not path.exists():
        logger.warning("Provenance file not found.")
        generate_template(path)
        return 1

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in provenance file: {e}")
        return 2

    # Check for required keys
    missing_keys = [key for key in REQUIRED_KEYS if key not in data]

    if missing_keys:
        logger.warning(f"Missing required keys: {missing_keys}")
        generate_template(path)
        return 1

    # Check for invalid keys (optional strict check: warn if extra keys exist,
    # but for this task we focus on existence of required keys.
    # If we want to be strict about 'invalid keys' meaning keys that break the schema,
    # we assume any key not in REQUIRED_KEYS + metadata fields is invalid.
    # However, the task says "exit with warning" if missing, and exit 2 if "invalid keys".
    # Let's interpret "invalid keys" as: the file structure is wrong or contains non-string/number
    # where expected, or we simply check if the keys are present and valid types.
    # To be safe and compliant with the prompt "exit 2 if invalid keys",
    # we will check if the values for required keys are of expected types.

    errors = []

    if not isinstance(data.get("irb_number"), str) or not data["irb_number"]:
        errors.append("irb_number must be a non-empty string")

    if not isinstance(data.get("expiration_date"), str):
        errors.append("expiration_date must be a string")
    else:
        # Basic date format check YYYY-MM-DD
        try:
            datetime.strptime(data["expiration_date"], "%Y-%m-%d")
        except ValueError:
            errors.append("expiration_date must be in YYYY-MM-DD format")

    if not isinstance(data.get("consent_form_version"), str):
        errors.append("consent_form_version must be a string")

    if not isinstance(data.get("participant_count_limit"), int):
        errors.append("participant_count_limit must be an integer")

    if errors:
        for err in errors:
            logger.error(f"Validation error: {err}")
        return 2

    logger.info("Consent provenance verified successfully.")
    return 0

def main() -> None:
    """Entry point for the script."""
    setup_logging()
    exit_code = verify_consent()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()