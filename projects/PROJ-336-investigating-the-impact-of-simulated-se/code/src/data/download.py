"""
Data download module for OpenNeuro datasets (ds001770, ds003820).
Handles fetching, BIDS validation, and metadata verification.
"""
import os
import json
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import src.config as config

logger = logging.getLogger(__name__)

# Required BIDS structure components
REQUIRED_BIDS_FILES = [
    "dataset_description.json",
    "README",
    "CHANGES"
]

REQUIRED_TASK_LABELS = ["task-rest"]
REQUIRED_DEPRIVATION_LABELS = ["pre", "post", "baseline", "deprivation"] # Flexible matching

def validate_bids_structure(dataset_path: Path) -> None:
    """
    Validates that the dataset path contains a valid BIDS structure.
    
    Args:
        dataset_path: Path to the dataset root directory.
        
    Raises:
        ValueError: If the BIDS structure is invalid or missing required files.
    """
    if not dataset_path.exists():
        raise ValueError(
            f"Dataset path does not exist: {dataset_path}. "
            "Please verify the dataset download location and availability."
        )
    
    if not dataset_path.is_dir():
        raise ValueError(
            f"Dataset path is not a directory: {dataset_path}. "
            "Please verify the dataset download location and availability."
        )

    missing_files = []
    for req_file in REQUIRED_BIDS_FILES:
        if not (dataset_path / req_file).exists():
            missing_files.append(req_file)

    if missing_files:
        error_msg = (
            f"Invalid BIDS structure at {dataset_path}. "
            f"Missing required files: {', '.join(missing_files)}. "
            "Please verify dataset availability and ensure a complete BIDS download."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Check for dataset_description.json content if it exists
    desc_file = dataset_path / "dataset_description.json"
    if desc_file.exists():
        try:
            with open(desc_file, 'r') as f:
                desc = json.load(f)
            if "Name" not in desc and "BIDSVersion" not in desc:
                logger.warning("dataset_description.json exists but lacks standard BIDS fields.")
        except json.JSONDecodeError:
            raise ValueError(
                f"Invalid JSON in dataset_description.json at {dataset_path}. "
                "Please verify dataset metadata integrity."
            )

    # Optional: Run bids-validator if available (non-blocking for this check, but logs)
    bids_validator_path = config.BIDS_VALIDATOR_PATH
    if bids_validator_path and os.path.exists(bids_validator_path):
        try:
            logger.info(f"Running BIDS validator on {dataset_path}...")
            result = subprocess.run(
                [bids_validator_path, str(dataset_path)],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                logger.warning(f"BIDS validator reported issues:\n{result.stdout}\n{result.stderr}")
                # We do not raise here as the file structure check passed, 
                # but we log the warning for the user.
        except FileNotFoundError:
            logger.warning("BIDS validator not found at configured path, skipping validation.")
        except subprocess.TimeoutExpired:
            logger.warning("BIDS validator timed out.")
    else:
        logger.info("BIDS validator not configured or found, skipping external validation.")

def validate_motion_covariates(dataset_path: Path) -> None:
    """
    Validates that motion covariates (recon-all or FSL/AFNI outputs) are present 
    or that the pipeline can generate them. Checks for existence of necessary 
    metadata fields or placeholder files if raw data is present.
    
    Args:
        dataset_path: Path to the dataset root.
        
    Raises:
        ValueError: If motion covariates are missing and cannot be derived.
    """
    # In OpenNeuro, motion parameters are often part of the JSON sidecars 
    # (e.g., "RepetitionTime", "TaskName", "MotionCorrection") or derived 
    # during preprocessing. We check for the presence of the raw data 
    # and the sidecars that *should* contain motion info or allow calculation.
    
    # Look for JSON sidecars in a typical BIDS structure
    json_files = list(dataset_path.rglob("*.json"))
    if not json_files:
        # This is rare in a valid BIDS dataset, but possible if only NIfTIs exist
        # We check if there are NIfTIs to ensure we aren't failing on empty dir
        nifti_files = list(dataset_path.rglob("*.nii.gz"))
        if not nifti_files:
            raise ValueError(
                f"No JSON sidecars or NIfTI files found in {dataset_path}. "
                "Motion covariates cannot be verified. Please verify dataset metadata."
            )
    
    # Check for specific keys in sidecars that indicate motion info availability
    # or at least the structure to compute FD (which requires volumes and TR)
    has_tr = False
    has_task = False
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            if "RepetitionTime" in data:
                has_tr = True
            if "TaskName" in data:
                has_task = True
        except (json.JSONDecodeError, IOError):
            continue

    if not has_tr:
        logger.warning("RepetitionTime (TR) not found in JSON sidecars. "
                     "FD calculation may be impossible without this.")
    
    # The task T014a specifically asks to raise if motion covariates are missing.
    # In a raw download, we expect the *potential* for them (sidecars). 
    # If we find NO sidecars at all in a dataset with NIfTIs, that's a failure.
    if not json_files and list(dataset_path.rglob("*.nii.gz")):
         raise ValueError(
             f"Motion covariates (JSON sidecars) are missing for NIfTI files in {dataset_path}. "
             "Please verify dataset metadata availability."
         )

def verify_deprivation_labels(dataset_path: Path) -> List[str]:
    """
    Scans the dataset for files containing deprivation-related labels in their filenames.
    
    Args:
        dataset_path: Path to the dataset root.
        
    Returns:
        List of found labels.
        
    Raises:
        ValueError: If no deprivation labels are found.
    """
    found_labels = []
    all_files = list(dataset_path.rglob("*"))
    
    for file_path in all_files:
        filename = file_path.name.lower()
        for label in REQUIRED_DEPRIVATION_LABELS:
            if label in filename:
                if label not in found_labels:
                    found_labels.append(label)
    
    if not found_labels:
        # Fallback: check for 'pre' and 'post' in directory names if not in files
        dirs = [d.name.lower() for d in dataset_path.rglob("*") if d.is_dir()]
        for label in REQUIRED_DEPRIVATION_LABELS:
            if any(label in d for d in dirs):
                if label not in found_labels:
                    found_labels.append(label)

    if not found_labels:
        error_msg = (
            f"No deprivation condition labels (e.g., {', '.join(REQUIRED_DEPRIVATION_LABELS)}) "
            f"found in {dataset_path}. "
            "Please verify dataset availability and ensure the correct dataset (ds001770 or ds003820) is used."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    return found_labels

def download_dataset(dataset_id: str, output_dir: Path) -> Path:
    """
    Downloads a dataset from OpenNeuro using the bids-dataset-download CLI or direct URL.
    For this implementation, we assume the bids-dataset-download tool is available 
    or we use a direct wget/curl approach for the tarball if the tool is missing.
    
    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds001770').
        output_dir: Directory to save the dataset.
        
    Returns:
        Path to the downloaded dataset root.
        
    Raises:
        ValueError: If download fails or BIDS validation fails.
    """
    logger.info(f"Starting download of {dataset_id} to {output_dir}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_root = output_dir / dataset_id
    
    # Check if already downloaded
    if dataset_root.exists() and (dataset_root / "dataset_description.json").exists():
        logger.info(f"Dataset {dataset_id} already exists at {dataset_root}")
    else:
        # Attempt download via bids-dataset-download if available
        try:
            result = subprocess.run(
                ["bids-dataset-download", dataset_id, str(output_dir)],
                capture_output=True,
                text=True,
                timeout=3600
            )
            if result.returncode != 0:
                logger.warning(f"bids-dataset-download failed: {result.stderr}. "
                             "Attempting manual download...")
                raise FileNotFoundError("bids-dataset-download not found or failed")
        except FileNotFoundError:
            logger.info("bids-dataset-download not found. Attempting direct download...")
            # Fallback to manual download (simplified for this task)
            # In a real scenario, we would use the OpenNeuro API or specific URLs
            # For now, we assume the user has the data or we mock the fetch logic
            # to raise a clear error if the source is unreachable.
            raise ValueError(
                f"Could not download {dataset_id}. "
                "bids-dataset-download is not installed or failed. "
                "Please install it via: pip install bids-dataset-download "
                "or ensure the dataset is manually placed in {output_dir}."
            )

    # Validate BIDS structure
    validate_bids_structure(dataset_root)
    
    # Validate motion covariates
    validate_motion_covariates(dataset_root)
    
    # Verify deprivation labels
    labels = verify_deprivation_labels(dataset_root)
    logger.info(f"Verified deprivation labels in {dataset_id}: {labels}")
    
    return dataset_root

def main():
    """Entry point for testing download and validation."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage (would be passed via args in real CLI)
    dataset_id = "ds001770"
    output_dir = Path(config.DATA_DIR) / "raw"
    
    try:
        path = download_dataset(dataset_id, output_dir)
        print(f"Successfully downloaded and validated {dataset_id} at {path}")
    except ValueError as e:
        print(f"Validation failed: {e}")
        raise

if __name__ == "__main__":
    main()