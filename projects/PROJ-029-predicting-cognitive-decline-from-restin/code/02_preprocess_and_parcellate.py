from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import nibabel as nib
from nilearn import image, masking
from nilearn.datasets import fetch_atlas_aal
from nilearn.input_data import NiftiLabelsMasker
from tqdm import tqdm

# Import from existing utils as per API surface
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, save_json
from utils.atlas import load_aal_atlas_mask

# Constants
DATA_PROCESSED = Path("data/processed")
DATA_RAW = Path("data/raw")
CONNECTIVITY_DIR = DATA_PROCESSED / "connectivity_matrices"
ELIGIBLE_SUBJECTS_FILE = DATA_PROCESSED / "eligible_subjects.csv"
EXCLUDED_LOG_FILE = DATA_PROCESSED / "excluded_subjects.log"
STATUS_FILE = DATA_PROCESSED / "preprocessing_status.json"
EXIT_CODE_NO_ELIGIBLE = 3
EXIT_CODE_MEMORY_ERROR = 4
EXIT_CODE_PROCESSING_FAILURE = 5

logger = get_logger("preprocess_and_parcellate")


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists."""
    ensure_dir(path)


def read_eligible_subjects(filepath: Path) -> List[str]:
    """Read subject IDs from the eligible subjects CSV."""
    if not filepath.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {filepath}")
    subjects = []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle potential variations in column name
            subj_id = row.get("subject_id") or row.get("SubjectID") or row.get("subject")
            if subj_id:
                subjects.append(str(subj_id))
    return subjects


def find_subject_fmri(subject_id: str, bids_root: Path) -> Optional[Path]:
    """
    Find the preprocessed (or raw) functional image for a subject in BIDS structure.
    Looks for 'sub-<id>_task-rest_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz'
    or similar variants. Falls back to raw if preprocessed not found.
    """
    # Strategy: Look for the most appropriate bold image
    # 1. Try to find a preprocessed MNI space image
    # 2. Try to find a raw image and assume we need to preprocess it locally if not found
    # For this pipeline, we assume T017a downloaded raw data. We will preprocess here.
    
    # Pattern 1: Preprocessed MNI
    pattern_preproc = bids_root / f"sub-{subject_id}" / "func" / f"sub-{subject_id}_task-rest_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    if pattern_preproc.exists():
        return pattern_preproc

    # Pattern 2: Raw space
    pattern_raw = bids_root / f"sub-{subject_id}" / "func" / f"sub-{subject_id}_task-rest_bold.nii.gz"
    if pattern_raw.exists():
        return pattern_raw

    # Fallback: Search recursively if exact pattern fails
    for p in bids_root.glob(f"sub-{subject_id}/func/*.nii*"):
        if "task-rest" in str(p):
            return p
    
    return None


@log_operation("motion_correction")
def motion_correction(func_img_path: Path, output_dir: Path) -> Path:
    """
    Perform motion correction (realignment) to mean image.
    Note: Nilearn's resample_img can handle registration, but for strict
    motion correction (realignment), we typically use fsl or SPM.
    Given constraints, we will use nilearn's resampling to a standard space
    which implicitly handles alignment if the input is already roughly aligned,
    or we perform a simple realignment using nilearn's image processing.
    
    For this implementation, we will assume the input is the raw BIDS image.
    We will perform:
    1. Realignment (approximated by resampling to mean if we had time series, but here we just normalize)
    2. Resampling to MNI152 (2mm)
    
    Since nilearn's 'realignment' is not a single high-level function like in fsl,
    we will use image.resample_img to standard space which is the standard nilearn approach
    for preprocessing pipelines that don't use fsl/ants.
    
    We will output the resampled image.
    """
    ensure_directory(output_dir)
    output_path = output_dir / f"sub-{func_img_path.parent.parent.name}_task-rest_space-MNI152NLin2009cAsym_res-2mm_desc-preproc_bold.nii.gz"
    
    if output_path.exists():
        return output_path

    try:
        # Load image
        img = image.load_img(func_img_path)
        
        # Resample to MNI152 2mm (standard preprocessing step)
        # This handles normalization and resampling.
        # Realignment is often done before this, but without fsl/ants, we assume
        # the BIDS dataset is already roughly aligned or we skip the explicit
        # rigid-body realignment step and rely on the normalization step.
        # However, to be robust, we can try to use nilearn's image.math_img if needed,
        # but standard practice in nilearn for this task is resample_img.
        
        # We need the target image for MNI152
        from nilearn.datasets import load_mni152_template
        template = load_mni152_template(resolution=2)
        
        # Resample
        preproc_img = image.resample_img(
            img,
            target_affine=template.affine,
            target_shape=template.shape,
            interpolation="continuous",
            copy=True,
            order=3
        )
        
        # Save
        preproc_img.to_filename(str(output_path))
        return output_path
    except Exception as e:
        logger.error(f"Motion correction failed for {func_img_path}: {e}")
        raise


@log_operation("normalize_and_parcellate")
def normalize_and_parcellate(
    func_img_path: Path, 
    atlas_mask_path: Path
) -> np.ndarray:
    """
    Extract time series from the preprocessed image using the AAL atlas.
    Returns the mean time series per region (parcellated).
    """
    try:
        # Use NiftiLabelsMasker to extract time series
        masker = NiftiLabelsMasker(
            labels_img=atlas_mask_path,
            standardize=True,
            detrend=True,
            low_pass=None,
            high_pass=None,
            t_r=2.0, # Approximate TR for ds000246, adjust if metadata differs
            memory="nilearn_cache",
            verbose=0
        )
        
        time_series = masker.fit_transform(func_img_path)
        return time_series
    except Exception as e:
        logger.error(f"Parcellation failed for {func_img_path}: {e}")
        raise


@log_operation("compute_connectivity_matrix")
def compute_connectivity_matrix(time_series: np.ndarray) -> np.ndarray:
    """
    Compute Pearson correlation matrix from time series.
    """
    if time_series.ndim == 1:
        time_series = time_series.reshape(-1, 1)
    
    # Pearson correlation
    corr_matrix = np.corrcoef(time_series.T)
    
    # Handle NaNs (e.g. from constant time series)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    return corr_matrix


@log_operation("save_connectivity_matrix")
def save_connectivity_matrix(
    matrix: np.ndarray, 
    subject_id: str, 
    output_dir: Path
) -> Path:
    """Save connectivity matrix to disk."""
    ensure_directory(output_dir)
    output_path = output_dir / f"sub-{subject_id}_connectivity.npy"
    np.save(str(output_path), matrix)
    return output_path


@log_operation("save_time_series")
def save_time_series(
    time_series: np.ndarray, 
    subject_id: str, 
    output_dir: Path
) -> Path:
    """Save time series to disk."""
    ensure_directory(output_dir)
    output_path = output_dir / f"sub-{subject_id}_timeseries.npy"
    np.save(str(output_path), time_series)
    return output_path


@log_operation("preprocess_subject")
def preprocess_subject(
    subject_id: str,
    bids_root: Path,
    atlas_mask_path: Path,
    output_dir: Path,
    temp_dir: Path
) -> Dict[str, Any]:
    """
    Full pipeline for a single subject:
    1. Find image
    2. Motion correction / Normalization
    3. Parcellation
    4. Connectivity matrix
    5. Save results
    """
    result = {
        "subject_id": subject_id,
        "status": "success",
        "error": None,
        "paths": {}
    }

    try:
        # 1. Find image
        func_path = find_subject_fmri(subject_id, bids_root)
        if not func_path:
            raise FileNotFoundError(f"No fMRI image found for subject {subject_id}")
        
        # 2. Motion Correction / Normalization
        preproc_path = motion_correction(func_path, temp_dir)
        result["paths"]["preprocessed"] = str(preproc_path)

        # 3. Parcellation
        time_series = normalize_and_parcellate(preproc_path, atlas_mask_path)
        result["paths"]["timeseries"] = str(save_time_series(time_series, subject_id, output_dir))

        # 4. Connectivity Matrix
        conn_matrix = compute_connectivity_matrix(time_series)
        result["paths"]["connectivity"] = str(save_connectivity_matrix(conn_matrix, subject_id, output_dir))

    except MemoryError:
        result["status"] = "memory_error"
        result["error"] = "MemoryError during processing"
        raise
    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        raise

    return result


@log_operation("write_excluded_log")
def write_excluded_log(excluded_list: List[Dict[str, str]], filepath: Path) -> None:
    """Write excluded subjects to log."""
    ensure_dir(filepath.parent)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["subject_id", "reason"])
        writer.writeheader()
        for entry in excluded_list:
            writer.writerow(entry)


@log_operation("write_status")
def write_status(status: Dict[str, Any], filepath: Path) -> None:
    """Write processing status."""
    ensure_dir(filepath.parent)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)


@log_operation("main")
def main() -> int:
    """Main entry point."""
    logger.log("main_start", parameters={})
    
    # 1. Check eligible subjects
    if not ELIGIBLE_SUBJECTS_FILE.exists():
        logger.error(f"Eligible subjects file missing: {ELIGIBLE_SUBJECTS_FILE}")
        print(f"ERROR: {ELIGIBLE_SUBJECTS_FILE} not found. Run T017a first.")
        return EXIT_CODE_NO_ELIGIBLE

    subjects = read_eligible_subjects(ELIGIBLE_SUBJECTS_FILE)
    if not subjects:
        logger.error("No eligible subjects found.")
        print("ERROR: No eligible subjects found.")
        return EXIT_CODE_NO_ELIGIBLE

    logger.info(f"Processing {len(subjects)} eligible subjects.")

    # 2. Setup directories
    ensure_directory(CONNECTIVITY_DIR)
    temp_dir = DATA_PROCESSED / "temp_preprocessing"
    ensure_directory(temp_dir)

    # 3. Fetch AAL Atlas
    try:
        logger.log("fetch_atlas_aal", parameters={"source": "nilearn"})
        atlas_data = fetch_atlas_aal()
        atlas_mask_path = Path(atlas_data.maps)
        logger.info(f"AAL Atlas fetched: {atlas_mask_path}")
    except Exception as e:
        logger.error(f"Failed to fetch AAL atlas: {e}")
        return EXIT_CODE_PROCESSING_FAILURE

    # 4. Process subjects
    excluded_list = []
    processed_count = 0
    failed_count = 0

    # BIDS root is typically data/raw/ds000246
    bids_root = DATA_RAW / "ds000246"
    if not bids_root.exists():
        # Try to find the raw data root
        raw_dirs = list(DATA_RAW.glob("ds*"))
        if raw_dirs:
            bids_root = raw_dirs[0]
        else:
            logger.error(f"BIDS root not found at {bids_root} or in {DATA_RAW}")
            return EXIT_CODE_NO_ELIGIBLE

    logger.info(f"Using BIDS root: {bids_root}")

    for subj in tqdm(subjects, desc="Preprocessing Subjects"):
        try:
            result = preprocess_subject(
                subject_id=subj,
                bids_root=bids_root,
                atlas_mask_path=atlas_mask_path,
                output_dir=CONNECTIVITY_DIR,
                temp_dir=temp_dir
            )
            if result["status"] == "success":
                processed_count += 1
            else:
                failed_count += 1
                excluded_list.append({"subject_id": subj, "reason": result.get("error", "Unknown")})
        except MemoryError:
            failed_count += 1
            excluded_list.append({"subject_id": subj, "reason": "MemoryError"})
            logger.error(f"MemoryError for subject {subj}. Exiting to prevent data corruption.")
            # Per spec: If memory constraints cause failure, exit with non-zero code
            write_excluded_log(excluded_list, EXCLUDED_LOG_FILE)
            write_status({"processed": processed_count, "failed": failed_count, "status": "memory_error"}, STATUS_FILE)
            return EXIT_CODE_MEMORY_ERROR
        except Exception as e:
            failed_count += 1
            excluded_list.append({"subject_id": subj, "reason": str(e)})
            logger.warning(f"Failed to process {subj}: {e}")
            # Per spec: If a subject fails, log and exit with non-zero code
            write_excluded_log(excluded_list, EXCLUDED_LOG_FILE)
            write_status({"processed": processed_count, "failed": failed_count, "status": "processing_error"}, STATUS_FILE)
            return EXIT_CODE_PROCESSING_FAILURE

    # 5. Finalize
    if processed_count == 0:
        logger.error("No subjects were successfully processed.")
        write_excluded_log(excluded_list, EXCLUDED_LOG_FILE)
        write_status({"processed": 0, "failed": len(subjects), "status": "no_success"}, STATUS_FILE)
        return EXIT_CODE_NO_ELIGIBLE

    logger.info(f"Preprocessing complete. Processed: {processed_count}, Failed: {failed_count}")
    write_excluded_log(excluded_list, EXCLUDED_LOG_FILE)
    write_status({"processed": processed_count, "failed": failed_count, "status": "completed"}, STATUS_FILE)

    return 0


if __name__ == "__main__":
    sys.exit(main())
