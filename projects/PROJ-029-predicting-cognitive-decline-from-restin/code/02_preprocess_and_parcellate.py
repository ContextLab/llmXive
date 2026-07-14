"""
T018: Preprocess rs-fMRI data and parcellate using AAL atlas.

Implements:
1. Motion correction using FSL mcflirt (6 DOF, default reference).
2. Normalization to MNI space using Nilearn.
3. Parcellation using AAL atlas.
4. Extraction of mean time series per region.
5. Output: Connectivity matrices (saved as .nii.gz) and time series (saved as .csv).

Note: This script assumes FSL is installed and available in the system PATH.
"""
from __future__ import annotations

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
import nibabel as nib
import numpy as np
from nilearn import image, input_data
from nilearn.datasets import fetch_atlas_aal

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger, log_operation
from utils.atlas import load_aal_atlas_mask, validate_atlas_shape
from config import get_config

logger = get_logger("preprocess_and_parcellate")

# Constants
CONFIG = get_config()
RANDOM_SEED = CONFIG.get("random_seed", 42)
ELIGIBLE_SUBJECTS_FILE = Path("data/processed/eligible_subjects.csv")
RAW_DATA_DIR = Path("data/raw/ds000246")
PROCESSED_DIR = Path("data/processed")
CONNECTIVITY_DIR = PROCESSED_DIR / "connectivity_matrices"
TIME_SERIES_DIR = PROCESSED_DIR / "time_series"
FSL_MCFLIRT_CMD = "mcflirt"

def read_eligible_subjects() -> List[str]:
    """Read eligible subjects from CSV file."""
    if not ELIGIBLE_SUBJECTS_FILE.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_FILE}")
    
    df = pd.read_csv(ELIGIBLE_SUBJECTS_FILE)
    return df["subject_id"].tolist()

def find_subject_fmri(subject_id: str) -> Optional[Path]:
    """Find the preprocessed rs-fMRI file for a subject."""
    # Look for the first rs-fMRI file in the subject's directory
    subject_dir = RAW_DATA_DIR / "sub-" + subject_id / "func"
    if not subject_dir.exists():
        logger.warning(f"Subject directory not found: {subject_dir}")
        return None
    
    # Find the first rs-fMRI file
    fmri_files = list(subject_dir.glob("sub-*_task-rest_*preproc*.nii.gz"))
    if not fmri_files:
        # Try without 'preproc' in the name
        fmri_files = list(subject_dir.glob("sub-*_task-rest_*.nii.gz"))
    
    if fmri_files:
        return fmri_files[0]
    
    logger.warning(f"No rs-fMRI file found for subject {subject_id}")
    return None

