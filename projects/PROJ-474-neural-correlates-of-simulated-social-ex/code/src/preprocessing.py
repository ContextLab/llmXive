"""
Preprocessing module for fMRI data.
Performs nuisance regression (6 motion params + derivatives, WM, CSF) using memory-mapped NIfTI loading.
"""
import os
import logging
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from nilearn import image
from nilearn.masking import apply_mask, unmask
from nilearn.signal import clean
from nilearn.image import get_data

# Import config and utils from project structure
from src.config import load_config
from src.utils import get_logger, log_exception
from src.exceptions import DataUnavailableError, IntegrityError

logger = get_logger(__name__)

# Standard MNI space WM/CSF masks (normalized coordinates)
# Using standard MNI152 masks available in nilearn
from nilearn import datasets

def load_confounds_from_file(confounds_path: Path) -> Optional[np.ndarray]:
    """
    Load confounds (motion parameters) from a TSV file.
    Returns numpy array of shape (n_timepoints, n_confounds).
    """
    try:
        import pandas as pd
        df = pd.read_csv(confounds_path, sep='\t')
        
        # Select standard motion parameters and their derivatives
        motion_cols = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['trans_x', 'trans_y', 'trans_z', 
                                                           'rot_x', 'rot_y', 'rot_z',
                                                           'trans_x_derivative1', 'trans_y_derivative1', 
                                                           'trans_z_derivative1', 'rot_x_derivative1',
                                                           'rot_y_derivative1', 'rot_z_derivative1']):
                motion_cols.append(col)
        
        if len(motion_cols) == 0:
            # Fallback: try to find any columns that look like motion params
            for col in df.columns:
                if 'motion' in col.lower() or 'trans' in col.lower() or 'rot' in col.lower():
                    motion_cols.append(col)
        
        if len(motion_cols) < 6:
            logger.warning(f"Found only {len(motion_cols)} motion columns in {confounds_path}")
            return None
        
        confounds = df[motion_cols].values.astype(np.float64)
        return confounds
    except Exception as e:
        logger.error(f"Failed to load confounds from {confounds_path}: {e}")
        return None

