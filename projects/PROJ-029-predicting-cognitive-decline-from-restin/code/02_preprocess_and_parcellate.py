"""
T018: Preprocess and Parcellate Resting-State fMRI Data

This script loads raw BIDS data, performs motion correction using FSL (mcflirt),
normalizes to MNI space using Nilearn, applies the 90-region AAL atlas, and
generates 90x90 connectivity matrices for each subject.

Input:
    - data/raw/ds000246/ (BIDS dataset)
    - data/processed/eligible_subjects.csv (list of subjects to process)

Output:
    - data/processed/adjacency_matrices/ (directory containing .npy files)
    - data/processed/parcellated_timeseries/ (directory containing .npy files)
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
from nilearn.input_data import NiftiLabelsMasker
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger
from utils.atlas import load_aal_atlas_mask
from utils.io import load_csv, ensure_dir

# Configuration
DATASET_PATH = Path("data/raw/ds000246")
ELIGIBLE_SUBJECTS_PATH = Path("data/processed/eligible_subjects.csv")
ADJACENCY_OUTPUT_DIR = Path("data/processed/adjacency_matrices")
TIMESERIES_OUTPUT_DIR = Path("data/processed/parcellated_timeseries")
TEMP_DIR = Path("data/processed/temp_preprocessing")

# FSL command
MCFLIRT_CMD = "mcflirt"

def get_logger_wrapper(name=__name__):
    """Get a configured logger."""
    return get_logger(name)

def run_command(cmd, logger, cwd=None):
    """Run a shell command and log output."""
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout:
            logger.debug(result.stdout)
        if result.stderr:
            logger.debug(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(cmd)}")
        logger.error(f"Error output: {e.stderr}")
        return False

def perform_motion_correction(input_nifti, output_nifti, logger):
    """
    Perform motion correction using FSL's mcflirt.
    
    Args:
        input_nifti: Path to input 4D NIfTI file
        output_nifti: Path to output corrected 4D NIfTI file
        logger: Logger instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not Path(input_nifti).exists():
        logger.error(f"Input file not found: {input_nifti}")
        return False
    
    # Ensure output directory exists
    ensure_dir(Path(output_nifti).parent)
    
    cmd = [
        MCFLIRT_CMD,
        "-in", str(input_nifti),
        "-out", str(output_nifti),
        "-ref", "mean",
        "-dof", 6,
        "-stats"
    ]
    
    return run_command(cmd, logger)

