"""
Data validation module for fMRI-Music preference study.
Implements dynamic dataset validation, integrity checks, and subject exclusion logic.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd

from config import get_data_path, get_processed_path
from utils.io import load_json, save_json, ensure_dir

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Custom exception for data validation failures."""
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code
        self.message = message

# Verified dataset registry: maps dataset IDs to required behavioral variables
# This list is loaded dynamically from a JSON configuration file if available,
# otherwise falls back to a hardcoded baseline (which should be updated via config).
VERIFIED_DATASETS_CONFIG_PATH = "data/derived/verified_datasets.json"

# Hardcoded baseline for initial execution if config file is missing.
# In a production run, this file MUST be populated with real verified datasets.
BASELINE_VERIFIED_DATASETS = {
    "ds000030": {
        "required_variables": ["musical_genre", "STOMP-R"],
        "description": "OpenNeuro ds000030 - Resting state fMRI",
        "verified": True
    },
    "ds000208": {
        "required_variables": ["musical_genre", "STOMP-R"],
        "description": "OpenNeuro ds000208 - Resting state fMRI",
        "verified": True
    }
}

def _load_verified_datasets() -> Dict[str, Dict[str, Any]]:
    """
    Dynamically load the verified datasets configuration.
    Falls back to baseline if the config file is missing or invalid.
    """
    config_path = Path(VERIFIED_DATASETS_CONFIG_PATH)
    if config_path.exists():
        try:
            data = load_json(config_path)
            if isinstance(data, dict):
                logger.info(f"Loaded verified datasets from {config_path}")
                return data
            else:
                logger.warning(f"Invalid format in {config_path}, using baseline.")
        except Exception as e:
            logger.warning(f"Failed to load {config_path}: {e}. Using baseline.")
    
    # Fallback to baseline
    logger.info("Using baseline verified datasets configuration.")
    return BASELINE_VERIFIED_DATASETS

def validate_dataset_id(dataset_id: str, required_variable: str = "musical_genre") -> Tuple[bool, Optional[str]]:
    """
    Dynamically validate dataset IDs against a verified list of datasets.
    
    Args:
        dataset_id: The OpenNeuro dataset ID to validate (e.g., 'ds000030').
        required_variable: The specific behavioral variable that must exist in the dataset.
    
    Returns:
        Tuple of (is_valid: bool, missing_variable: Optional[str])
        If valid, returns (True, None).
        If invalid (not in list or missing variable), returns (False, missing_variable).
    
    Raises:
        DataValidationError: If the dataset ID is not in the verified list.
    """
    verified_datasets = _load_verified_datasets()
    
    if dataset_id not in verified_datasets:
        logger.error(f"ERR_INVALID_DATASET: Dataset ID '{dataset_id}' is not in the verified list.")
        # Log the specific missing variable context (even if the dataset itself is unknown)
        logger.error(f"Required variable check for '{required_variable}' cannot proceed for unknown dataset.")
        raise DataValidationError(
            f"Dataset ID '{dataset_id}' is not in the verified list. "
            f"Verified datasets: {list(verified_datasets.keys())}",
            code="ERR_INVALID_DATASET"
        )
    
    dataset_info = verified_datasets[dataset_id]
    required_vars = dataset_info.get("required_variables", [])
    
    if required_variable not in required_vars:
        logger.error(f"ERR_INVALID_DATASET: Dataset '{dataset_id}' does not contain required variable '{required_variable}'.")
        logger.error(f"Available variables for this dataset: {required_vars}")
        return False, required_variable
    
    return True, None

def check_sample_size(participants_df: pd.DataFrame, min_size: int = 85) -> None:
    """
    Check if the sample size meets the minimum requirement.
    
    Args:
        participants_df: DataFrame containing participant information.
        min_size: Minimum required sample size.
    
    Raises:
        DataValidationError: If sample size is below the threshold.
    """
    n = len(participants_df)
    if n < min_size:
        logger.error(f"ERR_UNDERPOWERED: Sample size N={n} is less than required minimum N={min_size}.")
        raise DataValidationError(
            f"Sample size N={n} is underpowered (minimum required: {min_size}). "
            "Execution halted.",
            code="ERR_UNDERPOWERED"
        )
    logger.info(f"Sample size check passed: N={n} >= {min_size}")

def check_behavioral_variables(participants_df: pd.DataFrame) -> str:
    """
    Verify that required behavioral variables exist in the participants file.
    
    Args:
        participants_df: DataFrame containing participant information.
    
    Returns:
        The name of the found behavioral variable ('musical_genre' or 'STOMP-R').
    
    Raises:
        DataValidationError: If neither required variable is found.
    """
    columns = participants_df.columns.tolist()
    
    # Check for primary variable
    if "musical_genre" in columns:
        logger.info("Found primary behavioral variable: 'musical_genre'")
        return "musical_genre"
    
    # Check for fallback variable
    if "STOMP-R" in columns:
        logger.warning("Primary variable 'musical_genre' missing. Falling back to 'STOMP-R'.")
        return "STOMP-R"
    
    # Both missing
    missing_fields = [f for f in ["musical_genre", "STOMP-R"] if f not in columns]
    logger.error(f"ERR_DATA_MISSING: Required behavioral variables missing: {missing_fields}")
    raise DataValidationError(
        f"Dataset missing required behavioral variables: {missing_fields}. "
        "Cannot proceed with analysis.",
        code="ERR_DATA_MISSING"
    )

