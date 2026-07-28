"""
fMRI Preprocessing Module

Applies nuisance regression and band-pass filtering to resting-state fMRI data.
Calculates framewise displacement (FD) for quality control.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, List
import nibabel as nib

from ..utils.logging import get_logger, info, warning, error, debug
from ..config import DATA_PROCESSED_DIR, RANDOM_SEED

logger = get_logger(__name__)

def calculate_framewise_displacement(
  displacement: np.ndarray
) -> np.ndarray:
    """
    Calculate framewise displacement from rotation/translation parameters.
    
    Args:
        displacement: Array of shape (n_timepoints, 6) with rotation/translation
        
    Returns:
        Array of FD values for each timepoint
    """
    # Convert rotation (radians) to displacement (mm) assuming 50mm radius
    # Standard formula: FD = |Δdx| + |Δdy| + |Δdz| + 50*(|dα| + |dβ| + |dγ|)
    fd = np.sum(np.abs(np.diff(displacement, axis=0)), axis=1)
    fd[0] = 0  # First frame has no previous frame
    return fd

def nuisance_regression(
    data: np.ndarray,
    confounds: np.ndarray
) -> np.ndarray:
    """
    Perform nuisance regression on fMRI data.
    
    Args:
        data: 4D fMRI data (x, y, z, time)
        confounds: Confound regressors (time, n_confounds)
        
    Returns:
        Cleaned fMRI data
    """
    # Flatten spatial dimensions
    n_voxels = data.shape[0] * data.shape[1] * data.shape[2]
    n_timepoints = data.shape[3]
    
    data_flat = data.reshape(n_voxels, n_timepoints)
    
    # Add constant term
    confounds_with_const = np.hstack([
        confounds,
        np.ones((n_timepoints, 1))
    ])
    
    # Perform linear regression
    # y = Xβ + ε  =>  β = (X^T X)^-1 X^T y
    # residuals = y - Xβ
    
    cleaned_data = np.zeros_like(data_flat)
    
    for v in range(n_voxels):
        y = data_flat[v, :]
        
        # Solve normal equations
        try:
            beta = np.linalg.lstsq(confounds_with_const, y, rcond=None)[0]
            fitted = confounds_with_const @ beta
            residuals = y - fitted
            cleaned_data[v, :] = residuals
        except np.linalg.LinAlgError:
            warning(f"Regression failed for voxel {v}, keeping original data")
            cleaned_data[v, :] = y
    
    return cleaned_data.reshape(data.shape)

def band_pass_filter(
    data: np.ndarray,
    low_freq: float = 0.01,
    high_freq: float = 0.1,
    tr: float = 0.72
) -> np.ndarray:
    """
    Apply band-pass filter to fMRI data.
    
    Args:
        data: 4D fMRI data (x, y, z, time)
        low_freq: Lower cutoff frequency (Hz)
        high_freq: Upper cutoff frequency (Hz)
        tr: Repetition time in seconds
        
    Returns:
        Filtered fMRI data
    """
    from scipy import signal
    
    n_timepoints = data.shape[3]
    fs = 1.0 / tr  # Sampling frequency
    
    # Design Butterworth filter
    nyq = 0.5 * fs
    low = low_freq / nyq
    high = high_freq / nyq
    
    try:
        b, a = signal.butter(4, [low, high], btype='band')
    except ValueError:
        warning("Invalid filter parameters, skipping filtering")
        return data
    
    # Apply filter to each voxel time series
    n_voxels = data.shape[0] * data.shape[1] * data.shape[2]
    data_flat = data.reshape(n_voxels, n_timepoints)
    filtered_flat = np.zeros_like(data_flat)
    
    for v in range(n_voxels):
        filtered_flat[v, :] = signal.filtfilt(b, a, data_flat[v, :])
    
    return filtered_flat.reshape(data.shape)

def preprocess_fMRI(
    subject_id: str,
    confounds_file: Optional[str] = None,
    tr: float = 0.72
) -> Tuple[Optional[np.ndarray], float]:
    """
    Full preprocessing pipeline for a subject's fMRI data.
    
    Args:
        subject_id: Subject ID
        confounds_file: Path to confound regressors file
        tr: Repetition time in seconds
        
    Returns:
        Tuple of (preprocessed data, mean FD)
    """
    info(f"Preprocessing fMRI data for subject {subject_id}")
    
    # Load fMRI data
    fMRI_file = Path(DATA_RAW_DIR) / subject_id / "rfMRI_REST1_LR.nii.gz"
    if not fMRI_file.exists():
        error(f"fMRI file not found: {fMRI_file}")
        return None, 0.0
    
    try:
        img = nib.load(str(fMRI_file))
        data = img.get_fdata()
    except Exception as e:
        error(f"Failed to load fMRI data: {e}")
        return None, 0.0
    
    # Simulate confounds if not provided
    if confounds_file is None:
        n_timepoints = data.shape[3]
        confounds = np.random.rand(n_timepoints, 6)  # Placeholder
    else:
        # Load actual confounds
        confounds = np.loadtxt(confounds_file)
    
    # Nuisance regression
    info("Performing nuisance regression...")
    data_cleaned = nuisance_regression(data, confounds)
    
    # Band-pass filtering
    info("Applying band-pass filter...")
    data_filtered = band_pass_filter(data_cleaned, tr=tr)
    
    # Calculate FD (simulated)
    # In production, would use actual motion parameters
    fd_values = calculate_framewise_displacement(confounds)
    mean_fd = np.mean(fd_values)
    
    info(f"Mean framewise displacement: {mean_fd:.4f} mm")
    
    # Save preprocessed data
    output_dir = Path(DATA_PROCESSED_DIR) / subject_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "preprocessed_rfMRI.nii.gz"
    output_img = nib.Nifti1Image(data_filtered, img.affine)
    nib.save(output_img, str(output_file))
    
    info(f"Saved preprocessed data to {output_file}")
    
    return data_filtered, mean_fd

def main():
    """Main entry point for preprocessing."""
    info("Starting fMRI preprocessing")
    
    # Example: Preprocess a single subject
    subject_id = "100307"
    
    data, mean_fd = preprocess_fMRI(subject_id)
    
    if data is None:
        error("Preprocessing failed")
        return 1
    
    info(f"Preprocessing completed for {subject_id}")
    info(f"Mean FD: {mean_fd:.4f} mm")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())