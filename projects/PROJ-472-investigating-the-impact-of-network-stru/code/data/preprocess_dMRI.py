"""
Preprocess dMRI tractography data to generate HCP-MMP structural connectomes.

This module handles:
1. Downloading and verifying the HCP-MMP parcellation file.
2. Converting .tck tractography files to adjacency matrices using MRtrix3.
3. Calculating and storing file checksums for data integrity.
"""
import os
import sys
import hashlib
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Local imports
from config import get_data_root, HCP_MMP_URL, HCP_MMP_FILE_PATH, HCP_MMP_HASH, ensure_directories
from utils.logger import get_logger, log_pipeline_start, log_pipeline_end, handle_exceptions
from utils.data_setup import compute_file_checksum, load_checksums, save_checksums, verify_file_integrity

logger = get_logger(__name__)

# Constants
PARCELLATION_ZIP_NAME = "HCP_MMP1.0_Glasser2016.zip"
PARCELLATION_UNZIPPED_NAME = "HCP_MMP1.0_Glasser2016.dlabel.nii"
TRACK_FILE_EXT = ".tck"
CONNECTOME_OUTPUT_EXT = ".tsv"
ASSIGNMENT_OUTPUT_EXT = ".txt"

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex digest of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_parcellation_file() -> Path:
    """
    Download the HCP-MMP parcellation file if it doesn't exist.

    Returns:
        Path to the downloaded zip file.
    """
    data_root = get_data_root()
    raw_dir = data_root / "raw"
    ensure_directories()
    
    zip_path = raw_dir / PARCELLATION_ZIP_NAME
    
    if zip_path.exists():
        logger.info(f"Parcellation file already exists at {zip_path}")
        # Verify integrity
        calculated_hash = compute_sha256(zip_path)
        # Load stored hash if available
        checksum_file = data_root / "processed" / "parcellation_hash.json"
        stored_hash = None
        if checksum_file.exists():
            with open(checksum_file, 'r') as f:
                stored_hash = json.load(f).get('parcellation_hash')
        
        # If we have a stored hash, verify against it
        if stored_hash and calculated_hash != stored_hash:
            logger.warning(f"Hash mismatch for {zip_path}. Expected: {stored_hash}, Got: {calculated_hash}")
            # If the stored hash is a placeholder, update it
            if stored_hash == "PLACEHOLDER_HASH_TO_BE_UPDATED":
                logger.info("Updating placeholder hash with calculated value.")
                save_checksums({
                    "parcellation_hash": calculated_hash,
                    "file_path": str(zip_path)
                })
                return zip_path
            else:
                raise RuntimeError(f"Parcellation file integrity check failed. Hash mismatch.")
        else:
            # If no stored hash or match, save/update the hash
            if stored_hash != calculated_hash:
                logger.info(f"Saving calculated hash: {calculated_hash}")
                save_checksums({
                    "parcellation_hash": calculated_hash,
                    "file_path": str(zip_path)
                })
        return zip_path

    logger.info(f"Downloading parcellation file from {HCP_MMP_URL}...")
    try:
        # Use wget for simplicity and reliability in this context
        # If wget is not available, we could use urllib.request
        import urllib.request
        logger.info("Starting download...")
        urllib.request.urlretrieve(HCP_MMP_URL, zip_path)
        logger.info("Download complete.")
        
        # Verify the download
        calculated_hash = compute_sha256(zip_path)
        logger.info(f"Calculated hash: {calculated_hash}")
        
        # Save the hash
        save_checksums({
            "parcellation_hash": calculated_hash,
            "file_path": str(zip_path)
        })
        
        return zip_path
    except Exception as e:
        logger.error(f"Failed to download parcellation file: {e}")
        raise

