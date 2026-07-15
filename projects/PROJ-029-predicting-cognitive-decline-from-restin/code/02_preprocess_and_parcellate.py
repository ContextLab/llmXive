"""
02_preprocess_and_parcellate.py

Loads raw BIDS data for eligible subjects, performs motion correction (FSL mcflirt),
normalization (nilearn), applies the AAL atlas, and computes connectivity matrices.
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import nibabel as nib
import numpy as np
from nilearn import image, masking
from nilearn.input_data import NiftiLabelsMasker
from nilearn.datasets import fetch_atlas_aal

# Import project utilities
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir
from utils.atlas import load_aal_atlas_mask, create_minimal_atlas, validate_atlas_shape

logger = get_logger("preprocess_and_parcellate")

# Constants
DATA_PROCESSED_DIR = Path("data/processed")
CONNECTIVITY_DIR = DATA_PROCESSED_DIR / "connectivity_matrices"
ELIGIBLE_SUBJECTS_FILE = DATA_PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_LOG_FILE = DATA_PROCESSED_DIR / "excluded_preprocess.log"
STATUS_FILE = DATA_PROCESSED_DIR / "preprocess_status.json"

# FSL mcflirt parameters
FSL_MCFLIRT_REF = "mean"  # Use mean image as reference
FSL_MCFLIRT_DOF = 6


def read_eligible_subjects(filepath: Path = ELIGIBLE_SUBJECTS_FILE) -> List[Dict[str, str]]:
    """Read the eligible subjects CSV file."""
    subjects = []
    if not filepath.exists():
        logger.log("read_eligible_subjects", error=f"File not found: {filepath}")
        return subjects

    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            subjects.append(row)
    return subjects


def find_subject_fmri(subject_dir: Path) -> Optional[Path]:
    """
    Find the preprocessed (or raw) rs-fMRI NIfTI file for a subject.
    Looks for files matching pattern: sub-*/func/*task-rest_bold.nii.gz
    """
    func_dir = subject_dir / "func"
    if not func_dir.exists():
        return None

    # Look for task-rest_bold files
    for f in func_dir.glob("sub-*_task-rest_bold.nii.gz"):
        return f
    for f in func_dir.glob("sub-*_task-rest_bold.nii"):
        return f
    
    # Fallback: any bold file if task-rest not found
    for f in func_dir.glob("sub-*_bold.nii.gz"):
        return f
    for f in func_dir.glob("sub-*_bold.nii"):
        return f

    return None


@log_operation("motion_correction")
def motion_correction(input_nii: Path, output_dir: Path) -> Optional[Path]:
    """
    Perform motion correction using FSL mcflirt.
    Returns path to corrected image, or None if failed.
    """
    ensure_dir(output_dir)
    output_file = output_dir / f"{input_nii.stem}_mc.nii.gz"
    
    # Check if FSL is available
    try:
        result = subprocess.run(
            ["which", "mcflirt"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            logger.log("motion_correction", 
                       warning="FSL mcflirt not found in PATH. Skipping motion correction.",
                       input=str(input_nii))
            # Return original if FSL not available
            return input_nii
    except Exception as e:
        logger.log("motion_correction", 
                   warning=f"Error checking FSL: {e}. Skipping motion correction.",
                   input=str(input_nii))
        return input_nii

    # Run mcflirt
    try:
        cmd = [
            "mcflirt",
            "-in", str(input_nii),
            "-out", str(output_file),
            "-ref", FSL_MCFLIRT_REF,
            "-dof", str(FSL_MCFLIRT_DOF),
            "-plots"
        ]
        logger.log("motion_correction", 
                   command=" ".join(cmd),
                   input=str(input_nii),
                   output=str(output_file))
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return output_file
        else:
            logger.log("motion_correction", 
                       error=f"mcflirt failed: {result.stderr}",
                       input=str(input_nii))
            return input_nii
    except subprocess.TimeoutExpired:
        logger.log("motion_correction", 
                   error="mcflirt timed out",
                   input=str(input_nii))
        return input_nii
    except Exception as e:
        logger.log("motion_correction", 
                   error=f"Unexpected error: {e}",
                   input=str(input_nii))
        return input_nii


@log_operation("normalize_and_parcellate")
def normalize_and_parcellate(
    input_nii: Path, 
    output_dir: Path,
    atlas_mask: Optional[nib.Nifti1Image] = None
) -> Optional[Dict[str, Any]]:
    """
    Normalize image to MNI space and extract time series using AAL atlas.
    Returns a dictionary with time_series and matrix info.
    """
    ensure_dir(output_dir)
    
    # Load atlas if not provided
    if atlas_mask is None:
        try:
            atlas_data = fetch_atlas_aal()
            atlas_mask_path = Path(atlas_data.maps)
            atlas_mask = nib.load(atlas_mask_path)
            logger.log("normalize_and_parcellate", 
                       info=f"Loaded AAL atlas from {atlas_mask_path}")
        except Exception as e:
            logger.log("normalize_and_parcellate", 
                       error=f"Failed to load AAL atlas: {e}")
            return None

    # Normalize to MNI space (using nilearn)
    try:
        logger.log("normalize_and_parcellate", 
                   info="Normalizing to MNI space",
                   input=str(input_nii))
        normalized_img = image.resample_to_img(
            input_nii, 
            atlas_mask, 
            interpolation="continuous"
        )
    except Exception as e:
        logger.log("normalize_and_parcellate", 
                   error=f"Normalization failed: {e}",
                   input=str(input_nii))
        return None

    # Extract time series using masker
    try:
        masker = NiftiLabelsMasker(
            labels_img=atlas_mask,
            standardize=True,
            detrend=True,
            low_pass=0.1,
            high_pass=0.01,
            t_r=2.0,  # Default TR, adjust if metadata available
            memory="nilearn_cache",
            verbose=0
        )
        
        logger.log("normalize_and_parcellate", 
                   info="Extracting time series",
                   regions=atlas_mask.shape)
        
        time_series = masker.fit_transform(normalized_img)
        
        if time_series is None or len(time_series) == 0:
            logger.log("normalize_and_parcellate", 
                       error="Time series extraction returned empty result")
            return None
            
        return {
            "time_series": time_series,
            "n_regions": time_series.shape[1],
            "n_timepoints": time_series.shape[0]
        }
    except Exception as e:
        logger.log("normalize_and_parcellate", 
                   error=f"Time series extraction failed: {e}")
        return None


@log_operation("save_connectivity_matrix")
def save_connectivity_matrix(
    subject_id: str,
    time_series: np.ndarray,
    output_dir: Path
) -> Optional[Path]:
    """
    Compute correlation matrix from time series and save to disk.
    """
    ensure_dir(output_dir)
    output_file = output_dir / f"{subject_id}_connectivity.npy"
    
    try:
        # Compute correlation matrix
        if time_series.shape[0] < 2:
            logger.log("save_connectivity_matrix", 
                       error="Insufficient timepoints for correlation",
                       subject=subject_id)
            return None
        
        corr_matrix = np.corrcoef(time_series, rowvar=False)
        
        # Handle NaN/Inf
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0, posinf=1.0, neginf=-1.0)
        
        np.save(output_file, corr_matrix)
        logger.log("save_connectivity_matrix", 
                   info="Saved connectivity matrix",
                   subject=subject_id,
                   shape=corr_matrix.shape)
        return output_file
    except Exception as e:
        logger.log("save_connectivity_matrix", 
                   error=f"Failed to save matrix: {e}",
                   subject=subject_id)
        return None


@log_operation("save_time_series")
def save_time_series(
    subject_id: str,
    time_series: np.ndarray,
    output_dir: Path
) -> Optional[Path]:
    """Save the extracted time series for debugging/analysis."""
    ensure_dir(output_dir)
    output_file = output_dir / f"{subject_id}_timeseries.npy"
    
    try:
        np.save(output_file, time_series)
        logger.log("save_time_series", 
                   info="Saved time series",
                   subject=subject_id,
                   shape=time_series.shape)
        return output_file
    except Exception as e:
        logger.log("save_time_series", 
                   error=f"Failed to save time series: {e}",
                   subject=subject_id)
        return None


def write_status(
    processed: int,
    excluded: int,
    status_file: Path = STATUS_FILE
) -> None:
    """Write processing status to JSON."""
    ensure_dir(status_file.parent)
    status = {
        "processed": processed,
        "excluded": excluded,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)
    logger.log("write_status", info="Wrote status file", path=str(status_file))


def write_excluded_log(
    excluded_subjects: List[Dict[str, str]],
    log_file: Path = EXCLUDED_LOG_FILE
) -> None:
    """Write log of excluded subjects."""
    ensure_dir(log_file.parent)
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("# Excluded Subjects Log\n")
        f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for subj in excluded_subjects:
            f.write(f"Subject: {subj.get('subject_id', 'unknown')}\n")
            f.write(f"  Reason: {subj.get('reason', 'unknown')}\n")
            f.write(f"  File: {subj.get('file', 'unknown')}\n\n")
    logger.log("write_excluded_log", info="Wrote excluded log", path=str(log_file))


@log_operation("preprocess_subject")
def preprocess_subject(
    subject: Dict[str, str],
    data_dir: Path,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Full preprocessing pipeline for a single subject.
    Returns result dict with status and paths.
    """
    subject_id = subject.get("subject_id", "unknown")
    result = {
        "subject_id": subject_id,
        "status": "pending",
        "input_file": None,
        "mc_file": None,
        "connectivity_file": None,
        "timeseries_file": None,
        "error": None
    }
    
    # Find fMRI file
    subject_dir = data_dir / subject_id
    fmri_file = find_subject_fmri(subject_dir)
    
    if fmri_file is None:
        result["status"] = "excluded_no_fmri"
        result["error"] = "No fMRI file found"
        return result
    
    result["input_file"] = str(fmri_file)
    
    # Motion correction
    mc_dir = output_dir / subject_id / "mc"
    mc_file = motion_correction(fmri_file, mc_dir)
    
    if mc_file is None:
        result["status"] = "excluded_mc_failed"
        result["error"] = "Motion correction failed"
        return result
    
    result["mc_file"] = str(mc_file)
    
    # Normalize and parcellate
    parcellate_dir = output_dir / subject_id / "parcellate"
    ts_result = normalize_and_parcellate(mc_file, parcellate_dir)
    
    if ts_result is None:
        result["status"] = "excluded_parcellate_failed"
        result["error"] = "Normalization/Parcellation failed"
        return result
    
    # Save connectivity matrix
    conn_dir = output_dir / subject_id / "connectivity"
    conn_file = save_connectivity_matrix(
        subject_id, 
        ts_result["time_series"], 
        conn_dir
    )
    
    if conn_file is None:
        result["status"] = "excluded_save_failed"
        result["error"] = "Failed to save connectivity matrix"
        return result
    
    result["connectivity_file"] = str(conn_file)
    result["status"] = "success"
    
    # Save time series for debugging
    ts_file = save_time_series(
        subject_id,
        ts_result["time_series"],
        conn_dir
    )
    if ts_file:
        result["timeseries_file"] = str(ts_file)
    
    return result


@log_operation("main")
def main() -> int:
    """Main entry point."""
    start_time = time.time()
    logger.log("main", info="Starting preprocessing pipeline")
    
    # Check for eligible subjects file
    if not ELIGIBLE_SUBJECTS_FILE.exists():
        logger.log("main", error=f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_FILE}")
        return 1
    
    # Load eligible subjects
    subjects = read_eligible_subjects()
    if not subjects:
        logger.log("main", error="No eligible subjects found")
        return 1
    
    logger.log("main", info=f"Processing {len(subjects)} eligible subjects")
    
    # Ensure output directories
    ensure_dir(CONNECTIVITY_DIR)
    
    # Determine data root (assuming raw data is in data/raw/ds000246)
    data_root = Path("data/raw/ds000246")
    if not data_root.exists():
        logger.log("main", error=f"Data root not found: {data_root}")
        return 1
    
    processed_count = 0
    excluded_count = 0
    excluded_subjects = []
    
    for subject in subjects:
        subject_id = subject.get("subject_id", "unknown")
        logger.log("main", info=f"Processing subject: {subject_id}")
        
        result = preprocess_subject(subject, data_root, CONNECTIVITY_DIR)
        
        if result["status"] == "success":
            processed_count += 1
            logger.log("main", info=f"Successfully processed: {subject_id}")
        else:
            excluded_count += 1
            excluded_subjects.append({
                "subject_id": subject_id,
                "reason": result.get("error", "Unknown error"),
                "file": result.get("input_file", "N/A")
            })
            logger.log("main", warning=f"Excluded subject {subject_id}: {result.get('error')}")
    
    # Write outputs
    write_status(processed_count, excluded_count)
    write_excluded_log(excluded_subjects)
    
    elapsed = time.time() - start_time
    logger.log("main", 
               info="Pipeline complete",
               processed=processed_count,
               excluded=excluded_count,
               elapsed_seconds=elapsed)
    
    print(f"Preprocessing complete: {processed_count} processed, {excluded_count} excluded")
    print(f"Output directory: {CONNECTIVITY_DIR}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
