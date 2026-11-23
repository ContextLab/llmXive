import os
import json
import logging
from pathlib import Path
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

def load_metadata(metadata_path: str) -> dict:
    """Load metadata from the specified JSON file."""
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_path, 'r') as f:
        return json.load(f)

def validate_stimulus_doi(metadata: dict) -> bool:
    """
    Validate stimulus DOI from metadata.
    
    Returns True if DOI exists and is not null, False otherwise.
    Logs appropriate messages based on validation result.
    """
    doi = metadata.get('validation_study_doi')
    
    if doi is not None and doi != "":
        log_info("INFO_STIMULUS_VALIDATED", f"Stimulus validated via DOI: {doi}")
        return True
    else:
        log_warning("WARN_STIMULUS_NO_VALIDATION", "No validation DOI found in metadata")
        return False

def main():
    """Main entry point for T015b stimulus validation task."""
    # Setup logging
    log_path = Path("data/results/runtime_log.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_path)
    
    log_info("T015B_START", f"Starting stimulus validation task at {get_timestamp()}")
    
    try:
        # Load metadata
        metadata_path = "data/raw/metadata.json"
        log_info("T015B_LOAD_METADATA", f"Loading metadata from {metadata_path}")
        
        metadata = load_metadata(metadata_path)
        
        # Validate stimulus DOI
        log_info("T015B_VALIDATE_DOI", "Checking validation_study_doi in metadata")
        is_validated = validate_stimulus_doi(metadata)
        
        # Log result
        if is_validated:
            log_info("T015B_RESULT", "Stimulus validation PASSED")
        else:
            log_warning("T015B_RESULT", "Stimulus validation WARNING - no DOI provided")
        
        log_info("T015B_COMPLETE", f"Stimulus validation task completed at {get_timestamp()}")
        
    except FileNotFoundError as e:
        log_error("T015B_ERROR", f"File not found: {e}")
        raise
    except json.JSONDecodeError as e:
        log_error("T015B_ERROR", f"Invalid JSON in metadata file: {e}")
        raise
    except Exception as e:
        log_error("T015B_ERROR", f"Unexpected error during stimulus validation: {e}")
        raise

if __name__ == "__main__":
    main()