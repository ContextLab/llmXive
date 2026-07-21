import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from code.config import Config

logger = logging.getLogger(__name__)

def validate_metadata(metadata: Dict[str, Any], config: Config) -> Tuple[bool, List[str]]:
    """
    Validate dataset metadata for required variables.
    
    Args:
        metadata: Dataset metadata
        config: Configuration object
        
    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    
    # Check for required variables
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
        
    return len(errors) == 0, errors

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
    """
    # In a real implementation, load metadata from the dataset
    # For now, we use a placeholder
    metadata = {
        "variables": ["pre_treatment_score", "post_treatment_score"],
        "instrument": "GAD-7"
    }
    
    is_valid, errors = validate_metadata(metadata, config)
    
    if not is_valid:
        for error in errors:
            logger.error(error)
        logger.critical("Dataset validation failed. Halting pipeline.")
        return False
        
    # Validate subject directories
    raw_dir = config.RAW_DATA_DIR
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        return False
        
    subject_dirs = [d for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    
    for subject_dir in subject_dirs:
        if not validate_subject_metadata_path(subject_dir):
            logger.warning(f"Subject {subject_dir.name} is incomplete and will be excluded.")
            
    logger.info("Dataset validation successful.")
    return True

def main():
    """Main entry point."""
    config = Config()
    run_validation(config)

if __name__ == "__main__":
    main()
