import os
import sys
import hashlib
import json
import logging
import subprocess
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, List

from config import get_data_root, HCP_MMP_FILE_PATH, HCP_MMP_HASH
from utils.logger import get_logger, DataLoadError

logger = get_logger(__name__)

def verify_parcellation_file(data_root: Optional[Path] = None) -> Path:
    """
    Verify the presence and SHA-256 hash of the HCP-MMP parcellation file.
    MUST NOT download. File must be present and pinned.
    Raises DataLoadError if missing or hash mismatch.
    """
    if data_root is None:
        data_root = get_data_root()
    
    # Resolve the path relative to data_root
    # HCP_MMP_FILE_PATH is defined in config.py as 'raw/HCP_MMP1.0_Glasser2016.zip'
    file_path = data_root / HCP_MMP_FILE_PATH
    
    if not file_path.exists():
        raise DataLoadError(
            f"HCP-MMP parcellation file not found at {file_path}. "
            "The file must be placed in data/raw prior to execution (per T004/T005). "
            "Do not attempt to download at runtime."
        )
    
    # Calculate SHA-256
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    computed_hash = sha256_hash.hexdigest()
    
    if computed_hash != HCP_MMP_HASH:
        raise DataLoadError(
            f"Hash mismatch for HCP-MMP file at {file_path}. "
            f"Expected: {HCP_MMP_HASH}\nGot:      {computed_hash}\n"
            "The file may be corrupted or incorrect. Verify the source and re-download if necessary."
        )
    
    logger.info(f"HCP-MMP parcellation file verified successfully: {file_path}")
    logger.info(f"SHA-256: {computed_hash}")
    return file_path

def load_tractography(subject_id: str, data_root: Optional[Path] = None) -> Path:
    """
    Locate the raw tractography (.tck) file for a given subject.
    Expects data structure: data/raw/ds004230/sub-{id}/...
    """
    if data_root is None:
        data_root = get_data_root()
    
    # Expected path based on T009 download structure
    raw_dir = data_root / "raw" / "ds004230" / subject_id
    
    if not raw_dir.exists():
        raise FileNotFoundError(
            f"Raw dMRI directory not found for subject {subject_id} at {raw_dir}. "
            "Ensure T009 (download) has completed successfully."
        )
    
    # Search for .tck files
    tck_files = list(raw_dir.rglob("*.tck"))
    
    if not tck_files:
        raise FileNotFoundError(
            f"No tractography (.tck) files found for {subject_id} in {raw_dir}. "
            "Check if the dataset download was successful or if the file extension is different."
        )
    
    # If multiple, pick the first one (or logic could be added to merge)
    # For OpenNeuro ds004230, typically one main track file per subject
    tck_file = tck_files[0]
    logger.info(f"Found tractography file for {subject_id}: {tck_file}")
    return tck_file

