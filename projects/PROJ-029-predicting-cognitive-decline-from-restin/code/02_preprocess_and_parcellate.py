"""
Task T018: Preprocess rs-fMRI data and generate connectivity matrices.

This script performs:
1. Motion correction using FSL's mcflirt
2. Normalization to MNI space using nilearn
3. Parcellation using the AAL atlas (90 regions)
4. Extraction of 90x90 connectivity matrices for each subject

Output: data/processed/connectivity_matrices/ directory containing .npy files.
"""
import os
import sys
import subprocess
import time
import shutil
import logging
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Optional, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger
from utils.io import ensure_dir, load_bids_subject_data
from utils.atlas import load_aal_atlas_mask, validate_atlas_shape
from config import get_config

# --- Configuration ---
CONFIG = get_config()
RANDOM_SEED = CONFIG.get('random_seed', 42)
DATA_RAW_DIR = Path(CONFIG.get('data_raw_dir', 'data/raw'))
DATA_PROCESSED_DIR = Path(CONFIG.get('data_processed_dir', 'data/processed'))
CONNECTIVITY_DIR = DATA_PROCESSED_DIR / 'connectivity_matrices'
ELIGIBLE_SUBJECTS_FILE = DATA_PROCESSED_DIR / 'eligible_subjects.csv'

# FSL path configuration - typically set in environment or config
FSL_DIR = os.environ.get('FSLDIR', '/usr/share/fsl')
if FSL_DIR:
    os.environ['PATH'] = f"{FSL_DIR}/bin:{os.environ.get('PATH', '')}"

logger = get_logger('preprocess_parcellate')

def get_logger_wrapper(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)

