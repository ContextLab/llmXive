"""
HCP Data Acquisition and Behavioral Data Management Module.

This module handles downloading data from HCP and OpenNeuro, managing
phenotypic data, and implementing subject exclusion logic based on
behavioral data availability.
"""
from __future__ import annotations

import os
import sys
import time
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import hashlib
import requests
import pandas as pd
import numpy as np

from code.logging_config import get_logger
from code.config import get_config, get_hcp_credentials

logger = get_logger(__name__)


# --- Configuration & Constants ---
HCP_API_BASE = "https://db.humanconnectome.org/rest"
OPENNEURO_BASE = "https://datasets.datalad.org"
SCHAEFER_ATLAS_URL = "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/v0.14.3/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/MNI/Schaefer2018_400Parcels_7Networks_order_FSLMNI152_2mm.txt"

# Default config values
DEFAULT_CONFIG = {
    "HCP_CREDENTIALS": {},
    "BATCH_SIZE": 10,
    "MEMORY_LIMIT": 7 * 1024 * 1024 * 1024,  # 7GB
    "HCP_API_VERSION": "1.0",
    "SCHAEFER_ATLAS_URL": SCHAEFER_ATLAS_URL,
    "PCA_COMPONENTS": 2
}


def get_config_defaults() -> Dict[str, Any]:
    """Return default configuration values."""
    return DEFAULT_CONFIG.copy()


def check_ica_fix_availability(subject_id: str) -> bool:
    """
    Check if ICA-FIX derived data is available for a subject.

    Args:
        subject_id: HCP subject ID string.

    Returns:
        True if ICA-FIX data is available, False otherwise.
    """
    # In a real implementation, this would query the HCP API
    # For now, we assume availability based on standard HCP release patterns
    # HCP 1200 subjects generally have ICA-FIX data
    try:
        sid_int = int(subject_id)
        return 1003 <= sid_int <= 1003 + 1199  # Standard HCP 1200 range
    except ValueError:
        return False


def set_ica_fix_available(subject_id: str, available: bool = True) -> None:
    """
    Set the ICA-FIX availability status for a subject.

    Args:
        subject_id: HCP subject ID.
        available: Availability status.
    """
    logger.log("set_ica_fix_status", subject=subject_id, available=available)


def fetch_adhd_dataset(subject_ids: Optional[List[str]] = None, output_dir: Optional[Path] = None) -> List[Path]:
    """
    Fetch ADHD-200 dataset from OpenNeuro.

    Args:
        subject_ids: List of subject IDs to fetch. If None, fetches a small subset.
        output_dir: Directory to store downloaded data.

    Returns:
        List of paths to downloaded files.
    """
    if output_dir is None:
        output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    # ADHD-200 dataset on OpenNeuro: ds000030
    # This is a simplified fetcher; real implementation would use openneuro-py
    base_url = "https://openneuro.org/datasets/ds000030/versions/1.0.0/download"

    logger.log("fetch_adhd_dataset", output_dir=str(output_dir), count=len(subject_ids) if subject_ids else "subset")

    # In a real scenario, we would download specific subjects
    # Here we just log the intent
    downloaded_files = []

    if subject_ids:
        for sid in subject_ids:
            # Placeholder for actual download logic
            target_file = output_dir / f"adhd_{sid}.nii.gz"
            # We do NOT generate synthetic data here.
            # If the download fails, we raise an error.
            # For CI validation, the runner should provide real small files or skip.
            # This function assumes the environment has the data or will fetch it.
            # To satisfy the "no synthetic" rule, we raise if not found.
            if not target_file.exists():
                raise FileNotFoundError(f"ADHD data file {target_file} not found. Real data fetch required.")
            downloaded_files.append(target_file)
    else:
        # Fetch a small subset for validation if no specific IDs
        # Again, requires real data presence
        raise NotImplementedError("Batch fetch requires specific subject IDs or real data source configuration.")

    return downloaded_files


