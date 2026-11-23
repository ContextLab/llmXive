"""
Utility functions for file I/O operations, BIDS loading, dataset versioning, and checksum verification.
Implements Constitution III requirements for data integrity and versioning.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from utils.logger import get_logger

logger = get_logger("io_utils")

# Constants for BIDS and dataset validation
BIDS_REQUIRED_FILES = ["dataset_description.json", "participants.tsv"]
CHECKSUM_ALGORITHM = "sha256"

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def load_csv(path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame."""
    path = Path(path)
    if not path.exists():
        logger.log("file_not_found", path=str(path), operation="load_csv")
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path, **kwargs)

def save_csv(df: pd.DataFrame, path: Union[str, Path], **kwargs) -> None:
    """Save a pandas DataFrame to a CSV file."""
    path = Path(path)
    ensure_dir(path.parent)
    df.to_csv(path, index=False, **kwargs)
    logger.log("file_saved", path=str(path), operation="save_csv")

def load_json(path: Union[str, Path], **kwargs) -> Any:
    """Load a JSON file."""
    path = Path(path)
    if not path.exists():
        logger.log("file_not_found", path=str(path), operation="load_json")
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f, **kwargs)

def save_json(data: Any, path: Union[str, Path], **kwargs) -> None:
    """Save data to a JSON file."""
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str, **kwargs)
    logger.log("file_saved", path=str(path), operation="save_json")

def load_pickle(path: Union[str, Path]) -> Any:
    """Load a pickle file."""
    path = Path(path)
    if not path.exists():
        logger.log("file_not_found", path=str(path), operation="load_pickle")
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'rb') as f:
        return pickle.load(f)

def save_pickle(data: Any, path: Union[str, Path]) -> None:
    """Save data to a pickle file."""
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, 'wb') as f:
        pickle.dump(data, f)
    logger.log("file_saved", path=str(path), operation="save_pickle")

def save_text(text: str, path: Union[str, Path], encoding: str = 'utf-8') -> None:
    """Save text to a file."""
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, 'w', encoding=encoding) as f:
        f.write(text)
    logger.log("file_saved", path=str(path), operation="save_text")

def load_numpy(path: Union[str, Path]) -> np.ndarray:
    """Load a NumPy .npy file."""
    path = Path(path)
    if not path.exists():
        logger.log("file_not_found", path=str(path), operation="load_numpy")
        raise FileNotFoundError(f"File not found: {path}")
    return np.load(path)

def save_numpy(arr: np.ndarray, path: Union[str, Path]) -> None:
    """Save a NumPy array to a .npy file."""
    path = Path(path)
    ensure_dir(path.parent)
    np.save(path, arr)
    logger.log("file_saved", path=str(path), operation="save_numpy")

# --- BIDS and Dataset Integrity Functions (Constitution III) ---

