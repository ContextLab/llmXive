"""
Data Validation Module.
Verifies presence of NIfTI and behavioral logs (private_belief, social_feedback, choice).
"""
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from utils.io import IOLoadError, ensure_dir, file_exists, load_json, load_csv
from utils.config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)

REQUIRED_BEHAVIORAL_COLUMNS = {"private_belief", "social_feedback", "choice"}

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
    
    # Check for BIDS root structure
    if not file_exists(str(root_path / "sub-01")):
        # We don't fail immediately if no sub-01, but log warning if we expect data
        logger.warning("No sub-01 directory found. Dataset may be empty or not yet downloaded.")
    
    return len(errors) == 0, errors

def validate_participant_data(dataset_root: str, participant_id: str, session_id: str) -> Tuple[bool, List[str]]:
    """
    Validates data availability for a specific participant and session.
    Specifically checks for NIfTI and behavioral logs with required columns.
    
    Args:
        dataset_root: Path to the dataset root.
        participant_id: Participant ID (e.g., 'sub-01').
        session_id: Session ID (e.g., 'ses-01').
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    base_path = Path(dataset_root) / participant_id / session_id
    
    # 1. Check for functional NIfTI
    func_file = base_path / "func" / f"{participant_id}_{session_id}_task-social_bold.nii.gz"
    if not file_exists(str(func_file)):
        errors.append(f"Missing functional image: {func_file}")
    
    # 2. Check for behavioral logs and validate columns
    # Look for TSV files which are standard for behavioral data in BIDS
    beh_dir = base_path / "beh"
    beh_files = []
    if beh_dir.exists():
        beh_files = list(beh_dir.glob(f"{participant_id}_{session_id}_task-social_beh.tsv"))
    
    # Fallback to common names if specific pattern not found
    if not beh_files:
        fallback_names = [
            base_path / "beh" / f"{participant_id}_{session_id}_task-social_beh.tsv",
            base_path / "beh" / "behavioral.tsv",
            base_path / "behavioral.tsv",
            base_path / "beh" / f"{participant_id}_{session_id}_task-social_beh.json", # Check json just in case
            base_path / "behavioral.json"
        ]
        for p in fallback_names:
            if file_exists(str(p)):
                beh_files.append(p)
                break
    
    if not beh_files:
        errors.append(f"Missing behavioral log file for {participant_id}/{session_id}")
    else:
        # Validate the content of the found behavioral file
        beh_file = beh_files[0]
        try:
            # Attempt to load as CSV/TSV to check columns
            # load_csv handles TSV automatically if extension is .tsv or if delimiter detection is on
            # Assuming load_csv in utils.io handles TSVs
            df = load_csv(str(beh_file))
            
            if df is None or df.empty:
                errors.append(f"Behavioral file {beh_file} is empty or could not be loaded.")
            else:
                # Check for required columns
                df_columns = set(df.columns)
                missing_cols = REQUIRED_BEHAVIORAL_COLUMNS - df_columns
                if missing_cols:
                    errors.append(
                        f"Behavioral file {beh_file} missing required columns: {sorted(missing_cols)}. "
                        f"Found columns: {sorted(df_columns)}"
                    )
                else:
                    logger.debug(f"Behavioral file {beh_file} validated successfully with required columns.")
                    
        except Exception as e:
            errors.append(f"Failed to parse behavioral file {beh_file}: {str(e)}")
    
    # 3. Check for motion parameters (if available as separate file)
    # Often named *_bold.nii.gz or *_events.tsv, but strictly for motion:
    motion_file = base_path / "func" / f"{participant_id}_{session_id}_task-social_desc-motions.tsv"
    # If not found, we might not fail hard unless motion is strictly required for this step.
    # The task description implies verifying presence of logs, not necessarily motion files yet,
    # but T018 handles motion QC. We just log a warning if missing.
    if not file_exists(str(motion_file)):
        # Not a hard error for this specific task, but noted
        logger.debug(f"Motion parameters file not found at {motion_file}, skipping validation.")
    
    return len(errors) == 0, errors

def main():
    """
    Main entry point for data validation.
    Iterates through participants in the raw data directory and validates them.
    """
    config = get_config()
    dataset_root = config.get("paths", {}).get("raw_data", "data/raw")
    
    is_valid, errors = validate_dataset_structure(dataset_root)
    if not is_valid:
        logger.error("Dataset structure validation failed:")
        for err in errors:
            logger.error(f"  - {err}")
        # Don't exit early, try to validate participants if structure is partially there
    
    # Attempt to find participants
    root_path = Path(dataset_root)
    participants = [d.name for d in root_path.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    
    if not participants:
        logger.warning("No participants found in raw data directory.")
        return
    
    logger.info(f"Found {len(participants)} participants to validate.")
    
    total_valid = 0
    total_invalid = 0
    
    for pid in participants:
        # Assume single session for now, or find sessions
        ses_path = root_path / pid
        sessions = [d.name for d in ses_path.iterdir() if d.is_dir() and d.name.startswith("ses-")]
        
        if not sessions:
            # Maybe no session folder, check directly in sub
            sessions = [""] # Treat root of sub as session
        
        for sid in sessions:
            valid, p_errors = validate_participant_data(dataset_root, pid, sid)
            if valid:
                total_valid += 1
                logger.info(f"Participant {pid} (Session {sid if sid else 'N/A'}): VALID")
            else:
                total_invalid += 1
                logger.error(f"Participant {pid} (Session {sid if sid else 'N/A'}): INVALID")
                for err in p_errors:
                    logger.error(f"  - {err}")
    
    logger.info(f"Validation complete. Valid: {total_valid}, Invalid: {total_invalid}")
    if total_invalid > 0:
        logger.warning("Some participants failed validation. Check logs for details.")

if __name__ == "__main__":
    main()