def run_command(cmd: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """
    Run a shell command and return exit code, stdout, stderr.
    
    Args:
        cmd: Command as a list of strings
        cwd: Working directory
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return 1, "", str(e)

def perform_motion_correction(nifti_path: Path, output_dir: Path) -> Optional[Path]:
    """
    Perform motion correction using FSL's mcflirt.
    
    Args:
        nifti_path: Path to input 4D NIfTI file
        output_dir: Directory to save corrected output
        
    Returns:
        Path to corrected NIfTI file, or None if failed
    """
    if not nifti_path.exists():
        logger.error(f"Input file not found: {nifti_path}")
        return None
        
    base_name = nifti_path.stem
    output_path = output_dir / f"{base_name}_mcflirt.nii.gz"
    
    cmd = [
        'mcflirt',
        '-in', str(nifti_path),
        '-out', str(output_path),
        '-refvol', '0',
        '-sinc',
        '-mats',
        '-rmsrel', '0.1',
        '-rmsabs', '0.2'
    ]
    
    logger.info(f"Running motion correction for {base_name}...")
    start_time = time.time()
    return_code, stdout, stderr = run_command(cmd)
    elapsed = time.time() - start_time
    
    if return_code != 0:
        logger.error(f"mcflirt failed for {base_name}: {stderr}")
        return None
        
    if not output_path.exists():
        logger.error(f"mcflirt output not found: {output_path}")
        return None
        
    logger.info(f"Motion correction completed in {elapsed:.2f}s: {output_path}")
    return output_path

def normalize_to_mni(nifti_path: Path, output_dir: Path) -> Optional[Path]:
    """
    Normalize to MNI space using nilearn's resampling.
    
    Note: Since we don't have structural images for all subjects in this dataset,
    we use affine transformation to MNI152 space as a proxy.
    
    Args:
        nifti_path: Path to motion-corrected NIfTI
        output_dir: Directory to save normalized output
        
    Returns:
        Path to normalized NIfTI file, or None if failed
    """
    if not nifti_path.exists():
        logger.error(f"Input file not found: {nifti_path}")
        return None
        
    from nilearn import image
    from nilearn.image import resample_to_img
    from nilearn.datasets import load_mni152_template
    
    base_name = nifti_path.stem
    output_path = output_dir / f"{base_name}_mni.nii.gz"
    
    try:
        logger.info(f"Normalizing to MNI space for {base_name}...")
        start_time = time.time()
        
        # Load the functional image
        func_img = image.load_img(nifti_path)
        
        # Load MNI152 template
        mni_img = load_mni152_template()
        
        # Resample functional to MNI space (2mm isotropic)
        # Using resample_to_img which handles the transformation
        normalized_img = resample_to_img(
            func_img, 
            mni_img, 
            interpolation='continuous',
            copy_header=True
        )
        
        # Save the result
        image.save_img(normalized_img, output_path)
        
        elapsed = time.time() - start_time
        logger.info(f"Normalization completed in {elapsed:.2f}s: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Normalization failed for {base_name}: {e}")
        return None

def extract_timeseries_from_atlas(nifti_path: Path, atlas_mask_path: Path) -> Optional[np.ndarray]:
    """
    Extract mean time series from each atlas region.
    
    Args:
        nifti_path: Path to normalized NIfTI file
        atlas_mask_path: Path to AAL atlas mask
        
    Returns:
        2D array of shape (n_timepoints, n_regions), or None if failed
    """
    if not nifti_path.exists():
        logger.error(f"Functional image not found: {nifti_path}")
        return None
    if not atlas_mask_path.exists():
        logger.error(f"Atlas mask not found: {atlas_mask_path}")
        return None
        
    from nilearn.input_data import NiftiLabelsMasker
    
    base_name = nifti_path.stem
    
    try:
        logger.info(f"Extracting timeseries for {base_name}...")
        start_time = time.time()
        
        # Load the atlas mask
        atlas_img = nib.load(atlas_mask_path)
        
        # Create masker
        masker = NiftiLabelsMasker(
            labels_img=atlas_img,
            standardize=True,
            detrend=True,
            low_pass=0.1,
            high_pass=0.01,
            t_r=2.0,  # Approximate TR for this dataset
            memory='nilearn_cache',
            memory_level=1,
            verbose=0
        )
        
        # Extract timeseries
        timeseries = masker.fit_transform(nifti_path)
        
        elapsed = time.time() - start_time
        logger.info(f"Timeseries extraction completed in {elapsed:.2f}s: shape {timeseries.shape}")
        return timeseries
        
    except Exception as e:
        logger.error(f"Timeseries extraction failed for {base_name}: {e}")
        return None

def compute_connectivity_matrix(timeseries: np.ndarray) -> np.ndarray:
    """
    Compute Pearson correlation matrix from timeseries.
    
    Args:
        timeseries: 2D array of shape (n_timepoints, n_regions)
        
    Returns:
        2D correlation matrix of shape (n_regions, n_regions)
    """
    from scipy.stats import pearsonr
    
    n_regions = timeseries.shape[1]
    corr_matrix = np.zeros((n_regions, n_regions))
    
    # Compute correlation for each pair
    for i in range(n_regions):
        for j in range(i, n_regions):
            if i == j:
                corr_matrix[i, j] = 1.0
            else:
                # Compute Pearson correlation
                corr, _ = pearsonr(timeseries[:, i], timeseries[:, j])
                corr_matrix[i, j] = corr
                corr_matrix[j, i] = corr
                
    return corr_matrix

def process_subject(subject_id: str, bids_data_dir: Path, temp_dir: Path) -> Optional[np.ndarray]:
    """
    Process a single subject: motion correction -> normalization -> parcellation.
    
    Args:
        subject_id: Subject identifier
        bids_data_dir: Path to BIDS dataset root
        temp_dir: Directory for intermediate files
        
    Returns:
        Connectivity matrix (90x90), or None if failed
    """
    # Load AAL atlas (load once per subject to avoid repeated I/O)
    atlas_mask_path = load_aal_atlas_mask()
    if not atlas_mask_path:
        logger.error("Failed to load AAL atlas mask")
        return None
        
    # Find functional image for this subject
    func_files = list(bids_data_dir.glob(f"sub-{subject_id}/**/func/*task-rest*bold.nii.gz"))
    if not func_files:
        logger.warning(f"No resting-state fMRI found for subject {subject_id}")
        return None
        
    func_path = func_files[0]
    logger.info(f"Processing subject {subject_id} with file: {func_path}")
    
    # Create subject-specific temp directory
    subject_temp_dir = temp_dir / subject_id
    ensure_dir(subject_temp_dir)
    
    # Step 1: Motion correction
    mc_path = perform_motion_correction(func_path, subject_temp_dir)
    if not mc_path:
        logger.error(f"Motion correction failed for {subject_id}")
        return None
        
    # Step 2: Normalization to MNI
    mni_path = normalize_to_mni(mc_path, subject_temp_dir)
    if not mni_path:
        logger.error(f"Normalization failed for {subject_id}")
        return None
        
    # Step 3: Extract timeseries using AAL atlas
    timeseries = extract_timeseries_from_atlas(mni_path, atlas_mask_path)
    if timeseries is None:
        logger.error(f"Timeseries extraction failed for {subject_id}")
        return None
        
    # Step 4: Compute connectivity matrix
    corr_matrix = compute_connectivity_matrix(timeseries)
    
    logger.info(f"Successfully processed subject {subject_id}: {corr_matrix.shape}")
    return corr_matrix

def write_outputs(subject_id: str, corr_matrix: np.ndarray, output_dir: Path) -> bool:
    """
    Save connectivity matrix to disk.
    
    Args:
        subject_id: Subject identifier
        corr_matrix: 90x90 correlation matrix
        output_dir: Output directory
        
    Returns:
        True if successful, False otherwise
    """
    ensure_dir(output_dir)
    output_path = output_dir / f"sub-{subject_id}_connectivity.npy"
    
    try:
        np.save(output_path, corr_matrix)
        logger.info(f"Saved connectivity matrix for {subject_id} to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save connectivity matrix for {subject_id}: {e}")
        return False

def load_eligible_subjects(file_path: Path) -> List[str]:
    """
    Load list of eligible subjects from CSV.
    
    Args:
        file_path: Path to eligible_subjects.csv
        
    Returns:
        List of subject IDs
    """
    import pandas as pd
    
    if not file_path.exists():
        logger.error(f"Eligible subjects file not found: {file_path}")
        return []
        
    try:
        df = pd.read_csv(file_path)
        if 'subject_id' not in df.columns:
            logger.error(f"'subject_id' column not found in {file_path}")
            return []
            
        subjects = df['subject_id'].tolist()
        logger.info(f"Loaded {len(subjects)} eligible subjects from {file_path}")
        return subjects
    except Exception as e:
        logger.error(f"Failed to load eligible subjects: {e}")
        return []

def main():
    """Main entry point for preprocessing and parcellation."""
    logger.info("Starting preprocessing and parcellation pipeline (T018)")
    start_time = time.time()
    
    # Ensure output directory exists
    ensure_dir(CONNECTIVITY_DIR)
    
    # Load eligible subjects
    if not ELIGIBLE_SUBJECTS_FILE.exists():
        logger.error(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_FILE}")
        logger.error("Please run code/01_download_and_filter.py first to generate eligible_subjects.csv")
        sys.exit(1)
        
    subjects = load_eligible_subjects(ELIGIBLE_SUBJECTS_FILE)
    if not subjects:
        logger.error("No eligible subjects found. Exiting.")
        sys.exit(1)
        
    # Create temporary directory for intermediate files
    temp_dir = DATA_PROCESSED_DIR / 'temp_preprocessing'
    ensure_dir(temp_dir)
    
    processed_count = 0
    failed_count = 0
    
    for subject_id in subjects:
        try:
            corr_matrix = process_subject(subject_id, DATA_RAW_DIR, temp_dir)
            if corr_matrix is not None:
                if write_outputs(subject_id, corr_matrix, CONNECTIVITY_DIR):
                    processed_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            logger.error(f"Unexpected error processing {subject_id}: {e}")
            failed_count += 1
    
    # Clean up temporary files
    try:
        shutil.rmtree(temp_dir)
        logger.info("Cleaned up temporary directory")
    except Exception as e:
        logger.warning(f"Failed to clean up temporary directory: {e}")
    
    elapsed = time.time() - start_time
    logger.info(f"Pipeline completed in {elapsed:.2f}s")
    logger.info(f"Successfully processed: {processed_count}/{len(subjects)} subjects")
    if failed_count > 0:
        logger.warning(f"Failed to process: {failed_count} subjects")
        
    # Write a summary log
    summary_path = CONNECTIVITY_DIR / 'processing_summary.json'
    import json
    summary = {
        'total_subjects': len(subjects),
        'processed': processed_count,
        'failed': failed_count,
        'elapsed_seconds': elapsed,
        'output_directory': str(CONNECTIVITY_DIR)
    }
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Summary written to {summary_path}")
    
    if processed_count == 0:
        logger.error("No subjects were successfully processed. Exiting with error.")
        sys.exit(1)
        
    logger.info("Preprocessing and parcellation pipeline completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())