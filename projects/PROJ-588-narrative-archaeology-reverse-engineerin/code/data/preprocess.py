"""
Preprocessing pipeline using nilearn and fmriprep (via CLI).
"""
import os
import logging
from pathlib import Path
import subprocess
import json
from nilearn import image, masking
import code.config as config

logger = logging.getLogger(__name__)

def run_fmriprep_sequential(subject_id, input_dir, output_dir, flags=None):
    """
    Run fMRIPrep on a single subject sequentially.
    
    Args:
        subject_id (str): Subject identifier.
        input_dir (Path): Directory containing BIDS data.
        output_dir (Path): Output directory.
        flags (list): Additional fMRIPrep flags.
    
    Returns:
        Path: Path to the preprocessed output.
    """
    if flags is None:
        flags = config.FMRIPREP_FLAGS
    
    output_dir = Path(output_dir) / subject_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "fmriprep",
        str(input_dir),
        str(output_dir),
        "participant",
        "--participant-label", subject_id,
        *flags
    ]
    
    logger.info(f"Running fMRIPrep for {subject_id}...")
    try:
        subprocess.run(cmd, check=True)
        logger.info(f"fMRIPrep complete for {subject_id}")
        return output_dir
    except subprocess.CalledProcessError as e:
        logger.error(f"fMRIPrep failed for {subject_id}: {e}")
        raise

def smooth_data(nii_path, fwhm=6.0):
    """
    Smooth a 3D/4D NIfTI image.
    
    Args:
        nii_path (str): Path to NIfTI file.
        fwhm (float): Full width at half maximum in mm.
    
    Returns:
        Nifti1Image: Smoothed image.
    """
    img = image.load_img(nii_path)
    smoothed = image.smooth_img(img, fwhm=fwhm)
    return smoothed