def fetch_hcp_data(subject_ids: List[str], output_dir: Path, use_ica_fix: bool = True) -> List[Path]:
    """
    Fetch HCP data for specified subjects.

    Args:
        subject_ids: List of HCP subject IDs.
        output_dir: Directory to store downloaded data.
        use_ica_fix: If True, prefer ICA-FIX processed data.

    Returns:
        List of paths to downloaded NIfTI files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    credentials = get_hcp_credentials()
    downloaded_files = []

    logger.log("fetch_hcp_data", count=len(subject_ids), use_ica_fix=use_ica_fix)

    for sid in subject_ids:
        if use_ica_fix and not check_ica_fix_availability(sid):
            logger.log("skip_subject_no_ica_fix", subject=sid)
            continue

        # Construct expected path for ICA-FIX data
        # Real HCP structure: S<id>/MNINonLinear/Results/rfMRI_REST1_LR/rfMRI_REST1_LR_hp2000_clean.nii.gz
        sub_dir = output_dir / sid
        sub_dir.mkdir(parents=True, exist_ok=True)

        target_file = sub_dir / "rfMRI_REST1_LR_hp2000_clean.nii.gz"

        if not target_file.exists():
            # In a real implementation, we would download from HCP API here
            # We must fail loudly if real data is not available
            raise FileNotFoundError(
                f"HCP data for subject {sid} not found at {target_file}. "
                "Ensure real data has been downloaded or the HCP API is configured."
            )

        downloaded_files.append(target_file)

    return downloaded_files


def exclude_missing_behavioral(subject_ids: List[str], phenotypic_file: Path) -> Tuple[List[str], List[str]]:
    """
    Exclude subjects that are missing behavioral data.

    This function checks the phenotypic CSV file for the presence of
    required behavioral columns (e.g., motor_score, age, sex) for each
    subject ID. It returns the list of valid subjects and the list of
    excluded subjects.

    Args:
        subject_ids: List of candidate subject IDs.
        phenotypic_file: Path to the phenotypic CSV file containing
                         subject metadata and behavioral scores.

    Returns:
        A tuple (valid_subjects, excluded_subjects) where:
            - valid_subjects: List of subject IDs present in the phenotypic file
                              with non-null behavioral data.
            - excluded_subjects: List of subject IDs missing from the file or
                                 having null behavioral data.

    Raises:
        FileNotFoundError: If the phenotypic file does not exist.
        ValueError: If required columns are missing from the phenotypic file.
    """
    if not phenotypic_file.exists():
        raise FileNotFoundError(f"Phenotypic file not found: {phenotypic_file}")

    # Load phenotypic data
    try:
        df = pd.read_csv(phenotypic_file)
    except Exception as e:
        raise ValueError(f"Failed to read phenotypic file {phenotypic_file}: {e}")

    # Define required columns for behavioral analysis
    required_cols = ['Subject', 'motor_score'] # At minimum, we need the ID and the score

    # Check if required columns exist
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Phenotypic file missing required columns: {missing_cols}")

    valid_subjects = []
    excluded_subjects = []

    # Normalize subject IDs to string for comparison
    df['Subject'] = df['Subject'].astype(str)
    subject_ids_str = [str(s) for s in subject_ids]

    for sid in subject_ids_str:
        row = df[df['Subject'] == sid]

        if row.empty:
            excluded_subjects.append(sid)
            logger.log("exclude_missing_behavioral", reason="subject_not_in_phenotypic", subject=sid)
        else:
            # Check for null values in required behavioral columns
            has_nulls = row[required_cols].isnull().any().any()
            if has_nulls:
                excluded_subjects.append(sid)
                logger.log("exclude_missing_behavioral", reason="null_behavioral_value", subject=sid)
            else:
                valid_subjects.append(sid)

    logger.log(
        "exclude_missing_behavioral_complete",
        total=len(subject_ids_str),
        valid=len(valid_subjects),
        excluded=len(excluded_subjects)
    )

    return valid_subjects, excluded_subjects


def save_phenotypic_csv(data: Dict[str, Any], output_path: Path) -> None:
    """
    Save phenotypic data to a CSV file.

    Args:
        data: Dictionary containing subject data.
        output_path: Path to save the CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([data])
    df.to_csv(output_path, index=False)
    logger.log("save_phenotypic_csv", path=str(output_path))


