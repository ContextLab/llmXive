"""
Data Validation Module.
Verifies presence of NIfTI and behavioral logs.
"""
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from utils.io import IOLoadError, ensure_dir, file_exists, load_json
from utils.config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)

def validate_dataset_structure(dataset_root: str) -> Tuple[bool, List[str]]:
    """
    Validates the overall structure of the OpenNeuro dataset.
    
    Args:
        dataset_root: Path to the root of the dataset.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    root_path = Path(dataset_root)
    
    # Check for dataset_description.json
    desc_file = root_path / "dataset_description.json"
    if not file_exists(str(desc_file)):
        errors.append(f"Missing dataset_description.json at {desc_file}")
    
    # Check for required BIDS structure elements (simplified)
    # In a full implementation, we would check for specific sub-*/ses-*/func patterns
    
    return len(errors) == 0, errors

def validate_participant_data(dataset_root: str, participant_id: str, session_id: str) -> Tuple[bool, List[str]]:
    """
    Validates data availability for a specific participant and session.
    
    Args:
        dataset_root: Path to the dataset root.
        participant_id: Participant ID (e.g., 'sub-01').
        session_id: Session ID (e.g., 'ses-01').
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    base_path = Path(dataset_root) / participant_id / session_id
    
    # Check for functional NIfTI
    func_file = base_path / "func" / f"{participant_id}_{session_id}_task-social_bold.nii.gz"
    if not file_exists(str(func_file)):
        errors.append(f"Missing functional image: {func_file}")
    
    # Check for behavioral logs (various possible names)
    beh_files = [
        base_path / "beh" / f"{participant_id}_{session_id}_task-social_beh.tsv",
        base_path / "beh" / "behavioral.json",
        base_path / "behavioral.json"
    ]
    beh_found = False
    for beh_file in beh_files:
        if file_exists(str(beh_file)):
            beh_found = True
            break
    
    if not beh_found:
        errors.append(f"Missing behavioral log for {participant_id}/{session_id}")
        
    # Check for motion parameters (if available)
    # This is often in the same directory as func or in a specific motion file
    # For this implementation, we assume it's part of the functional file metadata or a separate file
    # If strict motion file is required, add check here.
    
    return len(errors) == 0, errors

def main():
    """
    Main entry point for data validation.
    """
    config = get_config()
    dataset_root = config.get("paths", {}).get("raw_data", "data/raw")
    
    is_valid, errors = validate_dataset_structure(dataset_root)
    if not is_valid:
        logger.error("Dataset structure validation failed:")
        for err in errors:
            logger.error(f"  - {err}")
    else:
        logger.info("Dataset structure validation passed.")

if __name__ == "__main__":
    main()