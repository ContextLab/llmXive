"""
T015b: STIMULUS VALIDATION

Validates the stimulus metadata by checking for the presence of a
'validation_study_doi' in data/raw/metadata.json.

Logic:
1. Load data/raw/metadata.json.
2. Check if 'validation_study_doi' exists and is not None/null.
3. If valid DOI present: Log INFO_STIMULUS_VALIDATED.
4. If missing or null: Log WARN_STIMULUS_NO_VALIDATION.
5. Write validation status to data/results/stimulus_validation_status.json.
"""

import os
import json
import logging
from pathlib import Path

from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Configure logging for this module
logger = logging.getLogger(__name__)

# Paths relative to project root
METADATA_PATH = Path("data/raw/metadata.json")
RESULTS_DIR = Path("data/results")
VALIDATION_STATUS_PATH = RESULTS_DIR / "stimulus_validation_status.json"

def load_metadata() -> dict:
    """
    Loads the metadata file from data/raw/metadata.json.
    Raises FileNotFoundError if the file does not exist.
    """
    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Metadata file not found at {METADATA_PATH}. "
            "Ensure T015a has been executed successfully."
        )
    
    with open(META_DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_stimulus_doi(metadata: dict) -> bool:
    """
    Checks if 'validation_study_doi' exists in metadata and is not null.
    
    Returns:
        bool: True if DOI is present and valid, False otherwise.
    """
    doi = metadata.get('validation_study_doi')
    return doi is not None and doi != ""

def main():
    """
    Main entry point for T015b.
    """
    setup_logging()
    timestamp = get_timestamp()
    
    logger.info(f"Starting T015b: Stimulus Validation at {timestamp}")
    
    try:
        # 1. Load Metadata
        metadata = load_metadata()
        logger.info(f"Loaded metadata from {METADATA_PATH}")
        
        # 2. Validate DOI
        is_validated = validate_stimulus_doi(metadata)
        
        # 3. Log Result
        if is_validated:
            doi = metadata.get('validation_study_doi')
            log_info(f"INFO_STIMULUS_VALIDATED: Validation study DOI found ({doi})")
        else:
            log_warning("WARN_STIMULUS_NO_VALIDATION: No validation_study_doi found or it is null")
        
        # 4. Save Validation Status
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        
        status_report = {
            "task_id": "T015b",
            "timestamp": timestamp,
            "metadata_source": str(METADATA_PATH),
            "stimulus_validated": is_validated,
            "doi_found": metadata.get('validation_study_doi'),
            "log_message": "INFO_STIMULUS_VALIDATED" if is_validated else "WARN_STIMULUS_NO_VALIDATION"
        }
        
        with open(VALIDATION_STATUS_PATH, 'w', encoding='utf-8') as f:
            json.dump(status_report, f, indent=2)
        
        logger.info(f"Validation status saved to {VALIDATION_STATUS_PATH}")
        
    except FileNotFoundError as e:
        log_error(f"File not found: {e}")
        raise
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in metadata file: {e}")
        raise
    except Exception as e:
        log_error(f"Unexpected error during stimulus validation: {e}")
        raise

if __name__ == "__main__":
    main()