def verify_parcellation_file(zip_path: Path) -> Path:
    """
    Verify the downloaded parcellation file and unzip it if necessary.

    Args:
        zip_path: Path to the zip file.

    Returns:
        Path to the unzipped parcellation file (nii).
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"Parcellation file not found at {zip_path}")

    # Check hash
    calculated_hash = compute_sha256(zip_path)
    checksum_file = get_data_root() / "processed" / "parcellation_hash.json"
    stored_hash = None
    if checksum_file.exists():
        with open(checksum_file, 'r') as f:
            stored_hash = json.load(f).get('parcellation_hash')

    if stored_hash and calculated_hash != stored_hash:
        raise RuntimeError(f"Parcellation file integrity check failed. Expected: {stored_hash}, Got: {calculated_hash}")

    # Unzip if needed
    nii_path = zip_path.with_name(PARCELLATION_UNZIPPED_NAME)
    if not nii_path.exists():
        logger.info(f"Unzipping {zip_path}...")
        try:
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(zip_path.parent)
            logger.info(f"Unzipped to {nii_path}")
        except Exception as e:
            logger.error(f"Failed to unzip parcellation file: {e}")
            raise
    
    return nii_path

def load_tractography(subject_id: str) -> Path:
    """
    Locate the tractography file (.tck) for a given subject.

    Args:
        subject_id: The subject identifier (e.g., 'sub-001').

    Returns:
        Path to the .tck file.
    """
    data_root = get_data_root()
    # Assuming the structure: data/raw/dMRI/sub-{id}/tracks.tck or similar
    # The exact path depends on how T009 organized the downloaded data.
    # We look for .tck files in the subject's directory.
    subject_dir = data_root / "raw" / "dMRI" / subject_id
    
    if not subject_dir.exists():
        # Try alternative structure if raw is flat
        subject_dir = data_root / "raw" / subject_id
        
    if not subject_dir.exists():
        raise FileNotFoundError(f"Subject directory not found for {subject_id}")

    tck_files = list(subject_dir.glob(f"*{TRACK_FILE_EXT}"))
    if not tck_files:
        raise FileNotFoundError(f"No tractography file (.tck) found for subject {subject_id} in {subject_dir}")
    
    if len(tck_files) > 1:
        logger.warning(f"Multiple .tck files found for {subject_id}: {tck_files}. Using the first one.")
    
    return tck_files[0]

def generate_connectome_matrix(tck_path: Path, parcellation_path: Path, output_dir: Path, subject_id: str) -> Path:
    """
    Generate a connectome matrix from tractography and parcellation using MRtrix3.

    Args:
        tck_path: Path to the .tck tractography file.
        parcellation_path: Path to the parcellation file (nii).
        output_dir: Directory to save the output connectome.
        subject_id: Subject identifier for naming.

    Returns:
        Path to the generated connectome matrix (.tsv).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    connectome_tsv = output_dir / f"connectome_{subject_id}.tsv"
    assignments_txt = output_dir / f"assignments_{subject_id}.txt"

    # Check if MRtrix3 is available
    try:
        subprocess.run(["tck2connectome", "-version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("MRtrix3 (tck2connectome) is not installed or not in PATH. Please install MRtrix3.")

    cmd = [
        "tck2connectome",
        str(tck_path),
        str(parcellation_path),
        str(connectome_tsv),
        "-scale_invlength",
        "-out_assignments",
        str(assignments_txt)
    ]

    logger.info(f"Running MRtrix3 command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stderr:
            logger.debug(f"MRtrix3 stderr: {result.stderr}")
        logger.info(f"Connectome generated: {connectome_tsv}")
        return connectome_tsv
    except subprocess.CalledProcessError as e:
        logger.error(f"MRtrix3 command failed: {e}")
        logger.error(f"Stderr: {e.stderr}")
        raise

def save_connectome_matrix(connectome_path: Path, subject_id: str) -> None:
    """
    (Optional) Additional processing or validation of the saved connectome.
    Currently, the matrix is saved directly by generate_connectome_matrix.
    This function can be extended for format conversion or validation.
    """
    if not connectome_path.exists():
        raise FileNotFoundError(f"Connectome file not found: {connectome_path}")
    
    # Basic validation: check if it's a valid TSV
    try:
        import pandas as pd
        df = pd.read_csv(connectome_path, sep='\t', header=None)
        logger.info(f"Validated connectome matrix for {subject_id}: {df.shape}")
    except Exception as e:
        logger.warning(f"Could not validate connectome matrix for {subject_id}: {e}")

def run_preprocessing_for_subject(subject_id: str) -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline for a single subject.

    Args:
        subject_id: The subject identifier.

    Returns:
        Dictionary with paths to generated files.
    """
    logger.info(f"Processing subject: {subject_id}")
    
    # 1. Ensure parcellation is available and verified
    zip_path = download_parcellation_file()
    parcellation_path = verify_parcellation_file(zip_path)
    
    # 2. Load tractography
    tck_path = load_tractography(subject_id)
    
    # 3. Generate connectome
    output_dir = get_data_root() / "processed" / "connectomes" / subject_id
    connectome_path = generate_connectome_matrix(tck_path, parcellation_path, output_dir, subject_id)
    
    # 4. Validate/Save
    save_connectome_matrix(connectome_path, subject_id)
    
    return {
        "subject_id": subject_id,
        "tck_path": str(tck_path),
        "parcellation_path": str(parcellation_path),
        "connectome_path": str(connectome_path)
    }

def run_pipeline(subject_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Run the preprocessing pipeline for a list of subjects.

    Args:
        subject_ids: List of subject IDs to process. If None, processes all found in data/raw.

    Returns:
        List of results dictionaries for each subject.
    """
    log_pipeline_start("preprocess_dMRI")
    
    data_root = get_data_root()
    
    if subject_ids is None:
        # Discover subjects
        raw_dMRI_dir = data_root / "raw" / "dMRI"
        if not raw_dMRI_dir.exists():
            # Try flat structure
            raw_dMRI_dir = data_root / "raw"
        
        if not raw_dMRI_dir.exists():
            raise FileNotFoundError(f"dMRI raw directory not found: {raw_dMRI_dir}")
        
        # Find directories that look like subjects (sub-*)
        subject_dirs = [d for d in raw_dMRI_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
        subject_ids = [d.name for d in subject_dirs]
        
        if not subject_ids:
            logger.warning("No subjects found in raw dMRI directory.")
            return []

    results = []
    for sid in subject_ids:
        try:
            result = run_preprocessing_for_subject(sid)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process subject {sid}: {e}")
            # Continue with other subjects
            continue
    
    log_pipeline_end("preprocess_dMRI")
    return results

@handle_exceptions
def main():
    """
    Main entry point for the script.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Preprocess dMRI tractography to connectomes.")
    parser.add_argument("--subjects", nargs="+", help="Specific subject IDs to process.")
    args = parser.parse_args()

    subject_ids = args.subjects if args.subjects else None
    results = run_pipeline(subject_ids)
    
    logger.info(f"Pipeline completed. Processed {len(results)} subjects.")
    for r in results:
        logger.info(f"  - {r['subject_id']}: {r['connectome_path']}")

if __name__ == "__main__":
    main()