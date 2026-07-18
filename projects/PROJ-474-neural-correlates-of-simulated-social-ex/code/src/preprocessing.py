"""
Preprocessing module for fMRI data.

Performs nuisance regression (6 motion params + derivatives, WM, CSF)
using memory-mapped NIfTI loading. Does NOT include global signal regression.
Checks if input data is already preprocessed to avoid redundant processing.
"""

import os
import numpy as np
import nibabel as nib
from nilearn import image
from nilearn.masking import apply_mask, unmask
from nilearn.signal import clean
from pathlib import Path
import logging
from typing import List, Optional, Tuple, Dict, Any

from src.config import load_config
from src.utils import get_logger, PipelineError

# Constants
PREPROCESSED_SUFFIX = "_preprocessed"
DEFAULT_CONFOUNDS = ["trans_x", "trans_y", "trans_z", 
                     "rot_x", "rot_y", "rot_z",
                     "trans_x_derivative1", "trans_y_derivative1", "trans_z_derivative1",
                     "rot_x_derivative1", "rot_y_derivative1", "rot_z_derivative1",
                     "wm", "csf"]

def is_already_preprocessed(nifti_path: Path, config: Dict[str, Any]) -> bool:
    """
    Check if the input data is already preprocessed.
    
    Strategy: Check if filename contains preprocessed suffix or 
    if a corresponding preprocessed file already exists.
    
    Args:
        nifti_path: Path to the input NIfTI file
        config: Configuration dictionary
        
    Returns:
        True if already preprocessed, False otherwise
    """
    filename = nifti_path.name
    
    # Check if filename already has preprocessed suffix
    if PREPROCESSED_SUFFIX in filename:
        return True
    
    # Check if a preprocessed version already exists
    preprocessed_path = nifti_path.parent / filename.replace(
        ".nii.gz", f"{PREPROCESSED_SUFFIX}.nii.gz"
    )
    if not preprocessed_path.exists():
        preprocessed_path = nifti_path.parent / filename.replace(
            ".nii", f"{PREPROCESSED_SUFFIX}.nii.gz"
        )
    
    if preprocessed_path.exists():
        return True
    
    # Check for preprocessed flag in metadata if available
    # This is a heuristic based on filename conventions
    if "preproc" in filename.lower() or "clean" in filename.lower():
        return True
        
    return False

def load_confounds_from_file(confounds_path: Path, confound_names: List[str]) -> np.ndarray:
    """
    Load confound regressors from a TSV file.
    
    Args:
        confounds_path: Path to the confounds TSV file
        confound_names: List of confound column names to extract
        
    Returns:
        numpy array of shape (n_timepoints, n_confounds)
        
    Raises:
        PipelineError: If confounds file is missing or invalid
    """
    import pandas as pd
    
    if not confounds_path.exists():
        raise PipelineError(f"Confounds file not found: {confounds_path}")
    
    try:
        confounds_df = pd.read_csv(confounds_path, sep='\t')
    except Exception as e:
        raise PipelineError(f"Failed to read confounds file {confounds_path}: {str(e)}")
    
    # Filter for available confounds
    available_confounds = []
    missing_confounds = []
    
    for name in confound_names:
        if name in confounds_df.columns:
            available_confounds.append(name)
        else:
            missing_confounds.append(name)
    
    if not available_confounds:
        raise PipelineError(f"No matching confounds found in {confounds_path}. Available: {list(confounds_df.columns)}")
    
    if missing_confounds:
        logging.warning(f"Missing confounds (will proceed with available): {missing_confounds}")
    
    confounds_matrix = confounds_df[available_confounds].values.astype(np.float32)
    
    # Handle NaN values by interpolation or forward fill
    import pandas as pd
    confounds_df_filtered = confounds_df[available_confounds].interpolate(method='linear').fillna(method='bfill').fillna(method='ffill').fillna(0)
    confounds_matrix = confounds_df_filtered.values.astype(np.float32)
    
    return confounds_matrix

