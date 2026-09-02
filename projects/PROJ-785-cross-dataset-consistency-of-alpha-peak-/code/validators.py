"""
validators.py

Implements BIDS compliance checks and data integrity validation for EEG datasets.
Specifically validates:
  - Sampling frequency presence and validity in dataset_description.json
  - Channel layout consistency (existence of required files)
  - SHA256 checksum generation for raw data artifacts.

Raises DataIntegrityError if validation fails.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import get_data_path
from exceptions import DataIntegrityError


def _get_dataset_description_path(dataset_id: str) -> Path:
    """Construct the path to dataset_description.json for a given dataset ID."""
    data_root = get_data_path()
    return data_root / "raw" / dataset_id / "dataset_description.json"


def validate_sampling_frequency(dataset_id: str) -> Dict[str, Any]:
    """
    Validates that 'sampling_frequency' exists in dataset_description.json
    and is a valid positive number.

    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds003775').

    Returns:
        A dictionary containing the validated sampling frequency.

    Raises:
        DataIntegrityError: If the file is missing, JSON is invalid,
        or 'sampling_frequency' is missing/invalid.
    """
    desc_path = _get_dataset_description_path(dataset_id)

    if not desc_path.exists():
        raise DataIntegrityError(
            f"dataset_description.json not found at {desc_path}. "
            "Cannot validate sampling frequency."
        )

    try:
        with open(desc_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataIntegrityError(
            f"Invalid JSON in dataset_description.json for {dataset_id}: {e}"
        ) from e

    if "sampling_frequency" not in data:
        raise DataIntegrityError(
            f"Missing 'sampling_frequency' in dataset_description.json for {dataset_id}. "
            "This field is required for BIDS compliance and signal processing."
        )

    fs = data["sampling_frequency"]
    if not isinstance(fs, (int, float)) or fs <= 0:
        raise DataIntegrityError(
            f"Invalid 'sampling_frequency' value ({fs}) in dataset_description.json for {dataset_id}. "
            "Must be a positive number."
        )

    return {"sampling_frequency": fs, "source_file": str(desc_path)}


def validate_channel_layout(dataset_id: str, expected_subjects: List[str]) -> List[Dict[str, Any]]:
    """
    Validates the existence of EEG channel layout files (e.g., .tsv sidecars)
    and checks for required columns.

    Args:
        dataset_id: The OpenNeuro dataset ID.
        expected_subjects: List of subject IDs to check (e.g., ['sub-01', 'sub-02']).

    Returns:
        A list of validation results for each subject.

    Raises:
        DataIntegrityError: If a required channel file is missing or empty.
    """
    data_root = get_data_path()
    raw_dir = data_root / "raw" / dataset_id
    results = []

    required_columns = {"name", "type"}

    for subject_id in expected_subjects:
        # Look for eeg sub-XX_task-rest_channels.tsv
        # BIDS structure: sub-<label>/eeg/sub-<label>_<task>_<modality>_channels.tsv
        # We assume a standard task 'rest' for this project based on spec.
        channels_file = None
        eeg_dir = raw_dir / subject_id / "eeg"

        if not eeg_dir.exists():
            raise DataIntegrityError(
                f"EEG directory missing for {subject_id} in {dataset_id}."
            )

        # Find the channels file
        for f in eeg_dir.glob(f"{subject_id}_*_channels.tsv"):
            channels_file = f
            break

        if not channels_file:
            raise DataIntegrityError(
                f"No channels.tsv file found for {subject_id} in {dataset_id}. "
                f"Searched in {eeg_dir}."
            )

        try:
            with open(channels_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            raise DataIntegrityError(
                f"Could not read channels.tsv for {subject_id}: {e}"
            ) from e

        if len(lines) < 2:
            raise DataIntegrityError(
                f"channels.tsv for {subject_id} is empty or missing header."
            )

        # Parse header
        header = lines[0].strip().split("\t")
        if not required_columns.issubset(set(header)):
            raise DataIntegrityError(
                f"channels.tsv for {subject_id} missing required columns. "
                f"Found: {header}, Required: {required_columns}"
            )

        results.append({
            "subject": subject_id,
            "file": str(channels_file),
            "valid": True,
            "channel_count": len(lines) - 1
        })

    return results


def generate_sha256_checksum(file_path: str) -> str:
    """
    Generates a SHA256 checksum for a given file.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        Hexadecimal string of the SHA256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        DataIntegrityError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for checksum generation: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
    except Exception as e:
        raise DataIntegrityError(
            f"Failed to read file {file_path} for checksum generation: {e}"
        ) from e

    return sha256_hash.hexdigest()


def validate_all_datasets(dataset_ids: List[str]) -> Dict[str, Any]:
    """
    Runs comprehensive validation across a list of dataset IDs.
    Includes sampling frequency check, channel layout check (for first 2 subjects),
    and checksum generation for the dataset_description.json.

    Args:
        dataset_ids: List of dataset IDs to validate.

    Returns:
        Dictionary with validation summary and details.

    Raises:
        DataIntegrityError: If any dataset fails validation.
    """
    summary = {
        "total_datasets": len(dataset_ids),
        "valid_datasets": 0,
        "failed_datasets": 0,
        "details": {}
    }

    for ds_id in dataset_ids:
        try:
            # 1. Validate Sampling Frequency
            fs_info = validate_sampling_frequency(ds_id)

            # 2. Check for subjects (basic file existence check)
            data_root = get_data_path()
            raw_dir = data_root / "raw" / ds_id
            subjects = [d.name for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]

            if not subjects:
                raise DataIntegrityError(f"No subjects found in {ds_id}.")

            # 3. Validate Channel Layout for first 2 subjects
            sample_subjects = subjects[:2]
            channel_info = validate_channel_layout(ds_id, sample_subjects)

            # 4. Generate Checksum for dataset_description
            desc_path = _get_dataset_description_path(ds_id)
            checksum = generate_sha256_checksum(str(desc_path))

            summary["details"][ds_id] = {
                "status": "valid",
                "sampling_frequency": fs_info["sampling_frequency"],
                "subjects_checked": sample_subjects,
                "channel_validation": channel_info,
                "description_checksum": checksum
            }
            summary["valid_datasets"] += 1

        except DataIntegrityError as e:
            summary["details"][ds_id] = {
                "status": "failed",
                "error": str(e)
            }
            summary["failed_datasets"] += 1
            # Re-raise to fail loudly as per requirements
            raise

    return summary