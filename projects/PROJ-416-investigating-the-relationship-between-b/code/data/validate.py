import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from code.config import Config
from code.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def validate_metadata(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the presence of required metadata fields.

    Args:
        metadata: Dictionary containing subject metadata.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    required_fields = ["pre_treatment_score", "post_treatment_score"]
    
    for field in required_fields:
        if field not in metadata:
            errors.append(f"Missing required field: {field}")
    
    # Check for validated anxiety scale
    instrument = metadata.get("instrument", "")
    valid_instruments = ["GAD-7", "HAM-A", "LSAS"]
    if instrument not in valid_instruments:
        errors.append(f"Invalid or unvalidated instrument: {instrument}. Must be one of {valid_instruments}")
    
    return len(errors) == 0, errors


def validate_subject_metadata_path(
    subject_id: str,
    metadata_dir: Path
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validate metadata for a specific subject.

    Args:
        subject_id: Subject identifier.
        metadata_dir: Path to metadata directory.

    Returns:
        Tuple of (is_valid, metadata_dict or None).
    """
    metadata_path = metadata_dir / f"{subject_id}_metadata.json"
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found for {subject_id}")
        return False, None
    
    try:
        import json
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        is_valid, errors = validate_metadata(metadata)
        if not is_valid:
            logger.error(f"Validation failed for {subject_id}: {errors}")
            return False, None
        
        return True, metadata
    except Exception as e:
        logger.error(f"Error reading metadata for {subject_id}: {e}")
        return False, None


def run_validation(
    metadata_dir: Path,
    subject_ids: List[str]
) -> Dict[str, bool]:
    """
    Run validation for all subjects.

    Args:
        metadata_dir: Path to metadata directory.
        subject_ids: List of subject IDs.

    Returns:
        Dictionary mapping subject_id to validation status.
    """
    results = {}
    for sub_id in subject_ids:
        is_valid, _ = validate_subject_metadata_path(sub_id, metadata_dir)
        results[sub_id] = is_valid
    return results


def main():
    """Main entry point for the validation script."""
    setup_logging()
    config = Config()
    
    metadata_dir = Path(config.metadata_dir)
    # Placeholder subject list
    subject_ids = [f"sub-{i:03d}" for i in range(1, 11)]
    
    run_validation(metadata_dir, subject_ids)


if __name__ == "__main__":
    main()
