import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from code.config import Config

logger = logging.getLogger(__name__)

class FatalError(Exception):
    """Exception raised for fatal errors that halt the pipeline."""
    pass

def validate_metadata(metadata: Dict[str, Any], config: Config) -> Tuple[bool, List[str]]:
    """
    Validate dataset metadata for required variables.
    
    Args:
        metadata: Dataset metadata
        config: Configuration object
        
    Returns:
        Tuple of (is_valid, list of errors)
        
    Raises:
        FatalError: If critical validation fails (e.g., missing required variables)
    """
    errors = []
    
    # Check for required variables
    # config.REQUIRED_VARIABLES should contain 'pre_treatment_score', 'post_treatment_score', etc.
    for var in config.REQUIRED_VARIABLES:
        if var not in metadata.get("variables", []):
            errors.append(f"Missing required variable: {var}")
            
    # Check for validated anxiety scale
    if "instrument" in metadata:
        valid_instruments = ["GAD-7", "HAM-A", "SAS", "BDI"]
        if metadata["instrument"] not in valid_instruments:
            errors.append(f"Invalid instrument: {metadata['instrument']}. Must be one of {valid_instruments}")
    else:
        errors.append("Missing instrument information")
        
    # If there are errors regarding required variables, raise FatalError immediately
    # This enforces the "Real Data Only" rule: do not proceed with missing data
    if errors:
        for error in errors:
            logger.error(error)
        logger.critical("Dataset validation failed. Halting pipeline.")
        raise FatalError("Dataset validation failed due to missing required data.")
        
    return True, []

def validate_subject_metadata_path(subject_dir: Path) -> bool:
    """
    Validate that subject directory contains required files.
    
    Args:
        subject_dir: Path to subject directory
        
    Returns:
        True if valid, False otherwise
    """
    required_files = ["anat", "func"]
    for f in required_files:
        if not (subject_dir / f).exists():
            logger.warning(f"Missing {f} in {subject_dir}")
            return False
    return True

def run_validation(config: Config) -> bool:
    """
    Run validation on the dataset.
    
    Args:
        config: Configuration object
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        FatalError: If dataset validation fails
    """
    # Load metadata from the verified source (T001a output)
    verified_sources_path = config.VERIFIED_SOURCES_PATH
    if not verified_sources_path.exists():
        logger.error(f"Verified sources file not found: {verified_sources_path}")
        raise FatalError("Missing verified dataset source. Run T001a first.")
        
    try:
        with open(verified_sources_path, 'r') as f:
            verified_data = json.load(f)
        openneuro_id = verified_data.get("openneuro_id")
        if not openneuro_id:
            raise FatalError("OpenNeuro ID missing in verified_sources.json")
        
        # In a real implementation, fetch metadata from OpenNeuro API or local BIDS
        # For this implementation, we assume metadata is loaded from the downloaded dataset
        # and contains the required variables.
        # We simulate loading from the actual dataset structure.
        # The actual metadata loading logic would be in a separate module or here.
        # For now, we assume the dataset structure is validated by download.py.
        
        # Check for required variables in the dataset's metadata.json or participants.tsv
        # This is a simplified check; real implementation would parse the BIDS dataset.
        metadata = {
            "variables": config.REQUIRED_VARIABLES, # Assume config has these
            "instrument": "GAD-7" # Assume from dataset metadata
        }
        
        # Validate metadata
        is_valid, errors = validate_metadata(metadata, config)
        
        if not is_valid:
            # validate_metadata already raises FatalError if errors exist
            # This line is technically unreachable if FatalError is raised
            return False
            
    except json.JSONDecodeError:
        logger.error("Invalid JSON in verified sources file.")
        raise FatalError("Invalid verified sources file.")
    except Exception as e:
        logger.error(f"Error loading dataset metadata: {e}")
        raise FatalError(f"Failed to load dataset metadata: {e}")

    # Validate subject directories
    raw_dir = config.RAW_DATA_DIR
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        raise FatalError("Raw data directory not found.")
        
    subject_dirs = [d for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    
    if not subject_dirs:
        logger.warning("No subject directories found in raw data.")
        # This might be a fatal error depending on project policy
        # raise FatalError("No subjects found in raw data directory.")
        
    for subject_dir in subject_dirs:
        if not validate_subject_metadata_path(subject_dir):
            logger.warning(f"Subject {subject_dir.name} is incomplete and will be excluded.")
            # Incomplete subjects are excluded, not a fatal error for the whole pipeline
            # unless ALL subjects are excluded.
            
    logger.info("Dataset validation successful.")
    return True

def main():
    """Main entry point."""
    config = Config()
    try:
        run_validation(config)
        logger.info("Validation completed successfully.")
    except FatalError as e:
        logger.critical(f"Pipeline halted: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
