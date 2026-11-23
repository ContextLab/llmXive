import logging
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from code.config import Config

logger = logging.getLogger(__name__)
config = Config()

class FatalError(Exception):
    """Exception raised for fatal errors that halt the pipeline."""
    pass

def validate_metadata(dataset_type: str, required_variables: List[str]) -> Dict[str, Any]:
    """
    Validate dataset metadata for required variables.
    
    Args:
        dataset_type: Type of dataset (e.g., 'openneuro')
        required_variables: List of variable names that must be present
        
    Returns:
        Dict with validation results
        
    Raises:
        FatalError: If required variables are missing
    """
    verified_path = Path(config.VERIFIED_SOURCES_PATH)
    
    if not verified_path.exists():
        error_msg = "Verified sources file not found. Run T001a first."
        logger.error(error_msg)
        raise FatalError(error_msg)
    
    with open(verified_path, 'r') as f:
        metadata = json.load(f)
    
    # Check for required variables in metadata
    missing_vars = []
    for var in required_variables:
        # Check if variable exists in metadata or its sub-fields
        found = False
        if var in metadata:
            found = True
        elif isinstance(metadata.get('variables'), dict) and var in metadata['variables']:
            found = True
        elif isinstance(metadata.get('data_dictionary'), dict) and var in metadata['data_dictionary']:
            found = True
        
        if not found:
            missing_vars.append(var)
    
    if missing_vars:
        error_msg = f"Missing required variable: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise FatalError(error_msg)
    
    logger.info(f"Validation passed for {dataset_type} dataset")
    return {"status": "valid", "missing_variables": []}

def validate_subject_metadata_path(subject_id: str, expected_path: Path) -> bool:
    """Validate that a subject's metadata file exists at the expected path."""
    if not expected_path.exists():
        logger.warning(f"Subject metadata not found: {expected_path}")
        return False
    return True

def run_validation() -> None:
    """Main validation entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate dataset metadata")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset type")
    parser.add_argument("--check-variables", type=str, required=True, 
                      help="Comma-separated list of required variables")
    
    args = parser.parse_args()
    
    variables = [v.strip() for v in args.check_variables.split(",")]
    
    try:
        result = validate_metadata(args.dataset, variables)
        logger.info(f"Validation result: {result}")
    except FatalError as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    run_validation()