def compute_file_checksum(path: Union[str, Path], algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """
    Compute the checksum of a file for integrity verification.
    Supports sha256 (default), md5, sha1.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot compute checksum: file not found at {path}")
    
    hasher = hashlib.new(algorithm)
    with open(path, 'rb') as f:
        # Read in chunks to handle large files (e.g., NIfTI) without memory issues
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def verify_checksum(path: Union[str, Path], expected_checksum: str, algorithm: str = CHECKSUM_ALGORITHM) -> bool:
    """
    Verify a file's checksum against an expected value.
    Returns True if valid, raises ValueError if mismatch.
    """
    actual = compute_file_checksum(path, algorithm)
    if actual.lower() != expected_checksum.lower():
        logger.log(
            "checksum_mismatch",
            path=str(path),
            expected=expected_checksum,
            actual=actual,
            algorithm=algorithm,
            operation="verify_checksum"
        )
        raise ValueError(f"Checksum mismatch for {path}: expected {expected_checksum}, got {actual}")
    logger.log("checksum_verified", path=str(path), algorithm=algorithm, operation="verify_checksum")
    return True

def validate_bids_dataset(root: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate that a directory is a minimal BIDS-compliant dataset.
    Checks for required files (dataset_description.json, participants.tsv)
    and extracts versioning info from dataset_description.json.
    
    Returns a dict with:
      - valid: bool
      - version: str or None
      - license: str or None
      - missing_files: list of missing required file paths
    """
    root = Path(root)
    result = {
        "valid": True,
        "version": None,
        "license": None,
        "missing_files": [],
        "issues": []
    }

    # Check required files
    for req_file in BIDS_REQUIRED_FILES:
        file_path = root / req_file
        if not file_path.exists():
            result["valid"] = False
            result["missing_files"].append(req_file)
            logger.log(
                "bids_validation_failed",
                reason=f"Missing required BIDS file: {req_file}",
                path=str(root),
                operation="validate_bids_dataset"
            )
    
    if not result["valid"]:
        return result

    # Parse dataset_description.json for versioning
    desc_path = root / "dataset_description.json"
    try:
        desc = load_json(desc_path)
        result["version"] = desc.get("Version")
        result["license"] = desc.get("License")
        
        # Log version info
        logger.log(
            "bids_version_info",
            dataset_version=result["version"],
            license=result["license"],
            path=str(root),
            operation="validate_bids_dataset"
        )
    except Exception as e:
        result["valid"] = False
        result["issues"].append(f"Failed to parse dataset_description.json: {str(e)}")
        logger.log(
            "bids_validation_failed",
            reason=f"Error parsing dataset_description.json: {str(e)}",
            path=str(root),
            operation="validate_bids_dataset"
        )

    return result

def load_bids_participants(root: Union[str, Path]) -> pd.DataFrame:
    """
    Load the participants.tsv file from a BIDS dataset root.
    Returns a DataFrame with participant metadata.
    """
    root = Path(root)
    participants_path = root / "participants.tsv"
    if not participants_path.exists():
        raise FileNotFoundError(f"BIDS participants.tsv not found at {participants_path}")
    
    logger.log("loading_participants", path=str(participants_path), operation="load_bids_participants")
    return load_csv(participants_path, sep='\t')

def get_dataset_version(root: Union[str, Path]) -> Optional[str]:
    """
    Extract the dataset version string from dataset_description.json.
    Returns None if not found or file is invalid.
    """
    root = Path(root)
    desc_path = root / "dataset_description.json"
    if not desc_path.exists():
        return None
    try:
        desc = load_json(desc_path)
        return desc.get("Version")
    except Exception:
        return None

def verify_dataset_integrity(root: Union[str, Path], manifest_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Verify dataset integrity using a manifest file (if provided) or basic BIDS checks.
    
    Args:
        root: Path to the dataset root directory.
        manifest_path: Optional path to a JSON manifest containing expected checksums.
    
    Returns:
        Dict with 'valid', 'verified_files', 'failed_files', 'missing_files'.
    """
    root = Path(root)
    result = {
        "valid": True,
        "verified_files": [],
        "failed_files": [],
        "missing_files": []
    }

    # Basic BIDS validation first
    bids_check = validate_bids_dataset(root)
    if not bids_check["valid"]:
        result["valid"] = False
        result["missing_files"] = bids_check["missing_files"]
        return result

    # If manifest provided, verify checksums
    if manifest_path:
        manifest_path = Path(manifest_path)
        if not manifest_path.exists():
            result["valid"] = False
            result["missing_files"].append("manifest.json")
            return result

        manifest = load_json(manifest_path)
        files_to_check = manifest.get("files", {})
        
        for rel_path, expected_checksum in files_to_check.items():
            full_path = root / rel_path
            if not full_path.exists():
                result["missing_files"].append(rel_path)
                result["valid"] = False
                continue
            
            try:
                if verify_checksum(full_path, expected_checksum):
                    result["verified_files"].append(rel_path)
                else:
                    result["failed_files"].append(rel_path)
                    result["valid"] = False
            except ValueError as e:
                result["failed_files"].append(rel_path)
                result["valid"] = False
                logger.log("checksum_verification_error", error=str(e), operation="verify_dataset_integrity")
    
    return result