def perform_nuisance_regression(
    nifti_path: Path,
    confounds_path: Path,
    output_path: Path,
    confound_names: Optional[List[str]] = None
) -> Path:
    """
    Perform nuisance regression on fMRI data using memory-mapped loading.
    
    Args:
        nifti_path: Path to input NIfTI file
        confounds_path: Path to confounds TSV file
        output_path: Path for output preprocessed NIfTI file
        confound_names: List of confound column names (defaults to DEFAULT_CONFOUNDS)
        
    Returns:
        Path to the preprocessed NIfTI file
        
    Raises:
        PipelineError: If preprocessing fails
    """
    if confound_names is None:
        confound_names = DEFAULT_CONFOUNDS
    
    logger = get_logger(__name__)
    logger.info(f"Processing {nifti_path.name}")
    
    try:
        # Load confounds
        confounds = load_confounds_from_file(confounds_path, confound_names)
        logger.debug(f"Loaded {confounds.shape[1]} confound regressors")
        
        # Load image with memory mapping
        # nilearn.image.load_img supports mmap internally for large files
        img = image.load_img(str(nifti_path))
        
        # Get affine and shape for reconstruction
        affine = img.affine
        shape = img.shape
        
        # Extract mask to reduce dimensionality
        # Use a standard brain mask or create one from the data
        from nilearn.masking import compute_epi_mask
        
        # Compute mask (this is memory efficient)
        mask_img = compute_epi_mask(img)
        
        # Apply mask to get time series
        logger.debug("Extracting masked time series...")
        time_series = apply_mask(img, mask_img)
        
        # Perform nuisance regression using nilearn's clean function
        # This performs regression and detrending in one step
        logger.debug("Performing nuisance regression...")
        
        # clean() handles the regression internally
        # standardize=False to keep original scale
        # detrend=True to remove linear trends
        # confounds are the nuisance regressors
        cleaned_ts = clean(
            time_series,
            confounds=confounds,
            standardize=False,
            detrend=True,
            low_pass=None,  # No low-pass filtering per spec
            high_pass=None,  # No high-pass filtering per spec
            t_r=2.0,  # Default TR, will be updated if available
            ensure_finite=True
        )
        
        # Unmask to get full 4D volume
        logger.debug("Reconstructing full volume...")
        cleaned_volume = unmask(cleaned_ts, mask_img)
        
        # Save the preprocessed image
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as compressed NIfTI
        image.save_img(cleaned_volume, str(output_path), compress=True)
        
        logger.info(f"Saved preprocessed data to {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Preprocessing failed for {nifti_path}: {str(e)}")
        raise PipelineError(f"Preprocessing failed: {str(e)}")