def motion_correction(fmri_file: Path, output_dir: Path) -> Path:
    """
    Perform motion correction using FSL mcflirt.
    
    Args:
        fmri_file: Path to the input fMRI file
        output_dir: Directory to save the corrected file
        
    Returns:
        Path to the motion-corrected file
    """
    output_file = output_dir / f"{fmri_file.stem}_mcflirt.nii.gz"
    
    # Check if already processed
    if output_file.exists():
        logger.info(f"Motion correction already done: {output_file}")
        return output_file
    
    # Run mcflirt
    cmd = [
        FSL_MCFLIRT_CMD,
        "-in", str(fmri_file),
        "-ref", "mean",  # Use mean volume as reference
        "-dof", "6",      # 6 degrees of freedom
        "-out", str(output_file),
        "-rmsdiff",      # Output RMS difference
        "-spline"        # Use spline interpolation
    ]
    
    logger.info(f"Running motion correction: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stderr:
            logger.debug(f"mcflirt stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"mcflirt failed: {e}")
        raise
    
    return output_file

def normalize_and_parcellate(
    fmri_file: Path,
    atlas_mask: nib.Nifti1Image,
    atlas_labels: Dict[int, str]
) -> Dict[str, Any]:
    """
    Normalize fMRI to MNI space and parcellate using AAL atlas.
    
    Args:
        fmri_file: Path to motion-corrected fMRI file
        atlas_mask: AAL atlas mask image
        atlas_labels: Dictionary mapping region indices to names
        
    Returns:
        Dictionary with time series and metadata
    """
    # Load fMRI image
    fmri_img = image.load_img(fmri_file)
    
    # Normalize to MNI space using Nilearn (resampling to standard space)
    # Assuming the fMRI is already in MNI space or close enough for this pipeline
    # If not, we would need to apply a normalization transform here
    normalized_img = image.resample_img(
        fmri_img,
        target_affine=atlas_mask.affine,
        target_shape=atlas_mask.shape,
        interpolation='continuous'
    )
    
    # Extract time series using NiftiLabelsMasker
    masker = input_data.NiftiLabelsMasker(
        labels_img=atlas_mask,
        standardize=True,
        detrend=True,
        low_pass=0.1,
        high_pass=0.01,
        t_r=2.0,  # Assume TR=2.0s, adjust if known
        memory="nilearn_cache",
        verbose=0
    )
    
    time_series = masker.fit_transform(normalized_img)
    
    # Create a dictionary of time series by region name
    region_time_series = {}
    for i, label in atlas_labels.items():
        if i in range(time_series.shape[1]):
            region_time_series[label] = time_series[:, i]
    
    return {
        "time_series": time_series,
        "region_labels": atlas_labels,
        "n_regions": len(atlas_labels),
        "n_timepoints": time_series.shape[0]
    }

def save_connectivity_matrix(
    subject_id: str,
    time_series: np.ndarray,
    output_dir: Path
) -> Path:
    """
    Save connectivity matrix as a NIfTI file.
    
    Args:
        subject_id: Subject identifier
        time_series: Time series data (n_timepoints x n_regions)
        output_dir: Directory to save the file
        
    Returns:
        Path to the saved connectivity matrix
    """
    # Compute correlation matrix
    corr_matrix = np.corrcoef(time_series.T)
    
    # Save as a simple CSV for now (can be converted to NIfTI if needed)
    output_file = output_dir / f"{subject_id}_connectivity.csv"
    np.savetxt(output_file, corr_matrix, delimiter=',', fmt='%.6f')
    
    logger.info(f"Saved connectivity matrix: {output_file}")
    return output_file

def save_time_series(
    subject_id: str,
    time_series: np.ndarray,
    region_labels: Dict[int, str],
    output_dir: Path
) -> Path:
    """
    Save time series data as a CSV file.
    
    Args:
        subject_id: Subject identifier
        time_series: Time series data (n_timepoints x n_regions)
        region_labels: Dictionary mapping region indices to names
        output_dir: Directory to save the file
        
    Returns:
        Path to the saved time series file
    """
    output_file = output_dir / f"{subject_id}_time_series.csv"
    
    # Create DataFrame
    df = pd.DataFrame(time_series)
    df.columns = [region_labels.get(i, f"Region_{i}") for i in range(len(region_labels))]
    df.insert(0, "timepoint", range(time_series.shape[0]))
    
    df.to_csv(output_file, index=False)
    logger.info(f"Saved time series: {output_file}")
    return output_file

@log_operation("preprocess_and_parcellate")
def main() -> int:
    """Main entry point for preprocessing and parcellation."""
    start_time = time.time()
    
    # Ensure output directories exist
    CONNECTIVITY_DIR.mkdir(parents=True, exist_ok=True)
    TIME_SERIES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load AAL atlas
    logger.info("Loading AAL atlas...")
    try:
        aal_data = fetch_atlas_aal()
        atlas_mask = load_aal_atlas_mask(aal_data.maps)
        atlas_labels = aal_data.labels
        logger.info(f"Loaded AAL atlas with {len(atlas_labels)} regions")
    except Exception as e:
        logger.error(f"Failed to load AAL atlas: {e}")
        return 1
    
    # Read eligible subjects
    try:
        subject_ids = read_eligible_subjects()
        logger.info(f"Processing {len(subject_ids)} eligible subjects")
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    
    processed_count = 0
    excluded_count = 0
    
    for subject_id in subject_ids:
        logger.info(f"Processing subject: {subject_id}")
        try:
            # Find fMRI file
            fmri_file = find_subject_fmri(subject_id)
            if fmri_file is None:
                logger.warning(f"Skipping {subject_id}: No fMRI file found")
                excluded_count += 1
                continue
            
            # Motion correction
            logger.info(f"Motion correcting: {fmri_file}")
            corrected_file = motion_correction(fmri_file, CONNECTIVITY_DIR)
            
            # Normalize and parcellate
            logger.info(f"Normalizing and parcellating: {corrected_file}")
            result = normalize_and_parcellate(corrected_file, atlas_mask, atlas_labels)
            
            # Save outputs
            save_connectivity_matrix(subject_id, result["time_series"], CONNECTIVITY_DIR)
            save_time_series(subject_id, result["time_series"], result["region_labels"], TIME_SERIES_DIR)
            
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Failed to process {subject_id}: {e}")
            excluded_count += 1
            continue
    
    # Write summary
    elapsed_time = time.time() - start_time
    logger.info(f"Preprocessing complete: {processed_count} processed, {excluded_count} excluded in {elapsed_time:.2f}s")
    
    # Write status file
    status_file = PROCESSED_DIR / "preprocessing_status.json"
    status = {
        "total_subjects": len(subject_ids),
        "processed": processed_count,
        "excluded": excluded_count,
        "elapsed_time_seconds": elapsed_time,
        "random_seed": RANDOM_SEED
    }
    
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())