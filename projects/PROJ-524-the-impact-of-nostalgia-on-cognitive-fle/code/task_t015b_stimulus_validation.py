"""
T015b: Stimulus Validation
Validates the presence of a validation_study_doi in data/raw/metadata.json.
Logs INFO_STIMULUS_VALIDATED if found and not null, else WARN_STIMULUS_NO_VALIDATION.
"""
import os
import json
import logging
from pathlib import Path

from utils import setup_logging, log_info, log_warning, log_error, get_timestamp


def load_metadata(metadata_path: Path) -> dict:
    """Load metadata from the specified JSON file."""
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_stimulus_doi(metadata: dict) -> bool:
    """
    Check if 'validation_study_doi' exists and is not null.
    Returns True if valid, False otherwise.
    """
    doi = metadata.get('validation_study_doi')
    return doi is not None


def main():
    """Main entry point for T015b."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    metadata_path = project_root / "data" / "raw" / "metadata.json"
    
    try:
        logger.info(f"Loading metadata from {metadata_path}")
        metadata = load_metadata(metadata_path)
        
        # Validate DOI presence
        is_validated = validate_stimulus_doi(metadata)
        
        if is_validated:
            log_info(logger, "INFO_STIMULUS_VALIDATED", "validation_study_doi found and is not null.")
            logger.info(f"DOI found: {metadata.get('validation_study_doi')}")
        else:
            log_warning(logger, "WARN_STIMULUS_NO_VALIDATION", "validation_study_doi is missing or null.")
            
    except FileNotFoundError as e:
        log_error(logger, "ERR_METADATA_MISSING", str(e))
        raise
    except json.JSONDecodeError as e:
        log_error(logger, "ERR_METADATA_INVALID", f"Invalid JSON in metadata file: {e}")
        raise
    except Exception as e:
        log_error(logger, "ERR_UNKNOWN", f"Unexpected error during stimulus validation: {e}")
        raise


if __name__ == "__main__":
    main()