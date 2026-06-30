"""
T018: Preprocess and Parcellate rs-fMRI Data

This script performs:
1. Motion correction using FSL mcflirt
2. Normalization using Nilearn
3. Application of 90-region AAL atlas
4. Generation of 90x90 connectivity matrices per subject

Outputs:
- data/processed/parcellated_matrices/ directory containing .npy files
- data/processed/preprocessing_log.csv containing status for each subject
"""
import os
import sys
import subprocess
import time
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import nibabel as nib
from nilearn import image, masking, datasets
from nilearn.regions import signal_extraction
from utils.logger import get_logger
from utils.io import ensure_dir, load_json, save_csv
from utils.graph import load_aal_atlas_mask
from config import get_config

# Ensure we can import from the code directory
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

def run_command(cmd, description="Command"):
    """Run a shell command and log output."""
    logger = get_logger("preprocess")
    logger.info(f"Running: {description}")
    logger.debug(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            check=True, 
            text=True
        )
        if result.stdout:
            logger.debug(f"Output: {result.stdout[:500]}...")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {description}")
        logger.error(f"stderr: {e.stderr}")
        return False

def perform_motion_correction(nifti_path, output_dir):
    """Perform motion correction using FSL mcflirt."""
    logger = get_logger("preprocess")
    output_path = output_dir / f"{nifti_path.stem}_mc.nii.gz"
    
    # Check if FSL is available
    if not shutil.which("mcflirt"):
        logger.warning("FSL mcflirt not found in PATH. Skipping motion correction.")
        # Return original file if FSL not available
        return nifti_path, False
    
    cmd = [
        "mcflirt",
        "-in", str(nifti_path),
        "-out", str(output_path),
        "-refvol", "0",  # Use first volume as reference
        "-plots",
        "-dof", "6"
    ]
    
    success = run_command(cmd, "Motion correction with mcflirt")
    if success and output_path.exists():
        return output_path, True
    
    logger.warning("Motion correction failed or output missing. Using original file.")
    return nifti_path, False

def normalize_to_mni(nifti_path, output_dir):
    """Normalize image to MNI space using Nilearn."""
    logger = get_logger("preprocess")
    output_path = output_dir / f"{nifti_path.stem}_norm.nii.gz"
    
    try:
        # Load image
        img = image.load_img(nifti_path)
        
        # Normalize to MNI space using standard template
        # Using MNI152NLin2009cAsym as it's commonly available
        normalized_img = image.resample_to_img(
            img, 
            target_img=datasets.load_mni152_template(),
            interpolation="continuous"
        )
        
        # Save normalized image
        normalized_img.to_filename(str(output_path))
        logger.info(f"Normalized image saved to {output_path}")
        return output_path, True
        
    except Exception as e:
        logger.error(f"Normalization failed: {str(e)}")
        return nifti_path, False

