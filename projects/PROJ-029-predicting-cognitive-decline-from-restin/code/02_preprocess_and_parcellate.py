"""
T018: Preprocess rs-fMRI data and apply AAL parcellation.

Loads eligible subjects from data/processed/eligible_subjects.csv,
performs motion correction (mcflirt), normalization (nilearn),
and parcellation using the AAL atlas.

Outputs connectivity matrices to data/processed/connectivity_matrices/
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import nibabel as nib
from nilearn import image, masking, datasets
from nilearn.connectome import ConnectivityMeasure
from scipy import sparse

# Import from project utils
from utils.logger import get_logger, log_operation
from utils.atlas import load_aal_atlas_mask

logger = get_logger("preprocess_and_parcellate")

# Constants
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
ELIGIBLE_FILE = PROCESSED_DIR / "eligible_subjects.csv"
CONNECTIVITY_DIR = PROCESSED_DIR / "connectivity_matrices"
RAW_DIR = DATA_DIR / "raw" / "ds000246"

# FSL path configuration - check if FSL is available
def _check_fsl_mcflirt() -> bool:
    """Check if FSL's mcflirt is available in PATH."""
    try:
        subprocess.run(["which", "mcflirt"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def read_eligible_subjects(file_path: Path) -> List[Dict[str, str]]:
    """Read the eligible subjects CSV file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {file_path}")
    
    subjects = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            subjects.append(row)
    
    logger.log("read_eligible_subjects", count=len(subjects))
    return subjects

def find_subject_fmri(subject_id: str, bids_dir: Path) -> Optional[Path]:
    """Find the preprocessed fMRI file for a subject in BIDS directory."""
    # Look for functional files in BIDS structure
    # Pattern: sub-<label>/func/sub-<label>_task-rest_bold.nii.gz
    subject_dir = bids_dir / f"sub-{subject_id}" / "func"
    if not subject_dir.exists():
        return None
    
    # Find bold files
    bold_files = list(subject_dir.glob("*_task-rest_bold.nii.gz"))
    if not bold_files:
        # Try alternative naming
        bold_files = list(subject_dir.glob("*_bold.nii.gz"))
    
    if bold_files:
        return bold_files[0]
    return None

def motion_correction(input_path: Path, output_path: Path) -> bool:
    """
    Perform motion correction using FSL's mcflirt.
    
    Args:
        input_path: Path to input NIfTI file
        output_path: Path to save motion-corrected file
        
    Returns:
        True if successful, False otherwise
    """
    if not _check_fsl_mcflirt():
        logger.warning("mcflirt not found, skipping motion correction")
        # If FSL is not available, copy input to output
        import shutil
        shutil.copy2(input_path, output_path)
        return True
    
    try:
        # mcflirt: -in input -out output -refvol reference volume (0 = middle)
        # -dof 6: 6 degrees of freedom (rigid body)
        cmd = [
            "mcflirt",
            "-in", str(input_path),
            "-out", str(output_path),
            "-refvol", "0",
            "-dof", "6",
            "-mats",
            "-plots"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per subject
        )
        
        if result.returncode != 0:
            logger.error(f"mcflirt failed for {input_path}: {result.stderr}")
            return False
        
        logger.log("motion_correction", input=str(input_path), output=str(output_path))
        return True
        
    except subprocess.TimeoutExpired:
        logger.error(f"mcflirt timeout for {input_path}")
        return False
    except Exception as e:
        logger.error(f"mcflirt exception for {input_path}: {str(e)}")
        return False

def normalize_and_parcellate(
    mc_path: Path, 
    atlas_mask: np.ndarray,
    atlas_affine: np.ndarray,
    output_time_series_path: Path
) -> Optional[np.ndarray]:
    """
    Normalize fMRI data to MNI space and extract time series using AAL atlas.
    
    Args:
        mc_path: Path to motion-corrected NIfTI file
        atlas_mask: AAL atlas mask array
        atlas_affine: AAL atlas affine matrix
        output_time_series_path: Path to save time series CSV
        
    Returns:
        Time series array (n_timepoints, n_regions) or None if failed
    """
    try:
        # Load motion-corrected image
        mc_img = nib.load(str(mc_path))
        
        # Normalize to MNI space using nilearn
        # We use standard MNI template from nilearn
        from nilearn.datasets import load_mni152_template
        mni_template = load_mni152_template(resolution=2)
        
        # Normalize the functional image
        normalized_img = image.resample_to_img(mc_img, mni_template, interpolation="continuous")
        
        # Create a mask for the brain (non-zero voxels in atlas)
        # Use the AAL atlas to define regions of interest
        atlas_img = nib.Nifti1Image(atlas_mask, atlas_affine)
        
        # Extract time series from each region
        time_series = masking.apply_mask(normalized_img, atlas_img)
        
        # Save time series to CSV
        np.savetxt(output_time_series_path, time_series, delimiter=",")
        
        logger.log(
            "normalize_and_parcellate",
            input=str(mc_path),
            shape=time_series.shape,
            output=str(output_time_series_path)
        )
        
        return time_series
        
    except Exception as e:
        logger.error(f"Normalization/parcellation failed for {mc_path}: {str(e)}")
        return None

def save_connectivity_matrix(
    time_series: np.ndarray,
    subject_id: str,
    output_dir: Path
) -> Path:
    """
    Compute and save the connectivity matrix for a subject.
    
    Args:
        time_series: Time series array (n_timepoints, n_regions)
        subject_id: Subject identifier
        output_dir: Directory to save the matrix
        
    Returns:
        Path to the saved connectivity matrix
    """
    # Use Pearson correlation to compute connectivity
    conn_measure = ConnectivityMeasure(kind='correlation')
    connectivity_matrix = conn_measure.fit_transform([time_series])[0]
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as .npy file
    output_path = output_dir / f"sub-{subject_id}_connectivity.npy"
    np.save(output_path, connectivity_matrix)
    
    logger.log(
        "save_connectivity_matrix",
        subject=subject_id,
        shape=connectivity_matrix.shape,
        output=str(output_path)
    )
    
    return output_path

def save_time_series(
    time_series: np.ndarray,
    subject_id: str,
    output_dir: Path
) -> Path:
    """
    Save the time series data for a subject.
    
    Args:
        time_series: Time series array
        subject_id: Subject identifier
        output_dir: Directory to save the time series
        
    Returns:
        Path to the saved time series file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"sub-{subject_id}_time_series.npy"
    np.save(output_path, time_series)
    
    logger.log(
        "save_time_series",
        subject=subject_id,
        shape=time_series.shape,
        output=str(output_path)
    )
    
    return output_path

def write_status(output_dir: Path, success_count: int, total_count: int):
    """Write a status JSON file with processing results."""
    status = {
        "task": "preprocess_and_parcellate",
        "success_count": success_count,
        "total_count": total_count,
        "success_rate": success_count / total_count if total_count > 0 else 0.0
    }
    
    status_path = output_dir / "processing_status.json"
    with open(status_path, 'w') as f:
        json.dump(status, f, indent=2)
    
    logger.log("write_status", path=str(status_path))

def write_excluded_log(excluded_subjects: List[Dict[str, Any]], output_dir: Path):
    """Write a log of excluded subjects."""
    if not excluded_subjects:
        return
    
    log_path = output_dir / "excluded_subjects.log"
    with open(log_path, 'w') as f:
        for subj in excluded_subjects:
            f.write(f"Subject {subj.get('subject_id', 'unknown')}: {subj.get('reason', 'unknown')}\n")
    
    logger.log("write_excluded_log", count=len(excluded_subjects), path=str(log_path))

def preprocess_subject(
    subject_id: str,
    bids_dir: Path,
    atlas_mask: np.ndarray,
    atlas_affine: np.ndarray,
    output_dir: Path
) -> bool:
    """
    Preprocess a single subject: motion correction, normalization, parcellation.
    
    Args:
        subject_id: Subject identifier
        bids_dir: Path to BIDS data directory
        atlas_mask: AAL atlas mask array
        atlas_affine: AAL atlas affine matrix
        output_dir: Output directory for this subject
        
    Returns:
        True if successful, False otherwise
    """
    # Find input fMRI file
    fmri_path = find_subject_fmri(subject_id, bids_dir)
    if fmri_path is None:
        logger.warning(f"No fMRI file found for subject {subject_id}")
        return False
    
    # Create temporary directory for intermediate files
    temp_dir = output_dir / "temp" / subject_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Motion correction
    mc_output = temp_dir / "mc_bold.nii.gz"
    if not motion_correction(fmri_path, mc_output):
        logger.error(f"Motion correction failed for {subject_id}")
        return False
    
    # Step 2: Normalize and parcellate
    ts_output = temp_dir / "time_series.npy"
    time_series = normalize_and_parcellate(mc_output, atlas_mask, atlas_affine, ts_output)
    
    if time_series is None:
        logger.error(f"Normalization/parcellation failed for {subject_id}")
        return False
    
    # Step 3: Save connectivity matrix
    conn_path = save_connectivity_matrix(time_series, subject_id, output_dir)
    
    # Step 4: Save time series (optional, for debugging)
    save_time_series(time_series, subject_id, output_dir)
    
    # Cleanup temp directory
    import shutil
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    return True

def main():
    """Main entry point for preprocessing pipeline."""
    logger.log("main", start=True)
    
    # Ensure output directory exists
    CONNECTIVITY_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load eligible subjects
    try:
        subjects = read_eligible_subjects(ELIGIBLE_FILE)
    except FileNotFoundError as e:
        logger.error(str(e))
        print(f"Error: {e}")
        sys.exit(1)
    
    if not subjects:
        logger.error("No eligible subjects found")
        print("Error: No eligible subjects found in eligible_subjects.csv")
        sys.exit(1)
    
    # Load AAL atlas
    try:
        atlas_mask, atlas_affine = load_aal_atlas_mask()
        logger.log("load_atlas", shape=atlas_mask.shape)
    except Exception as e:
        logger.error(f"Failed to load AAL atlas: {str(e)}")
        print(f"Error loading AAL atlas: {e}")
        sys.exit(1)
    
    # Process each subject
    success_count = 0
    excluded_subjects = []
    
    for subject in subjects:
        subject_id = subject.get("subject_id", "")
        if not subject_id:
            excluded_subjects.append({"subject_id": "unknown", "reason": "Missing subject_id"})
            continue
        
        logger.info(f"Processing subject {subject_id}")
        
        success = preprocess_subject(
            subject_id=subject_id,
            bids_dir=RAW_DIR,
            atlas_mask=atlas_mask,
            atlas_affine=atlas_affine,
            output_dir=CONNECTIVITY_DIR
        )
        
        if success:
            success_count += 1
        else:
            excluded_subjects.append({"subject_id": subject_id, "reason": "Processing failed"})
    
    # Write status and exclusion logs
    write_status(CONNECTIVITY_DIR, success_count, len(subjects))
    write_excluded_log(excluded_subjects, CONNECTIVITY_DIR)
    
    logger.log("main", end=True, success_count=success_count, total_count=len(subjects))
    
    print(f"Preprocessing complete: {success_count}/{len(subjects)} subjects processed successfully")
    
    if success_count == 0:
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)
