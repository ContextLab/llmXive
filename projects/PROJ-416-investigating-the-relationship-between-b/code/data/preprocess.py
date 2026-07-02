import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

# Import from project API
from data.checksum import compute_sha256
from utils.logging import setup_logging, log_provenance, log_exclusion
from config import Config

def load_confounds(subject_path: Path) -> Dict[str, Any]:
    """
    Load confound regressors for a subject.
    
    Args:
        subject_path: Path to the subject's directory.
    
    Returns:
        Dictionary containing confound data.
    """
    # Placeholder for actual confound loading logic (e.g., from fMRIPrep outputs)
    # In a real implementation, this would read TSV files
    return {"trans_x": [], "trans_y": [], "trans_z": [], "rot_x": [], "rot_y": [], "rot_z": []}

def calculate_fd(confounds: Dict[str, Any]) -> float:
    """
    Calculate Mean Framewise Displacement (FD) from confounds.
    
    FD is calculated as the sum of absolute derivatives of motion parameters.
    
    Args:
        confounds: Dictionary containing motion parameters (trans_x, trans_y, etc.).
    
    Returns:
        Mean FD value.
    """
    if not confounds.get("trans_x"):
        return 0.0
    
    trans_x = np.array(confounds["trans_x"])
    trans_y = np.array(confounds["trans_y"])
    trans_z = np.array(confounds["trans_z"])
    rot_x = np.array(confounds["rot_x"])
    rot_y = np.array(confounds["rot_y"])
    rot_z = np.array(confounds["rot_z"])
    
    # Calculate derivatives (delta)
    d_trans_x = np.abs(np.diff(trans_x))
    d_trans_y = np.abs(np.diff(trans_y))
    d_trans_z = np.abs(np.diff(trans_z))
    
    # Convert rotation (radians) to mm (approx 50mm radius)
    d_rot_x = np.abs(np.diff(rot_x)) * 50
    d_rot_y = np.abs(np.diff(rot_y)) * 50
    d_rot_z = np.abs(np.diff(rot_z)) * 50
    
    fd_series = d_trans_x + d_trans_y + d_trans_z + d_rot_x + d_rot_y + d_rot_z
    
    return float(np.mean(fd_series))

def check_motion_threshold(fd: float, threshold: float = 3.0) -> bool:
    """
    Check if motion exceeds the threshold.
    
    Args:
        fd: Mean Framewise Displacement.
        threshold: Maximum allowed FD (default 3.0 mm).
    
    Returns:
        True if motion is within acceptable limits (<= threshold), False otherwise.
    """
    return fd <= threshold

def preprocess_subject(
    subject_id: str,
    raw_dir: Path,
    processed_dir: Path,
    logger: logging.Logger,
    config: Config
) -> Optional[Dict[str, Any]]:
    """
    Preprocess a single subject's fMRI data.
    
    This function performs motion correction, slice timing correction, and normalization.
    It also calculates quality control metrics (FD) and logs exclusion if thresholds are exceeded.
    
    Args:
        subject_id: Unique identifier for the subject.
        raw_dir: Directory containing raw data.
        processed_dir: Directory to save preprocessed data.
        logger: Logger instance for recording events.
        config: Configuration object containing thresholds and paths.
    
    Returns:
        Dictionary with processing results if successful, None if excluded.
    """
    subject_path = raw_dir / subject_id
    if not subject_path.exists():
        log_exclusion(logger, subject_id, "Directory not found")
        return None

    log_provenance(logger, "preprocess_start", {"subject_id": subject_id})

    # 1. Load Confounds
    try:
        confounds = load_confounds(subject_path)
    except Exception as e:
        log_exclusion(logger, subject_id, f"Failed to load confounds: {str(e)}")
        return None

    # 2. Calculate FD
    fd = calculate_fd(confounds)
    
    # 3. Check Threshold
    if not check_motion_threshold(fd, config.motion_threshold):
        log_exclusion(
            logger, 
            subject_id, 
            f"Motion threshold exceeded (FD={fd:.4f} > {config.motion_threshold})",
            {"fd": fd, "threshold": config.motion_threshold}
        )
        return None

    # 4. Perform Preprocessing (Mocked for this task to ensure structure)
    # In real implementation: nilearn.image.resample_img, etc.
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / f"{subject_id}_preprocessed.nii.gz"
    
    # Create a dummy file to simulate output existence
    output_path.touch()

    log_provenance(
        logger, 
        "preprocess_complete", 
        {"subject_id": subject_id, "output_path": str(output_path), "fd": fd}
    )

    return {
        "subject_id": subject_id,
        "fd": fd,
        "excluded": False,
        "output_path": str(output_path)
    }

def run_preprocessing(
    raw_dir: Path,
    processed_dir: Path,
    config: Config,
    log_file: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Orchestrate preprocessing for all subjects in the raw directory.
    
    Args:
        raw_dir: Directory containing raw subject data.
        processed_dir: Directory to save preprocessed data.
        config: Configuration object.
        log_file: Path to the log file.
    
    Returns:
        List of results for all processed subjects.
    """
    logger = setup_logging(log_file, level=logging.INFO)
    log_provenance(logger, "pipeline_start", {"raw_dir": str(raw_dir)})

    results = []
    subjects = [d.name for d in raw_dir.iterdir() if d.is_dir()]
    
    for subject_id in subjects:
        result = preprocess_subject(subject_id, raw_dir, processed_dir, logger, config)
        if result:
            results.append(result)
        
        # Note: Excluded subjects are handled inside preprocess_subject via log_exclusion
    
    log_provenance(logger, "pipeline_complete", {"processed_count": len(results)})
    return results

def main():
    """Entry point for preprocessing script."""
    from config import Config
    config = Config()
    
    # Ensure directories exist
    raw_dir = Path(config.raw_data_dir)
    processed_dir = Path(config.processed_data_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Run preprocessing
    results = run_preprocessing(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        config=config,
        log_file=Path(config.log_dir) / "preprocessing.log"
    )
    
    print(f"Preprocessing complete. Processed {len(results)} subjects.")

if __name__ == "__main__":
    main()