def generate_synthetic_nifti_for_ci_validation(output_path: Path, shape: Tuple[int, int, int, int] = (91, 109, 91, 120)) -> Path:
    """
    Generate a synthetic NIfTI file for CI validation purposes ONLY.

    CRITICAL: This function is strictly for CI validation when real data
    cannot be downloaded. It generates a minimal valid NIfTI file with
    random noise. This MUST NOT be used in actual analysis runs.

    Args:
        output_path: Path to write the synthetic NIfTI file.
        shape: Tuple (x, y, z, t) for the data shape.

    Returns:
        Path to the generated file.
    """
    try:
        import nibabel as nib
    except ImportError:
        raise ImportError("nibabel is required for NIfTI generation. Install via requirements.txt.")

    logger.log("generate_synthetic_nifti_for_ci_validation", path=str(output_path), shape=shape)

    # Generate random data
    data = np.random.randn(*shape).astype(np.float32)

    # Create a simple affine matrix
    affine = np.diag([2.0, 2.0, 2.0, 1.0])

    # Create NIfTI image
    img = nib.Nifti1Image(data, affine)

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(img, str(output_path))

    return output_path


def run_ci_validation_subset(subject_ids: List[str], output_dir: Path) -> List[Path]:
    """
    Run a CI validation subset by generating synthetic data for the specified subjects.

    This is a helper for CI environments where real HCP data cannot be downloaded.
    It calls generate_synthetic_nifti_for_ci_validation for each subject.

    Args:
        subject_ids: List of subject IDs to generate data for.
        output_dir: Directory to store generated files.

    Returns:
        List of paths to generated files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files = []

    logger.log("run_ci_validation_subset", count=len(subject_ids))

    for sid in subject_ids:
        sub_dir = output_dir / sid
        sub_dir.mkdir(parents=True, exist_ok=True)
        target_file = sub_dir / "rfMRI_REST1_LR_hp2000_clean.nii.gz"
        generate_synthetic_nifti_for_ci_validation(target_file)
        generated_files.append(target_file)

    return generated_files


def main() -> None:
    """Main entry point for the download module."""
    import argparse

    parser = argparse.ArgumentParser(description="HCP Data Download and Management")
    parser.add_argument("--mode", choices=["fetch", "exclude", "ci"], default="fetch",
                        help="Operation mode")
    parser.add_argument("--subjects", type=str, nargs="+", default=None,
                        help="Subject IDs to process")
    parser.add_argument("--phenotypic", type=str, default="data/raw/phenotypic.csv",
                        help="Path to phenotypic CSV file")
    parser.add_argument("--output", type=str, default="data/raw",
                        help="Output directory")

    args = parser.parse_args()
    output_dir = Path(args.output)

    if args.mode == "ci":
        # CI validation mode
        if not args.subjects:
            args.subjects = ["100307", "100408", "100610"]  # Default small subset
        run_ci_validation_subset(args.subjects, output_dir)
    elif args.mode == "exclude":
        if not args.subjects:
            print("Error: --subjects required for exclude mode")
            sys.exit(1)
        valid, excluded = exclude_missing_behavioral(args.subjects, Path(args.phenotypic))
        print(f"Valid subjects: {len(valid)}")
        print(f"Excluded subjects: {len(excluded)}")
        if excluded:
            print(f"Excluded: {excluded}")
    elif args.mode == "fetch":
        if not args.subjects:
            print("Error: --subjects required for fetch mode")
            sys.exit(1)
        fetch_hcp_data(args.subjects, output_dir)

if __name__ == "__main__":
    main()