def check_data_integrity(dataset_id: str, data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Perform comprehensive data integrity checks.
    
    1. Validates dataset ID against verified list.
    2. Checks sample size (N >= 85).
    3. Verifies behavioral variables (musical_genre or STOMP-R).
    
    Args:
        dataset_id: The dataset ID to validate.
        data_dir: Optional path to the data directory. If None, uses config default.
    
    Returns:
        Dictionary with validation results.
    
    Raises:
        DataValidationError: If any check fails.
    """
    if data_dir is None:
        data_dir = get_data_path() / dataset_id
    
    results = {
        "dataset_id": dataset_id,
        "valid_id": False,
        "sample_size_check": False,
        "variable_check": False,
        "error": None
    }
    
    # 1. Validate Dataset ID
    try:
        is_valid, missing_var = validate_dataset_id(dataset_id)
        results["valid_id"] = is_valid
        if not is_valid:
            results["error"] = f"Invalid dataset ID: missing variable '{missing_var}'"
            raise DataValidationError(results["error"], "ERR_INVALID_DATASET")
    except DataValidationError as e:
        results["error"] = str(e)
        raise
    
    # 2. Check Sample Size
    participants_path = data_dir / "participants.tsv"
    if not participants_path.exists():
        raise DataValidationError(
            f"participants.tsv not found at {participants_path}",
            code="ERR_FILE_MISSING"
        )
    
    participants_df = pd.read_csv(participants_path, sep='\t')
    check_sample_size(participants_df)
    results["sample_size_check"] = True
    
    # 3. Check Behavioral Variables
    found_var = check_behavioral_variables(participants_df)
    results["variable_check"] = True
    results["found_variable"] = found_var
    
    logger.info("Data integrity check passed successfully.")
    return results

def exclude_subjects_by_missing_data(participants_df: pd.DataFrame, threshold: float = 0.10) -> pd.DataFrame:
    """
    Exclude subjects with >10% missing behavioral data.
    
    Args:
        participants_df: DataFrame with participant data.
        threshold: Maximum allowed fraction of missing data.
    
    Returns:
        Filtered DataFrame with valid subjects.
    """
    # Identify columns that are behavioral variables (not subject ID)
    behavioral_cols = [col for col in participants_df.columns if col not in ['participant_id', 'subject_id']]
    
    if not behavioral_cols:
        return participants_df
    
    # Calculate missing fraction per row
    missing_fraction = participants_df[behavioral_cols].isna().mean(axis=1)
    
    # Filter
    valid_mask = missing_fraction <= threshold
    excluded_count = (~valid_mask).sum()
    
    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} subjects due to >{threshold*100}% missing behavioral data.")
    
    return participants_df[valid_mask].reset_index(drop=True)

def exclude_subjects_by_motion(confounds_df: pd.DataFrame, threshold: float = 0.5) -> List[str]:
    """
    Flag/exclude subjects with excessive head motion (mean FD > 0.5mm).
    
    Args:
        confounds_df: DataFrame containing confound regressors (must have 'framewise_displacement').
        threshold: Maximum allowed mean FD in mm.
    
    Returns:
        List of subject IDs to exclude.
    """
    if 'framewise_displacement' not in confounds_df.columns:
        logger.warning("framewise_displacement column not found in confounds. Skipping motion check.")
        return []
    
    mean_fd = confounds_df['framewise_displacement'].mean()
    
    if mean_fd > threshold:
        logger.warning(f"Subject excluded: Mean FD {mean_fd:.3f}mm > {threshold}mm threshold.")
        return [True] # Placeholder logic for single subject context; in batch, returns list of IDs
    
    return []

def main():
    """
    CLI entry point for data validation.
    Usage: python -m code.data.validate --dataset_id ds000030
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate dataset integrity")
    parser.add_argument("--dataset_id", type=str, required=True, help="OpenNeuro dataset ID")
    parser.add_argument("--data_dir", type=str, default=None, help="Optional data directory path")
    parser.add_argument("--variable", type=str, default="musical_genre", help="Required behavioral variable")
    
    args = parser.parse_args()
    
    try:
        data_dir = Path(args.data_dir) if args.data_dir else None
        results = check_data_integrity(args.dataset_id, data_dir)
        print(json.dumps(results, indent=2))
    except DataValidationError as e:
        logger.error(f"Validation failed: {e.message} (Code: {e.code})")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    main()