def generate_connectome_matrix(
    tck_file: Path, 
    parcellation_file: Path, 
    subject_id: str, 
    data_root: Optional[Path] = None
) -> Path:
    """
    Generate the structural connectome adjacency matrix using MRtrix3 tck2connectome.
    
    This function executes the MRtrix3 command-line tool. It assumes MRtrix3 is installed
    and available in the system PATH.
    
    Output:
      - CSV file with the adjacency matrix
      - Numpy array saved for internal use
    """
    if data_root is None:
        data_root = get_data_root()
    
    # Ensure output directory exists
    output_dir = data_root / "processed" / "sc" / subject_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define output paths
    csv_output = output_dir / "connectome.csv"
    npy_output = output_dir / "connectome.npy"
    
    # MRtrix3 tck2connectome command arguments
    # We use the parcellation file (which should be an image, e.g., .nii.gz)
    # The command expects: tck2connectome tracks.tck labels.mif connectome.csv [options]
    # Since parcellation_file is a .zip, we assume it has been extracted or is an image path.
    # However, T004 says HCP_MMP_FILE_PATH is the zip. 
    # Realistically, for tck2connectome, we need the parcellation IMAGE (e.g., Glasser2016_HCP_MMP1.0.nii.gz).
    # The task description says "verify presence of ... .zip". 
    # If the code cannot run without the extracted image, we must handle that.
    # Given the constraint "MUST NOT fetch at runtime", we assume the zip contains the image 
    # or the image is alongside it. 
    # For robustness, we look for the .nii.gz inside the zip directory or expect the user 
    # to have extracted it. 
    # STRATEGY: We will assume the parcellation_file passed is the .nii.gz if the .zip check passed,
    # OR we try to find the .nii.gz in the same folder.
    
    # Let's refine: The config defines HCP_MMP_FILE_PATH. 
    # If it's a zip, we need the image. 
    # We will assume the extracted image is at: data/raw/Glasser2016_HCP_MMP1.0.nii.gz
    # or inside the zip directory. 
    # Since we cannot unzip at runtime (no fetch), we assume the image is present.
    # Let's look for the image file in the raw directory.
    
    parcellation_image = None
    if parcellation_file.suffix == '.zip':
        # Look for .nii.gz in the same directory
        parent_dir = parcellation_file.parent
        nii_files = list(parent_dir.glob("*.nii.gz"))
        if not nii_files:
            raise DataLoadError(
                f"Parcellation image (.nii.gz) not found in {parent_dir}. "
                "The HCP-MMP .zip must be extracted, or the .nii.gz must be present alongside it."
            )
        parcellation_image = nii_files[0]
    else:
        parcellation_image = parcellation_file

    logger.info(f"Using parcellation image: {parcellation_image}")

    cmd = [
        "tck2connectome",
        str(tck_file),
        str(parcellation_image),
        str(csv_output),
        "-out_assignments", str(output_dir / "assignments.txt"),
        "-scale_length",
        "-zero_diagonal" # Optional: often desired for structural connectomes
    ]
    
    logger.info(f"Executing MRtrix3 command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=3600 # 1 hour timeout per subject
        )
        logger.info(f"MRtrix3 completed successfully for {subject_id}")
        if result.stderr:
            logger.debug(f"MRtrix3 stderr: {result.stderr}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"MRtrix3 failed for {subject_id}: {e.stderr}")
        raise RuntimeError(f"MRtrix3 tck2connectome failed: {e.stderr}")
    except subprocess.TimeoutExpired:
        logger.error(f"MRtrix3 timed out for {subject_id}")
        raise RuntimeError(f"MRtrix3 tck2connectome timed out for {subject_id}")
    
    # Convert CSV to numpy array and save as .npy for consistency with other modules
    try:
        df = pd.read_csv(csv_output, header=None)
        matrix = df.values.astype(np.float32)
        np.save(npy_output, matrix)
        logger.info(f"Saved connectome matrix as numpy array: {npy_output}")
        return npy_output
    except Exception as e:
        logger.error(f"Failed to convert CSV to numpy for {subject_id}: {e}")
        raise e

def save_connectome_matrix(matrix: np.ndarray, subject_id: str, data_root: Optional[Path] = None) -> Path:
    """
    Save a connectome matrix to disk.
    (Helper if matrix is generated elsewhere, but primary flow is via generate_connectome_matrix)
    """
    if data_root is None:
        data_root = get_data_root()
    
    output_dir = data_root / "processed" / "sc" / subject_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "connectome.npy"
    np.save(output_file, matrix)
    logger.info(f"Saved connectome matrix to {output_file}")
    return output_file

def run_preprocessing_for_subject(subject_id: str, data_root: Optional[Path] = None) -> Path:
    """
    Run the full dMRI preprocessing pipeline for a single subject.
    1. Verify Parcellation
    2. Load Tractography
    3. Generate Connectome Matrix
    """
    if data_root is None:
        data_root = get_data_root()
    
    logger.info(f"--- Processing subject: {subject_id} ---")
    
    # 1. Verify Parcellation
    parcellation_file = verify_parcellation_file(data_root)
    
    # 2. Load Tractography
    tck_file = load_tractography(subject_id, data_root)
    
    # 3. Generate Connectome
    output_path = generate_connectome_matrix(tck_file, parcellation_file, subject_id, data_root)
    
    return output_path

def run_pipeline(data_root: Optional[Path] = None) -> List[Path]:
    """
    Run the dMRI preprocessing pipeline for all subjects found in data/raw/ds004230.
    """
    if data_root is None:
        data_root = get_data_root()
    
    raw_dir = data_root / "raw" / "ds004230"
    if not raw_dir.exists():
        logger.error(f"Raw dMRI data directory not found at {raw_dir}.")
        raise FileNotFoundError(f"Raw data directory missing: {raw_dir}")
    
    # Identify subjects
    subjects = [
        d.name for d in raw_dir.iterdir() 
        if d.is_dir() and d.name.startswith("sub-")
    ]
    
    if not subjects:
        logger.warning(f"No subjects found in {raw_dir}.")
        return []
    
    logger.info(f"Found {len(subjects)} subjects to process: {subjects}")
    
    results = []
    for sub in subjects:
        try:
            logger.info(f"Starting processing for {sub}...")
            output_path = run_preprocessing_for_subject(sub, data_root)
            results.append(output_path)
        except Exception as e:
            logger.error(f"Failed to process {sub}: {e}")
            # Per spec: "FAIL LOUDLY" on critical errors. 
            # If one subject fails, do we stop? 
            # The execution gate requires real results. If we skip, we might miss data.
            # We will raise to stop the pipeline, ensuring no partial/fake results are accepted.
            raise e
    
    logger.info(f"Pipeline completed. Processed {len(results)} subjects.")
    return results

def main():
    """
    Entry point for the dMRI preprocessing script.
    """
    logger.info("Starting dMRI preprocessing pipeline...")
    try:
        run_pipeline()
        logger.info("dMRI preprocessing completed successfully.")
    except Exception as e:
        logger.error(f"dMRI preprocessing failed: {e}")
        # Re-raise to ensure the exit code is non-zero for the runner
        raise e

if __name__ == "__main__":
    main()
