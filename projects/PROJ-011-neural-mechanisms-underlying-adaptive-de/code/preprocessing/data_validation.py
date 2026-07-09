"""
Data Validation Module for Neural Mechanisms Study.

This module verifies the presence of required NIfTI files and behavioral logs
(private_belief, social_feedback, choice) for participants in the OpenNeuro ds003694 dataset.
It enforces the data contract defined in the project specifications.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from utils.io import IOLoadError, ensure_dir, file_exists, load_json
from utils.config import get_config
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Required file patterns per participant
# Expected structure in data/raw/ds003694/sub-<label>/func/
# and data/raw/ds003694/sub-<label>/beh/
REQUIRED_NIFTI_PATTERNS = [
    "sub-{participant_id}_task-socialfeedback_run-*.nii.gz",
    "sub-{participant_id}_task-privatebelief_run-*.nii.gz",
]

REQUIRED_BEHAV_LOGS = [
    "sub-{participant_id}_task-socialfeedback_beh.json",
    "sub-{participant_id}_task-privatebelief_beh.json",
    "sub-{participant_id}_events.tsv", # Standard BIDS events file for choices/timing
]

# Specific behavioral log names mentioned in task description
# These map to expected content files if not strictly BIDS
BEHAVIORAL_LOG_NAMES = {
    "private_belief": ["sub-{participant_id}_task-privatebelief_beh.json", "sub-{participant_id}_task-privatebelief_events.tsv"],
    "social_feedback": ["sub-{participant_id}_task-socialfeedback_beh.json", "sub-{participant_id}_task-socialfeedback_events.tsv"],
    "choice": ["sub-{participant_id}_events.tsv"],
}


def validate_participant_data(
    data_dir: Path,
    participant_id: str,
    strict: bool = True
) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validates the presence of required NIfTI and behavioral files for a single participant.

    Args:
        data_dir: Path to the root data directory (e.g., data/raw/ds003694).
        participant_id: The participant label (e.g., 'sub-01').
        strict: If True, missing any required file causes failure. If False, returns a report.

    Returns:
        Tuple of (is_valid, missing_files_dict) where missing_files_dict maps
        file categories to lists of missing file paths.
    """
    missing_files = {
        "nifti": [],
        "behavioral_logs": [],
        "choice_data": []
    }

    # Construct participant path
    sub_dir = data_dir / participant_id
    if not sub_dir.exists():
        logger.warning(f"Participant directory not found: {sub_dir}")
        missing_files["nifti"].append(f"{participant_id}/ (directory missing)")
        missing_files["behavioral_logs"].append(f"{participant_id}/ (directory missing)")
        return (False, missing_files)

    func_dir = sub_dir / "func"
    beh_dir = sub_dir / "beh"

    # Check NIfTI files
    # We look for at least one matching pattern per task
    found_nifti_tasks = set()
    for pattern in REQUIRED_NIFTI_PATTERNS:
        # Handle wildcard manually if glob isn't used, but pathlib glob is robust
        search_pattern = pattern.format(participant_id=participant_id)
        # If the pattern contains wildcards, use glob
        if '*' in search_pattern:
            matches = list(func_dir.glob(search_pattern)) if func_dir.exists() else []
        else:
            matches = [func_dir / search_pattern] if func_dir.exists() and (func_dir / search_pattern).exists() else []

        if matches:
            task_name = "socialfeedback" if "socialfeedback" in search_pattern else "privatebelief"
            found_nifti_tasks.add(task_name)
        else:
            missing_files["nifti"].append(f"func/{search_pattern}")

    # Check Behavioral Logs
    # We need to verify specific logs exist
    required_logs = [
        "sub-{participant_id}_task-socialfeedback_beh.json",
        "sub-{participant_id}_task-privatebelief_beh.json",
    ]
    
    # Check for events.tsv (standard for choice data in BIDS)
    events_file = sub_dir / "beh" / f"sub-{participant_id}_events.tsv"
    if not events_file.exists():
        # Fallback to func dir if BIDS structure varies
        events_file = func_dir / f"sub-{participant_id}_task-socialfeedback_events.tsv"
    
    if not events_file.exists():
         missing_files["choice_data"].append("events.tsv (choice data)")

    for log_pattern in required_logs:
        search_path = log_pattern.format(participant_id=participant_id)
        # Check in beh dir first, then func dir
        target = beh_dir / search_path if beh_dir else func_dir / search_path
        
        if target.exists():
            pass
        else:
            # Try alternate locations
            found = False
            for d in [beh_dir, func_dir, sub_dir]:
                if d and (d / search_path).exists():
                    found = True
                    break
            if not found:
                missing_files["behavioral_logs"].append(search_path)

    is_valid = strict and (len(missing_files["nifti"]) == 0 and len(missing_files["behavioral_logs"]) == 0 and len(missing_files["choice_data"]) == 0)
    
    if not is_valid:
        logger.warning(f"Validation failed for {participant_id}: {missing_files}")
    
    return is_valid, missing_files


def validate_dataset_structure(data_dir: Path) -> Dict[str, any]:
    """
    Scans the dataset directory for all participants and validates their data.
    
    Args:
        data_dir: Path to the root dataset directory.
        
    Returns:
        Dictionary containing validation summary.
    """
    config = get_config()
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    # Find all participant directories (sub-*)
    participants = [d.name for d in data_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    
    if not participants:
        logger.warning(f"No participant directories found in {data_dir}")
        return {
            "total_participants": 0,
            "valid_participants": 0,
            "invalid_participants": [],
            "details": {}
        }

    valid_count = 0
    invalid_details = []

    for pid in sorted(participants):
        is_valid, missing = validate_participant_data(data_dir, pid)
        
        status = "valid" if is_valid else "invalid"
        logger.info(f"Participant {pid}: {status}")
        
        if is_valid:
            valid_count += 1
        else:
            invalid_details.append({
                "participant_id": pid,
                "missing_files": missing
            })

    return {
        "total_participants": len(participants),
        "valid_participants": valid_count,
        "invalid_participants": invalid_details,
        "validation_rate": valid_count / len(participants) if participants else 0.0
    }


def main():
    """
    Entry point for data validation.
    Loads configuration, scans the dataset, and reports results.
    """
    config = get_config()
    data_root = Path(config.get("data_dir", "data/raw"))
    dataset_name = config.get("dataset_name", "ds003694")
    dataset_path = data_root / dataset_name

    logger.info(f"Starting data validation for dataset: {dataset_path}")
    
    try:
        results = validate_dataset_structure(dataset_path)
        
        # Log summary
        logger.info(f"Validation Complete. Valid: {results['valid_participants']}/{results['total_participants']}")
        
        if results['invalid_participants']:
            logger.warning("The following participants failed validation:")
            for inv in results['invalid_participants']:
                logger.warning(f"  - {inv['participant_id']}: {inv['missing_files']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Validation process failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