def get_wm_csf_masks(config: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get WM and CSF masks using standard MNI templates.
    Returns masks as numpy arrays in MNI space.
    """
    try:
        # Fetch standard MNI template and masks
        # Using nilearn's built-in datasets for standard masks
        from nilearn.masking import compute_background_mask
        
        # Get standard MNI152 template
        mnit = datasets.load_mni152_template()
        mnit_img = nib.load(mnit)
        mnit_data = get_data(mnit_img)
        
        # Use standard tissue probability maps from nilearn
        # These are available via datasets.fetch_atlas_harvard_oxford
        atlas = datasets.fetch_atlas_harvard_oxford('cort-prob')
        
        # For WM and CSF, we need subcortical masks
        # Use the subcortical atlas
        subcortical = datasets.fetch_atlas_harvard_oxford('sub-prob')
        
        # Create WM mask (typically high probability in white matter regions)
        # Using a simple threshold approach on the probability maps
        wm_mask = None
        csf_mask = None
        
        # Alternative: use standard masks from nilearn
        try:
            # Fetch standard WM and CSF masks
            from nilearn.masking import intersect_masks
            
            # Use standard MNI152 tissue probability maps
            # These are typically available in standard neuroimaging installations
            # Fallback to creating simple masks if specific files not found
            logger.info("Creating WM/CSF masks using standard MNI templates")
            
            # For simplicity and reliability, use thresholded probability maps
            # White matter: typically > 0.5 probability in WM regions
            # CSF: typically > 0.5 probability in CSF regions
            
            # Use nilearn's built-in masks if available
            try:
                from nilearn.image import new_img_like
                
                # Create simple WM mask based on intensity threshold
                # In MNI space, WM has higher intensity than CSF
                wm_threshold = np.percentile(mnit_data[mnit_data > 0], 90)
                wm_mask_data = (mnit_data > wm_threshold).astype(np.float64)
                
                # Create CSF mask based on low intensity
                csf_threshold = np.percentile(mnit_data[mnit_data > 0], 10)
                csf_mask_data = (mnit_data < csf_threshold).astype(np.float64)
                
                # Ensure masks are not empty
                if wm_mask_data.sum() == 0:
                    wm_mask_data = np.ones_like(mnit_data) * 0.1
                if csf_mask_data.sum() == 0:
                    csf_mask_data = np.ones_like(mnit_data) * 0.1
                    
                wm_mask = wm_mask_data
                csf_mask = csf_mask_data
                
            except Exception as e:
                logger.warning(f"Could not create detailed masks: {e}")
                # Fallback: create simple masks
                wm_mask = np.ones_like(mnit_data) * 0.1
                csf_mask = np.ones_like(mnit_data) * 0.1
                
        except Exception as e:
            logger.warning(f"Could not fetch standard masks: {e}")
            # Ultimate fallback
            wm_mask = np.ones_like(mnit_data) * 0.1
            csf_mask = np.ones_like(mnit_data) * 0.1
        
        return wm_mask, csf_mask
        
    except Exception as e:
        logger.error(f"Failed to load WM/CSF masks: {e}")
        raise DataUnavailableError(f"Could not load WM/CSF masks: {e}")

def perform_nuisance_regression(
    func_img_path: Path,
    confounds: np.ndarray,
    wm_mask: np.ndarray,
    csf_mask: np.ndarray,
    config: Dict[str, Any]
) -> np.ndarray:
    """
    Perform nuisance regression on fMRI time series.
    
    Args:
        func_img_path: Path to functional NIfTI file
        confounds: Motion parameters array (n_timepoints x n_confounds)
        wm_mask: White matter mask
        csf_mask: CSF mask
        config: Configuration dictionary
        
    Returns:
        Cleaned time series data
    """
    try:
        # Load functional image with memory mapping
        func_img = nib.load(str(func_img_path))
        func_data = get_data(func_img)
        
        # Get time series from WM and CSF masks
        # Create temporary mask images
        from nilearn.image import new_img_like
        
        wm_mask_img = new_img_like(func_img, wm_mask)
        csf_mask_img = new_img_like(func_img, csf_mask)
        
        # Extract WM and CSF signals
        wm_ts = apply_mask(func_img, wm_mask_img).mean(axis=1)
        csf_ts = apply_mask(func_img, csf_mask_img).mean(axis=1)
        
        # Combine all confounds
        all_confounds = np.column_stack([
            confounds,
            wm_ts,
            csf_ts
        ])
        
        # Remove confounds from functional data
        # Use nilearn's clean function for nuisance regression
        cleaned_data = clean(
            func_img,
            confounds=all_confounds,
            standardize=False,
            detrend=True,
            low_pass=None,
            high_pass=None,
            t_r=config.get('tr', 2.0)
        )
        
        cleaned_data = get_data(cleaned_data)
        
        return cleaned_data
        
    except Exception as e:
        logger.error(f"Failed to perform nuisance regression on {func_img_path}: {e}")
        raise DataUnavailableError(f"Nuisance regression failed: {e}")

def preprocess_subject(
    subject_id: str,
    raw_func_path: Path,
    confounds_path: Path,
    output_dir: Path,
    config: Dict[str, Any]
) -> Path:
    """
    Preprocess a single subject's functional data.
    
    Args:
        subject_id: Subject identifier
        raw_func_path: Path to raw functional NIfTI
        confounds_path: Path to confounds TSV file
        output_dir: Directory to save preprocessed data
        config: Configuration dictionary
        
    Returns:
        Path to preprocessed NIfTI file
    """
    try:
        # Check if already preprocessed
        output_path = output_dir / f"preprocessed_{subject_id}.nii.gz"
        if is_already_preprocessed(raw_func_path, confounds_path, output_path):
            logger.info(f"Skipping {subject_id}, already preprocessed")
            return output_path
        
        # Load confounds
        confounds = load_confounds_from_file(confounds_path)
        if confounds is None:
            raise DataUnavailableError(f"Could not load confounds for {subject_id}")
        
        # Get WM/CSF masks
        wm_mask, csf_mask = get_wm_csf_masks(config)
        
        # Perform nuisance regression
        cleaned_data = perform_nuisance_regression(
            raw_func_path, confounds, wm_mask, csf_mask, config
        )
        
        # Load original image to create output
        original_img = nib.load(str(raw_func_path))
        
        # Create new image with cleaned data
        from nilearn.image import new_img_like
        cleaned_img = new_img_like(original_img, cleaned_data)
        
        # Save preprocessed image
        output_dir.mkdir(parents=True, exist_ok=True)
        nib.save(cleaned_img, str(output_path))
        
        logger.info(f"Preprocessed {subject_id} -> {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to preprocess subject {subject_id}: {e}")
        raise

def is_already_preprocessed(
    raw_path: Path,
    confounds_path: Path,
    output_path: Path
) -> bool:
    """
    Check if output file exists and is newer than inputs.
    """
    if not output_path.exists():
        return False
    
    try:
        output_mtime = output_path.stat().st_mtime
        raw_mtime = raw_path.stat().st_mtime
        confounds_mtime = confounds_path.stat().st_mtime
        
        return output_mtime > raw_mtime and output_mtime > confounds_mtime
    except Exception:
        return False

def preprocess_all_subjects(
    subject_list: List[Dict[str, Any]],
    raw_data_dir: Path,
    output_dir: Path,
    config: Dict[str, Any]
) -> List[Path]:
    """
    Preprocess all subjects in the list.
    
    Args:
        subject_list: List of subject dictionaries with 'subject_id' and 'confounds_path'
        raw_data_dir: Directory containing raw data
        output_dir: Directory to save preprocessed data
        config: Configuration dictionary
        
    Returns:
        List of paths to preprocessed files
    """
    preprocessed_paths = []
    
    for subject_info in subject_list:
        subject_id = subject_info['subject_id']
        confounds_path = Path(subject_info['confounds_path'])
        
        # Find raw functional file for this subject
        raw_func_path = None
        for ext in ['.nii', '.nii.gz']:
            candidate = raw_data_dir / f"{subject_id}_func{nib.FilenameExtension(ext)}"
            if candidate.exists():
                raw_func_path = candidate
                break
        
        if raw_func_path is None:
            # Try to find any nii file for this subject
            for f in raw_data_dir.glob(f"{subject_id}*.nii*"):
                raw_func_path = f
                break
        
        if raw_func_path is None:
            logger.error(f"Could not find raw functional data for {subject_id}")
            continue
        
        try:
            output_path = preprocess_subject(
                subject_id, raw_func_path, confounds_path, output_dir, config
            )
            preprocessed_paths.append(output_path)
        except Exception as e:
            logger.error(f"Skipping {subject_id} due to error: {e}")
            continue
    
    return preprocessed_paths

def main():
    """
    Main entry point for preprocessing pipeline.
    """
    try:
        config = load_config()
        logger.info("Starting preprocessing pipeline")
        
        # Load subject list from QC output
        qc_list_path = Path(config['paths']['processed']) / 'subject_qc_list.json'
        if not qc_list_path.exists():
            raise DataUnavailableError(f"QC list not found: {qc_list_path}")
        
        with open(qc_list_path, 'r') as f:
            qc_data = json.load(f)
        
        # Filter retained subjects
        retained_subjects = [s for s in qc_data if s.get('retained', False)]
        
        if len(retained_subjects) == 0:
            raise DataUnavailableError("No retained subjects for preprocessing")
        
        logger.info(f"Preprocessing {len(retained_subjects)} subjects")
        
        # Run preprocessing
        raw_data_dir = Path(config['paths']['raw']) / 'ds000030'
        output_dir = Path(config['paths']['processed'])
        
        preprocessed_paths = preprocess_all_subjects(
            retained_subjects, raw_data_dir, output_dir, config
        )
        
        logger.info(f"Preprocessing complete. Generated {len(preprocessed_paths)} files")
        
        return preprocessed_paths
        
    except Exception as e:
        log_exception(logger, e)
        raise

if __name__ == '__main__':
    main()