def preprocess_subject(
    subject_id: str,
    input_nifti_path: Path,
    confounds_path: Path,
    output_dir: Path,
    config: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Preprocess a single subject's fMRI data.
    
    Args:
        subject_id: Subject identifier
        input_nifti_path: Path to input NIfTI file
        confounds_path: Path to confounds TSV file
        output_dir: Directory for output files
        config: Configuration dictionary (optional)
        
    Returns:
        Path to preprocessed NIfTI file
    """
    if config is None:
        config = load_config()
    
    logger = get_logger(__name__)
    
    # Check if already preprocessed
    if is_already_preprocessed(input_nifti_path, config):
        logger.info(f"Skipping preprocessing for {subject_id} (already preprocessed)")
        
        # If input is already preprocessed, just copy or link it
        # Determine output filename
        if input_nifti_path.suffixes[-2:] == ['.nii', '.gz']:
            base_name = input_nifti_path.name.replace('.nii.gz', '')
        else:
            base_name = input_nifti_path.stem
        
        output_path = output_dir / f"{base_name}{PREPROCESSED_SUFFIX}.nii.gz"
        
        if not output_path.exists():
            # Copy the file if output doesn't exist
            import shutil
            shutil.copy2(input_nifti_path, output_path)
        
        return output_path
    
    # Generate output filename
    if input_nifti_path.suffixes[-2:] == ['.nii', '.gz']:
        base_name = input_nifti_path.name.replace('.nii.gz', '')
    else:
        base_name = input_nifti_path.stem
    
    output_filename = f"{base_name}{PREPROCESSED_SUFFIX}.nii.gz"
    output_path = output_dir / output_filename
    
    # Perform preprocessing
    return perform_nuisance_regression(
        input_nifti_path,
        confounds_path,
        output_path,
        confound_names=DEFAULT_CONFOUNDS
    )

def preprocess_all_subjects(
    subjects_metadata: List[Dict[str, Any]],
    data_dir: Path,
    output_dir: Path,
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Preprocess all subjects from metadata.
    
    Args:
        subjects_metadata: List of subject metadata dictionaries
        data_dir: Root data directory
        output_dir: Output directory for preprocessed data
        config: Configuration dictionary
        
    Returns:
        Updated list of subject metadata with preprocessed paths
    """
    if config is None:
        config = load_config()
    
    logger = get_logger(__name__)
    processed_subjects = []
    
    for subject_info in subjects_metadata:
        subject_id = subject_info['subject_id']
        
        # Find input NIfTI and confounds paths
        # Assuming structure: data/processed/{subject_id}/func/{subject_id}_task-{task}_run-{run}_bold.nii.gz
        # and data/processed/{subject_id}/func/{subject_id}_task-{task}_run-{run}_confounds.tsv
        
        func_dir = data_dir / subject_id / "func"
        
        if not func_dir.exists():
            logger.warning(f"Function directory not found for {subject_id}, skipping")
            continue
        
        # Find the bold file
        bold_files = list(func_dir.glob("*bold.nii.gz"))
        if not bold_files:
            logger.warning(f"No BOLD files found for {subject_id}, skipping")
            continue
        
        # Process each run
        for bold_file in bold_files:
            # Find corresponding confounds file
            confounds_file = bold_file.parent / bold_file.name.replace("bold.nii.gz", "confounds.tsv")
            
            if not confounds_file.exists():
                logger.warning(f"Confounds file not found for {bold_file.name}, skipping")
                continue
            
            try:
                output_path = preprocess_subject(
                    subject_id=subject_id,
                    input_nifti_path=bold_file,
                    confounds_path=confounds_file,
                    output_dir=output_dir / subject_id / "func",
                    config=config
                )
                
                # Update metadata
                subject_info['preprocessed_path'] = str(output_path)
                processed_subjects.append(subject_info.copy())
                
            except PipelineError as e:
                logger.error(f"Failed to preprocess {bold_file}: {str(e)}")
                continue
    
    return processed_subjects

def main():
    """Main entry point for preprocessing pipeline."""
    import json
    
    logger = get_logger(__name__)
    logger.info("Starting preprocessing pipeline")
    
    # Load configuration
    config = load_config()
    
    # Load subjects metadata from previous QC step
    metadata_path = Path(config['paths']['processed_dir']) / "subjects_metadata.json"
    
    if not metadata_path.exists():
        raise PipelineError(f"Subjects metadata not found at {metadata_path}")
    
    with open(metadata_path, 'r') as f:
        subjects_metadata = json.load(f)
    
    logger.info(f"Found {len(subjects_metadata)} subjects to preprocess")
    
    # Setup output directory
    output_dir = Path(config['paths']['processed_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run preprocessing
    processed_subjects = preprocess_all_subjects(
        subjects_metadata=subjects_metadata,
        data_dir=Path(config['paths']['processed_dir']),
        output_dir=output_dir,
        config=config
    )
    
    logger.info(f"Successfully preprocessed {len(processed_subjects)} subjects")
    
    # Save updated metadata
    output_metadata_path = output_dir / "preprocessed_subjects_metadata.json"
    with open(output_metadata_path, 'w') as f:
        json.dump(processed_subjects, f, indent=2)
    
    logger.info(f"Saved updated metadata to {output_metadata_path}")
    return processed_subjects

if __name__ == "__main__":
    main()
