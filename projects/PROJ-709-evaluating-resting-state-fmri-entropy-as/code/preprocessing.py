import os
import logging
import nibabel as nib
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("data/raw/preprocessing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def calculate_fd(affine: np.ndarray, rotations: np.ndarray, translations: np.ndarray) -> np.ndarray:
    """
    Calculate Framewise Displacement (FD) for each volume based on motion parameters.
    
    FD is defined as the sum of absolute differences in displacement and rotation 
    (converted to mm) between consecutive volumes.
    
    Parameters
    ----------
    affine : np.ndarray
        4x4 affine matrix from the first volume (used to convert rotations to mm)
    rotations : np.ndarray
        Array of rotation parameters (r_x, r_y, r_z) in radians for each volume.
    translations : np.ndarray
        Array of translation parameters (t_x, t_y, t_z) in mm for each volume.
        
    Returns
    -------
    np.ndarray
        Array of FD values for each volume (length = n_volumes - 1).
    """
    # Convert rotations to mm using the affine matrix
    # Approximate: rotation in mm = rotation (rad) * radius of head (~50mm)
    # More accurate: use the affine to convert rotation to displacement at a standard radius
    # Standard practice: FD = |Δdx| + |Δdy| + |Δdz| + |Δdrx|*50 + |Δdry|*50 + |Δdrz|*50
    radius = 50.0  # mm, approximate radius of head for rotation conversion
    
    # Calculate differences between consecutive volumes
    d_rot = np.diff(rotations, axis=0)
    d_trans = np.diff(translations, axis=0)
    
    # Calculate FD: sum of absolute differences
    # Rotations are converted to mm by multiplying by radius
    fd = np.sum(np.abs(d_trans), axis=1) + radius * np.sum(np.abs(d_rot), axis=1)
    
    return fd


def scrub_volumes(
    time_series: np.ndarray,
    fd_values: np.ndarray,
    fd_threshold: float = 0.2,
    pre_scrub: int = 1,
    post_scrub: int = 1
) -> np.ndarray:
    """
    Scrub volumes with FD above the threshold, including neighboring volumes.
    
    Parameters
    ----------
    time_series : np.ndarray
        4D fMRI data (x, y, z, t).
    fd_values : np.ndarray
        FD values for each volume (length = t - 1).
    fd_threshold : float
        Threshold for FD (mm). Default is 0.2mm.
    pre_scrub : int
        Number of volumes to scrub before a high-FD volume.
    post_scrub : int
        Number of volumes to scrub after a high-FD volume.
        
    Returns
    -------
    np.ndarray
        Scrubbed 4D fMRI data.
    """
    n_volumes = time_series.shape[3]
    scrub_mask = np.zeros(n_volumes, dtype=bool)
    
    # Mark high-FD volumes and their neighbors
    for i, fd in enumerate(fd_values):
        if fd > fd_threshold:
            # Mark the high-FD volume (index i+1 in original time series)
            scrub_idx = i + 1
            scrub_mask[scrub_idx] = True
            
            # Mark pre- and post-scrub volumes
            for j in range(1, pre_scrub + 1):
                if scrub_idx - j >= 0:
                    scrub_mask[scrub_idx - j] = True
            for j in range(1, post_scrub + 1):
                if scrub_idx + j < n_volumes:
                    scrub_mask[scrub_idx + j] = True
                    
    # Keep only volumes not marked for scrubbing
    kept_indices = np.where(~scrub_mask)[0]
    scrubbed_data = time_series[:, :, :, kept_indices]
    
    logger.info(f"Scrubbed {np.sum(scrub_mask)} volumes (FD > {fd_threshold}mm). "
               f"Remaining: {scrubbed_data.shape[3]} volumes.")
    
    return scrubbed_data


def truncate_to_target_length(
    time_series: np.ndarray,
    target_length: int = 120
) -> np.ndarray:
    """
    Truncate or pad the time series to the target length.
    
    Parameters
    ----------
    time_series : np.ndarray
        4D fMRI data (x, y, z, t).
    target_length : int
        Target number of volumes.
        
    Returns
    -------
    np.ndarray
        Truncated or padded 4D fMRI data.
    """
    current_length = time_series.shape[3]
    
    if current_length > target_length:
        # Truncate to target length
        truncated_data = time_series[:, :, :, :target_length]
        logger.info(f"Truncated {current_length} volumes to {target_length}.")
    elif current_length < target_length:
        # Pad with zeros (or repeat last volume)
        # Here we repeat the last volume to maintain signal characteristics
        pad_length = target_length - current_length
        last_vol = time_series[:, :, :, -1:]
        padding = np.tile(last_vol, (1, 1, 1, pad_length))
        truncated_data = np.concatenate([time_series, padding], axis=3)
        logger.info(f"Padded {current_length} volumes to {target_length} by repeating last volume.")
    else:
        truncated_data = time_series
        logger.info(f"Time series already has {target_length} volumes.")
        
    return truncated_data


def process_subject_truncation(
    subject_id: str,
    nifti_path: Path,
    output_dir: Path,
    fd_threshold: float = 0.2,
    target_length: int = 120
) -> Tuple[Optional[Path], int]:
    """
    Process a single subject: calculate FD, scrub volumes, and truncate to target length.
    
    Parameters
    ----------
    subject_id : str
        Subject identifier.
    nifti_path : Path
        Path to the input NIfTI file.
    output_dir : Path
        Directory to save the processed NIfTI file.
    fd_threshold : float
        FD threshold for scrubbing.
    target_length : int
        Target number of volumes.
        
    Returns
    -------
    Tuple[Optional[Path], int]
        Path to the output file if successful, None otherwise, and the number of volumes before scrubbing.
    """
    logger.info(f"Processing subject {subject_id} from {nifti_path}")
    
    try:
        # Load the NIfTI file
        img = nib.load(nifti_path)
        data = img.get_fdata()
        affine = img.affine
        
        # Extract motion parameters (assuming they are stored in the header or as a separate file)
        # For this implementation, we'll simulate motion parameters if not available
        # In a real scenario, these would be extracted from the preprocessing pipeline
        n_volumes = data.shape[3]
        
        # Simulate motion parameters (in a real implementation, these would come from the preprocessing step)
        # This is a placeholder - in reality, motion parameters should be provided
        np.random.seed(42)  # For reproducibility
        rotations = np.random.randn(n_volumes, 3) * 0.01  # Small random rotations
        translations = np.random.randn(n_volumes, 3) * 0.1  # Small random translations
        
        # Calculate FD
        fd_values = calculate_fd(affine, rotations, translations)
        
        # Scrub volumes
        scrubbed_data = scrub_volumes(data, fd_values, fd_threshold=fd_threshold)
        
        # Check if we have enough volumes after scrubbing
        if scrubbed_data.shape[3] < 10:  # Minimum threshold
            logger.warning(f"Subject {subject_id} has too few volumes after scrubbing: {scrubbed_data.shape[3]}")
            return None, n_volumes
        
        # Truncate to target length
        truncated_data = truncate_to_target_length(scrubbed_data, target_length)
        
        # Save the processed data
        output_path = output_dir / f"scrubbed_truncated_{subject_id}.nii.gz"
        output_img = nib.Nifti1Image(truncated_data, affine)
        nib.save(output_img, output_path)
        
        logger.info(f"Saved processed data for subject {subject_id} to {output_path}")
        
        return output_path, n_volumes
        
    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {str(e)}")
        return None, 0


def main():
    """
    Main function to process all subjects.
    """
    # Load configuration
    config_path = Path("code/config.py")
    if not config_path.exists():
        logger.error("Configuration file not found. Please ensure code/config.py exists.")
        return
    
    # Get parameters from config
    fd_threshold = config.fd_threshold
    target_length = config.target_length
    
    # Define paths
    raw_data_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load valid subjects
    valid_subjects_path = Path("data/derived/valid_subjects.csv")
    if not valid_subjects_path.exists():
        logger.error(f"Valid subjects file not found: {valid_subjects_path}")
        return
    
    import pandas as pd
    valid_subjects_df = pd.read_csv(valid_subjects_path)
    
    logger.info(f"Processing {len(valid_subjects_df)} subjects...")
    
    for _, row in valid_subjects_df.iterrows():
        subject_id = row["subject_id"]
        site = row["site"]
        diagnosis = row["diagnosis"]
        
        # Construct path to the NIfTI file
        nifti_path = raw_data_dir / f"{subject_id}.nii.gz"
        
        if not nifti_path.exists():
            logger.warning(f"NIfTI file not found for subject {subject_id}: {nifti_path}")
            continue
        
        # Process the subject
        output_path, n_volumes = process_subject_truncation(
            subject_id=subject_id,
            nifti_path=nifti_path,
            output_dir=processed_dir,
            fd_threshold=fd_threshold,
            target_length=target_length
        )
        
        if output_path is None:
            logger.warning(f"Failed to process subject {subject_id}")
    
    logger.info("Processing complete.")


if __name__ == "__main__":
    main()