def extract_timeseries_from_atlas(nifti_path, atlas_mask_path, output_dir, subject_id):
    """Extract mean timeseries from each atlas region."""
    logger = get_logger("preprocess")
    
    try:
        # Load the normalized functional image
        func_img = image.load_img(nifti_path)
        
        # Load the atlas mask
        atlas_img = image.load_img(atlas_mask_path)
        
        # Extract signals from each region
        # This returns a 2D array: (n_timepoints, n_regions)
        signals = masking.apply_mask(
            func_img, 
            atlas_img
        )
        
        # If we have a label image (with region IDs), we need to extract mean per region
        # For AAL, we typically have a label image where each voxel has a region ID
        if hasattr(atlas_img, 'get_fdata') and len(np.unique(atlas_img.get_fdata())) > 2:
            # It's a label image, extract mean signal per label
            from nilearn import regions
            signals = regions.region_signals(
                regions=atlas_img,
                imgs=func_img,
                mask=None,
                allow_overlap=False
            )[0]  # region_signals returns a list, we want the first element
        
        # Save the timeseries
        timeseries_path = output_dir / f"subject_{subject_id}_timeseries.npy"
        np.save(str(timeseries_path), signals)
        
        # Also save connectivity matrix (correlation between regions)
        if signals.shape[0] > 1:  # Need at least 2 time points
            # Compute correlation matrix
            corr_matrix = np.corrcoef(signals.T)
            # Handle NaN values (from constant signals)
            corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
            
            matrix_path = output_dir / f"subject_{subject_id}_connectivity.npy"
            np.save(str(matrix_path), corr_matrix)
            
            logger.info(f"Extracted timeseries and computed connectivity for subject {subject_id}")
            return True, signals.shape
        else:
            logger.warning(f"Insufficient time points for subject {subject_id}")
            return False, signals.shape
            
    except Exception as e:
        logger.error(f"Timeseries extraction failed for subject {subject_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None

def main():
    """Main preprocessing pipeline."""
    logger = get_logger("preprocess")
    config = get_config()
    
    # Define paths
    raw_data_dir = Path(config["data"]["raw"]) / "ds000246"
    processed_dir = Path(config["data"]["processed"])
    parcellated_dir = processed_dir / "parcellated_matrices"
    temp_dir = processed_dir / "temp_preprocessing"
    
    ensure_dir(parcellated_dir)
    ensure_dir(temp_dir)
    
    # Load eligible subjects from previous task
    eligible_subjects_path = processed_dir / "eligible_subjects.csv"
    if not eligible_subjects_path.exists():
        logger.error(f"Eligible subjects file not found: {eligible_subjects_path}")
        logger.error("Please run 01_download_and_filter.py first")
        sys.exit(1)
    
    eligible_df = pd.read_csv(eligible_subjects_path)
    logger.info(f"Processing {len(eligible_df)} eligible subjects")
    
    # Load AAL atlas
    logger.info("Loading AAL atlas")
    try:
        # Try to load AAL atlas from nilearn or use a custom path
        # AAL is not included by default in nilearn, so we need to handle this
        atlas_mask_path = config.get("atlas", {}).get("aal_path")
        
        if atlas_mask_path and Path(atlas_mask_path).exists():
            logger.info(f"Using AAL atlas from: {atlas_mask_path}")
            atlas_img = image.load_img(atlas_mask_path)
        else:
            # Try to download or use a default AAL atlas
            logger.warning("AAL atlas path not configured. Attempting to use nilearn's built-in atlas...")
            # Fallback: use a standard MNI template and create a simple parcellation
            # In production, you should have the AAL atlas file
            logger.error("AAL atlas file not found. Please configure atlas path in config or download AAL atlas.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to load AAL atlas: {str(e)}")
        sys.exit(1)
    
    # Process each subject
    results = []
    total_subjects = len(eligible_df)
    
    for idx, row in eligible_df.iterrows():
        subject_id = row["subject_id"]
        logger.info(f"Processing subject {idx+1}/{total_subjects}: {subject_id}")
        
        # Find the functional image for this subject
        # Assuming BIDS structure: sub-<label>/func/sub-<label>_task-rest_bold.nii.gz
        func_pattern = raw_data_dir / f"sub-{subject_id}" / "func" / f"sub-{subject_id}_task-rest_bold.nii.gz"
        
        if not func_pattern.exists():
            # Try alternative patterns
            func_pattern = raw_data_dir / f"sub-{subject_id}" / "func" / f"sub-{subject_id}_task-rest_bold.nii"
            if not func_pattern.exists():
                logger.warning(f"Functional image not found for subject {subject_id}")
                results.append({
                    "subject_id": subject_id,
                    "status": "missing_func",
                    "motion_corrected": False,
                    "normalized": False,
                    "timeseries_extracted": False,
                    "error": "Functional image not found"
                })
                continue
        
        # Step 1: Motion correction
        mc_result, mc_success = perform_motion_correction(func_pattern, temp_dir)
        
        # Step 2: Normalization
        norm_result, norm_success = normalize_to_mni(mc_result, temp_dir)
        
        # Step 3: Extract timeseries and compute connectivity
        extract_success, shape_info = extract_timeseries_from_atlas(
            norm_result, 
            atlas_mask_path, 
            parcellated_dir, 
            subject_id
        )
        
        results.append({
            "subject_id": subject_id,
            "status": "success" if extract_success else "failed",
            "motion_corrected": mc_success,
            "normalized": norm_success,
            "timeseries_extracted": extract_success,
            "timeseries_shape": str(shape_info) if shape_info else None,
            "error": None if extract_success else "Timeseries extraction failed"
        })
    
    # Save processing log
    log_df = pd.DataFrame(results)
    log_path = processed_dir / "preprocessing_log.csv"
    save_csv(log_df, log_path)
    logger.info(f"Processing log saved to {log_path}")
    
    # Summary
    successful = sum(1 for r in results if r["status"] == "success")
    logger.info(f"Preprocessing completed: {successful}/{total_subjects} subjects successfully processed")
    
    if successful == 0:
        logger.error("No subjects were successfully processed!")
        sys.exit(1)
    
    return successful

if __name__ == "__main__":
    main()