def normalize_to_mni(input_nifti, output_nifti, logger):
    """
    Normalize to MNI space using Nilearn.
    
    Args:
        input_nifti: Path to input 4D NIfTI file (in native space)
        output_nifti: Path to output normalized 4D NIfTI file
        logger: Logger instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not Path(input_nifti).exists():
        logger.error(f"Input file not found: {input_nifti}")
        return False
    
    try:
        # Load the image
        img = image.load_img(input_nifti)
        
        # Normalize to MNI space
        # Using standard MNI152 template
        normalized_img = image.resample_to_img(
            img,
            target_img=datasets.load_mni152_template(),
            interpolation='continuous'
        )
        
        # Save the normalized image
        normalized_img.to_filename(str(output_nifti))
        logger.info(f"Normalized image saved to {output_nifti}")
        return True
    except Exception as e:
        logger.error(f"Normalization failed: {str(e)}")
        return False

def extract_timeseries_from_atlas(
    nifti_path, 
    atlas_mask_path, 
    labels, 
    output_timeseries_path, 
    output_adjacency_path, 
    logger
):
    """
    Extract timeseries from parcellated regions and compute adjacency matrix.
    
    Args:
        nifti_path: Path to 4D NIfTI file (normalized)
        atlas_mask_path: Path to AAL atlas mask file
        labels: List of region labels
        output_timeseries_path: Path to save timeseries (.npy)
        output_adjacency_path: Path to save adjacency matrix (.npy)
        logger: Logger instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not Path(nifti_path).exists():
        logger.error(f"Input NIfTI not found: {nifti_path}")
        return False
    
    if not Path(atlas_mask_path).exists():
        logger.error(f"Atlas mask not found: {atlas_mask_path}")
        return False
    
    try:
        # Load the 4D image
        img = image.load_img(nifti_path)
        
        # Load the atlas mask
        atlas_img = image.load_img(atlas_mask_path)
        
        # Create masker
        masker = NiftiLabelsMasker(
            labels_img=atlas_img,
            labels=labels,
            standardize=True,
            detrend=True,
            low_pass=0.1,
            high_pass=0.01,
            t_r=2.0,  # Assuming TR=2.0s, adjust if needed
            memory="data/processed/temp_preprocessing",
            memory_level=1,
            verbose=1
        )
        
        # Extract timeseries
        timeseries = masker.fit_transform(img)
        
        # Compute correlation matrix (adjacency matrix)
        # Using Pearson correlation
        correlation_matrix = np.corrcoef(timeseries.T)
        
        # Handle NaN values (can occur if a region has zero variance)
        correlation_matrix = np.nan_to_num(correlation_matrix, nan=0.0)
        
        # Save outputs
        np.save(output_timeseries_path, timeseries)
        np.save(output_adjacency_path, correlation_matrix)
        
        logger.info(f"Timeseries shape: {timeseries.shape}")
        logger.info(f"Adjacency matrix shape: {correlation_matrix.shape}")
        logger.info(f"Saved timeseries to {output_timeseries_path}")
        logger.info(f"Saved adjacency matrix to {output_adjacency_path}")
        
        return True
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def process_subject(subject_id, bids_path, logger):
    """
    Process a single subject: motion correction -> normalization -> parcellation.
    
    Args:
        subject_id: BIDS subject ID (e.g., 'sub-001')
        bids_path: Path to BIDS dataset root
        logger: Logger instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Processing subject: {subject_id}")
    
    # Find the rs-fMRI file for this subject
    func_dir = bids_path / subject_id / "func"
    if not func_dir.exists():
        logger.warning(f"No func directory for {subject_id}")
        return False
    
    # Find the first rs-fMRI file
    func_files = list(func_dir.glob("*task-rest*.nii*"))
    if not func_files:
        logger.warning(f"No resting-state fMRI files found for {subject_id}")
        return False
    
    input_nifti = func_files[0]
    logger.info(f"Found input file: {input_nifti}")
    
    # Create temporary directory for this subject
    subject_temp_dir = TEMP_DIR / subject_id
    ensure_dir(subject_temp_dir)
    
    # Step 1: Motion Correction
    motion_corrected_path = subject_temp_dir / "mcflirt.nii.gz"
    if not perform_motion_correction(input_nifti, motion_corrected_path, logger):
        logger.error(f"Motion correction failed for {subject_id}")
        return False
    
    # Step 2: Normalization to MNI
    normalized_path = subject_temp_dir / "normalized.nii.gz"
    if not normalize_to_mni(motion_corrected_path, normalized_path, logger):
        logger.error(f"Normalization failed for {subject_id}")
        return False
    
    # Step 3: Load AAL Atlas
    atlas_mask_path = load_aal_atlas_mask()
    if atlas_mask_path is None:
        logger.error("Failed to load AAL atlas mask")
        return False
    
    # Load atlas labels
    try:
        # AAL atlas typically has 90 regions (excluding cerebellum)
        # We'll use the standard AAL labels
        aal_labels = [
            "Frontal_Sup_L", "Frontal_Sup_R", "Frontal_Sup_Orb_L", "Frontal_Sup_Orb_R",
            "Frontal_Mid_L", "Frontal_Mid_R", "Frontal_Mid_Orb_L", "Frontal_Mid_Orb_R",
            "Frontal_Inf_Oper_L", "Frontal_Inf_Oper_R", "Frontal_Inf_Tri_L", "Frontal_Inf_Tri_R",
            "Frontal_Inf_Orb_L", "Frontal_Inf_Orb_R", "Rolandic_Oper_L", "Rolandic_Oper_R",
            "Supp_Motor_Area_L", "Supp_Motor_Area_R", "Olfactory_L", "Olfactory_R",
            "Frontal_Sup_Medial_L", "Frontal_Sup_Medial_R", "Frontal_Mid_Orb_Medial_L", "Frontal_Mid_Orb_Medial_R",
            "Cingulum_Ant_L", "Cingulum_Ant_R", "Cingulum_Mid_L", "Cingulum_Mid_R",
            "Cingulum_Post_L", "Cingulum_Post_R", "Hippocampus_L", "Hippocampus_R",
            "Parahippocampal_L", "Parahippocampal_R", "Amygdala_L", "Amygdala_R",
            "Calcarine_L", "Calcarine_R", "Cuneus_L", "Cuneus_R",
            "Lingual_L", "Lingual_R", "Occipital_Sup_L", "Occipital_Sup_R",
            "Occipital_Mid_L", "Occipital_Mid_R", "Occipital_Inf_L", "Occipital_Inf_R",
            "Fusiform_L", "Fusiform_R", "Postcentral_L", "Postcentral_R",
            "Parietal_Sup_L", "Parietal_Sup_R", "Parietal_Inf_L", "Parietal_Inf_R",
            "SupraMarginal_L", "SupraMarginal_R", "Angular_L", "Angular_R",
            "Precuneus_L", "Precuneus_R", "Paracentral_Lobule_L", "Paracentral_Lobule_R",
            "Caudate_L", "Caudate_R", "Putamen_L", "Putamen_R",
            "Pallidum_L", "Pallidum_R", "Thalamus_L", "Thalamus_R",
            "Heschl_L", "Heschl_R", "Temporal_Sup_L", "Temporal_Sup_R",
            "Temporal_Pole_Sup_L", "Temporal_Pole_Sup_R", "Temporal_Mid_L", "Temporal_Mid_R",
            "Temporal_Pole_Mid_L", "Temporal_Pole_Mid_R", "Temporal_Inf_L", "Temporal_Inf_R"
        ]
        
        if len(aal_labels) != 90:
            logger.warning(f"AAL labels length: {len(aal_labels)}, expected 90")
    except Exception as e:
        logger.error(f"Failed to load AAL labels: {str(e)}")
        return False
    
    # Step 4: Extract timeseries and compute adjacency matrix
    timeseries_output = TIMESERIES_OUTPUT_DIR / f"{subject_id}_timeseries.npy"
    adjacency_output = ADJACENCY_OUTPUT_DIR / f"{subject_id}_adjacency.npy"
    
    ensure_dir(TIMESERIES_OUTPUT_DIR)
    ensure_dir(ADJACENCY_OUTPUT_DIR)
    
    if not extract_timeseries_from_atlas(
        normalized_path,
        atlas_mask_path,
        aal_labels,
        timeseries_output,
        adjacency_output,
        logger
    ):
        logger.error(f"Parcellation failed for {subject_id}")
        return False
    
    logger.info(f"Successfully processed subject: {subject_id}")
    return True

def main():
    """Main entry point for preprocessing and parcellation."""
    logger = get_logger_wrapper("preprocess")
    logger.info("Starting T018: Preprocess and Parcellate")
    
    # Check if eligible subjects file exists
    if not ELIGIBLE_SUBJECTS_PATH.exists():
        logger.error(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_PATH}")
        logger.error("Please run 01_download_and_filter.py first")
        sys.exit(1)
    
    # Load eligible subjects
    eligible_df = load_csv(ELIGIBLE_SUBJECTS_PATH)
    if eligible_df is None or eligible_df.empty:
        logger.error("No eligible subjects found in the CSV file")
        sys.exit(1)
    
    logger.info(f"Found {len(eligible_df)} eligible subjects")
    
    # Ensure output directories exist
    ensure_dir(ADJACENCY_OUTPUT_DIR)
    ensure_dir(TIMESERIES_OUTPUT_DIR)
    ensure_dir(TEMP_DIR)
    
    # Load AAL atlas mask once
    atlas_mask_path = load_aal_atlas_mask()
    if atlas_mask_path is None:
        logger.error("Failed to load AAL atlas mask")
        sys.exit(1)
    logger.info(f"Loaded AAL atlas mask from: {atlas_mask_path}")
    
    # Process each subject
    success_count = 0
    fail_count = 0
    
    # Assuming the CSV has a 'subject_id' column
    subject_ids = eligible_df['subject_id'].tolist() if 'subject_id' in eligible_df.columns else eligible_df.iloc[:, 0].tolist()
    
    for subject_id in subject_ids:
        if process_subject(subject_id, DATASET_PATH, logger):
            success_count += 1
        else:
            fail_count += 1
            logger.error(f"Failed to process subject: {subject_id}")
    
    logger.info(f"Processing complete. Success: {success_count}, Failed: {fail_count}")
    
    if fail_count > 0:
        logger.warning(f"{fail_count} subjects failed to process")
        sys.exit(1)
    
    logger.info("All subjects processed successfully")
    sys.exit(0)

if __name__ == "__main__":
    main()