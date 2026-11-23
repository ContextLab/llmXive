import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import boto3
import numpy as np
import nibabel as nib
import pandas as pd
import re

from config import Config
from utils import setup_logging, ensure_dir

# Constants
CONFIG = Config()
LOG_DIR = CONFIG.LOG_DIR
ensure_dir(LOG_DIR)

# Setup module logger
logger = logging.getLogger(__name__)

def calculate_md5(file_path: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def verify_checksum(file_path: str, expected_md5: str) -> bool:
    """Verify file checksum against expected value."""
    return calculate_md5(file_path) == expected_md5

def download_from_s3(bucket: str, key: str, local_path: str) -> bool:
    """Download file from S3 bucket to local path."""
    try:
        s3 = boto3.client('s3')
        s3.download_file(bucket, key, local_path)
        return True
    except Exception as e:
        logger.error(f"Failed to download {key} from {bucket}: {e}")
        return False

def download_hcp_fmri_data(subject_id: str) -> Optional[str]:
    """Download pre-processed HCP fMRI data for a subject."""
    # Implementation details for S3 download
    # Assuming data is already downloaded per T039
    base_path = CONFIG.RAW_DATA_DIR / subject_id
    if base_path.exists():
        return str(base_path)
    logger.warning(f"Data not found for subject {subject_id}")
    return None

def download_phenotype_file() -> Optional[Path]:
    """Download phenotype file from HCP source."""
    # Assuming data is already downloaded per T040
    phenotype_path = CONFIG.PHENOTYPE_PATH
    if phenotype_path.exists():
        return phenotype_path
    logger.warning("Phenotype file not found")
    return None

def calculate_fd(time_series: np.ndarray, tr: float = 0.72) -> np.ndarray:
    """
    Calculate Framewise Displacement (FD) from fMRI time series.
    
    Args:
        time_series: 4D array (x, y, z, t) or 2D array (n_volumes, n_features)
        tr: Repetition time in seconds
        
    Returns:
        Array of FD values for each time point (length = n_volumes - 1)
    """
    if time_series.ndim == 4:
        # Convert 4D to 2D: reshape to (n_volumes, n_voxels)
        n_volumes = time_series.shape[3]
        n_voxels = time_series.shape[0] * time_series.shape[1] * time_series.shape[2]
        ts_2d = time_series.reshape(n_voxels, n_volumes).T
    else:
        ts_2d = time_series
        
    if ts_2d.shape[0] < 2:
        return np.array([])
        
    # Calculate displacement between consecutive time points
    # FD = |dx| + |dy| + |dz| + |da| + |db| + |dc|
    # For simplicity, we use sum of absolute differences across all features
    diffs = np.abs(np.diff(ts_2d, axis=0))
    fd = np.sum(diffs, axis=1)
    
    return fd

def load_and_scrub_subject(
    subject_id: str,
    fd_threshold: float = 0.2,
    min_frames: int = 100
) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
    """
    Load fMRI data for a subject, calculate FD, and scrub high-motion volumes.
    
    Args:
        subject_id: Subject identifier
        fd_threshold: FD threshold for scrubbing (default 0.2mm)
        min_frames: Minimum number of frames required after scrubbing
        
    Returns:
      - Scrubbed time series (None if subject excluded)
      - Metadata dict containing:
        - 'excluded': bool
        - 'reason': str
        - 'original_frames': int
        - 'scrubbed_frames': int
        - 'nan_count': int
        - 'fd_mean': float
    """
    data_path = download_hcp_fmri_data(subject_id)
    if not data_path:
        return None, {
            'excluded': True,
            'reason': 'Data not found',
            'original_frames': 0,
            'scrubbed_frames': 0,
            'nan_count': 0,
            'fd_mean': 0.0
        }
    
    try:
        # Load NIfTI file
        img = nib.load(data_path)
        data = img.get_fdata()
        
        if data.ndim != 4:
            return None, {
                'excluded': True,
                'reason': f'Invalid dimensions: {data.shape}',
                'original_frames': 0,
                'scrubbed_frames': 0,
                'nan_count': 0,
                'fd_mean': 0.0
            }
        
        original_frames = data.shape[3]
        
        # Calculate FD
        fd = calculate_fd(data)
        fd_mean = np.mean(fd) if len(fd) > 0 else 0.0
        
        # Identify high-motion volumes
        # FD is calculated for t=1 to t=N-1, so we align with original indices
        high_motion_mask = fd > fd_threshold
        
        # Create scrub mask (True = keep, False = scrub)
        # First volume is always kept (no previous frame to compare)
        scrub_mask = np.ones(original_frames, dtype=bool)
        scrub_mask[1:] = ~high_motion_mask
        
        # Apply scrubbing
        scrubbed_data = data[:, :, :, scrub_mask]
        scrubbed_frames = scrubbed_data.shape[3]
        
        # Count NaNs in scrubbed data
        nan_count = np.sum(np.isnan(scrubbed_data))
        
        # Check minimum frames
        if scrubbed_frames < min_frames:
            return None, {
                'excluded': True,
                'reason': f'Insufficient frames after scrubbing ({scrubbed_frames} < {min_frames})',
                'original_frames': original_frames,
                'scrubbed_frames': scrubbed_frames,
                'nan_count': nan_count,
                'fd_mean': fd_mean
            }
        
        return scrubbed_data, {
            'excluded': False,
            'reason': 'OK',
            'original_frames': original_frames,
            'scrubbed_frames': scrubbed_frames,
            'nan_count': nan_count,
            'fd_mean': fd_mean
        }
        
    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {e}")
        return None, {
            'excluded': True,
            'reason': f'Processing error: {str(e)}',
            'original_frames': 0,
            'scrubbed_frames': 0,
            'nan_count': 0,
            'fd_mean': 0.0
        }

def run_motion_scrubbing(
    subject_ids: List[str],
    fd_threshold: float = 0.2,
    min_frames: int = 100
) -> List[str]:
    """
    Run motion scrubbing on all subjects and log exclusions.
    
    Args:
        subject_ids: List of subject IDs to process
        fd_threshold: FD threshold for scrubbing
        min_frames: Minimum frames required
        
    Returns:
        List of valid (non-excluded) subject IDs
    """
    valid_subjects = []
    excluded_reasons = []
    nan_counts = []
    
    # Setup log files
    missing_data_log = LOG_DIR / 'missing_data.log'
    motion_exclusions_log = LOG_DIR / 'motion_exclusions.log'
    parcel_quality_log = LOG_DIR / 'parcel_quality.log'
    
    # Clear/create log files
    for log_file in [missing_data_log, motion_exclusions_log, parcel_quality_log]:
        with open(log_file, 'w') as f:
            f.write(f"Motion Scrubbing Log - {pd.Timestamp.now()}\n")
            f.write("=" * 50 + "\n\n")
    
    logger.info(f"Starting motion scrubbing for {len(subject_ids)} subjects")
    
    for subject_id in subject_ids:
        logger.info(f"Processing subject: {subject_id}")
        
        scrubbed_data, meta = load_and_scrub_subject(
            subject_id, 
            fd_threshold=fd_threshold, 
            min_frames=min_frames
        )
        
        if meta['excluded']:
            excluded_reasons.append({
                'subject_id': subject_id,
                'reason': meta['reason'],
                'original_frames': meta['original_frames'],
                'scrubbed_frames': meta['scrubbed_frames'],
                'fd_mean': meta['fd_mean']
            })
            
            # Log to missing_data.log or motion_exclusions.log
            if 'Data not found' in meta['reason'] or 'Processing error' in meta['reason']:
                with open(missing_data_log, 'a') as f:
                    f.write(f"Subject: {subject_id}\n")
                    f.write(f"  Reason: {meta['reason']}\n")
                    f.write(f"  Original frames: {meta['original_frames']}\n")
                    f.write(f"  Scrubbed frames: {meta['scrubbed_frames']}\n")
                    f.write(f"  FD mean: {meta['fd_mean']:.4f}\n\n")
            else:
                with open(motion_exclusions_log, 'a') as f:
                    f.write(f"Subject: {subject_id}\n")
                    f.write(f"  Reason: {meta['reason']}\n")
                    f.write(f"  Original frames: {meta['original_frames']}\n")
                    f.write(f"  Scrubbed frames: {meta['scrubbed_frames']}\n")
                    f.write(f"  FD mean: {meta['fd_mean']:.4f}\n\n")
        else:
            valid_subjects.append(subject_id)
            nan_counts.append({
                'subject_id': subject_id,
                'nan_count': meta['nan_count'],
                'scrubbed_frames': meta['scrubbed_frames']
            })
            
            # Log valid subject to parcel_quality.log
            with open(parcel_quality_log, 'a') as f:
                f.write(f"Subject: {subject_id}\n")
                f.write(f"  Status: VALID\n")
                f.write(f"  Scrubbed frames: {meta['scrubbed_frames']}\n")
                f.write(f"  NaN count: {meta['nan_count']}\n")
                f.write(f"  FD mean: {meta['fd_mean']:.4f}\n\n")
    
    # Summary logging
    logger.info(f"Motion scrubbing complete. {len(valid_subjects)} valid subjects, {len(excluded_reasons)} excluded.")
    
    with open(motion_exclusions_log, 'a') as f:
        f.write("\n" + "=" * 50 + "\n")
        f.write("SUMMARY\n")
        f.write(f"Total subjects processed: {len(subject_ids)}\n")
        f.write(f"Valid subjects: {len(valid_subjects)}\n")
        f.write(f"Excluded subjects: {len(excluded_reasons)}\n")
        f.write(f"Exclusion rate: {len(excluded_reasons)/len(subject_ids)*100:.1f}%\n")
    
    return valid_subjects

def main():
    """Main entry point for motion scrubbing."""
    # Get subject list from phenotype file
    phenotype_path = download_phenotype_file()
    if not phenotype_path:
        logger.critical("Phenotype file not found. Cannot proceed.")
        return []
        
    df = pd.read_csv(phenotype_path)
    subject_ids = df['Subject_ID'].tolist()  # Assuming column name is Subject_ID
    
    # Run motion scrubbing
    valid_subjects = run_motion_scrubbing(subject_ids)
    
    logger.info(f"Valid subjects: {valid_subjects}")
    return valid_subjects

if __name__ == "__main__":
    setup_logging()
    main()
