import os
import sys
import csv
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    root_dir = Path(__file__).resolve().parent.parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

from preprocessing.download import process_metadata_and_exclude_subjects

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MOTION_THRESHOLD_MM = 2.0  # Maximum allowed translation in mm
DATA_RAW_DIR = Path("data/raw")
DATA_METADATA_DIR = Path("data/metadata")
DATA_PROCESSED_DIR = Path("data/processed")

def load_motion_parameters(subject_id: str) -> Optional[np.ndarray]:
    """
    Load motion parameters (6 rigid-body parameters: 3 translation, 3 rotation)
    from the preprocessing output for a given subject.
    
    In a real pipeline, these would be extracted from FSL MCFLIRT logs or
    nilearn preprocessing outputs. For this implementation, we look for
    a standard motion parameter file format.
    
    Args:
        subject_id: The subject identifier (e.g., 'sub-001')
        
    Returns:
        numpy array of shape (n_volumes, 6) containing motion parameters,
        or None if file not found.
    """
    # Expected path for motion parameters (standardized naming)
    motion_file = DATA_RAW_DIR / f"{subject_id}_motion_params.npy"
    
    if not motion_file.exists():
        # Alternative: try to find in a subdirectory structure
        possible_paths = [
            DATA_RAW_DIR / subject_id / "motion_params.npy",
            DATA_RAW_DIR / subject_id / "mcflirt_params.txt",
            DATA_PROCESSED_DIR / f"{subject_id}_motion.npy"
        ]
        
        for path in possible_paths:
            if path.exists():
                motion_file = path
                break
        else:
            logger.warning(f"Motion parameters not found for {subject_id}")
            return None
    
    try:
        # Try loading as numpy array
        if motion_file.suffix == '.npy':
            params = np.load(motion_file)
        elif motion_file.suffix == '.txt' or motion_file.suffix == '.csv':
            params = np.loadtxt(motion_file, delimiter=',')
        else:
            logger.error(f"Unsupported motion parameter file format: {motion_file.suffix}")
            return None
        
        # Ensure shape is (n_volumes, 6)
        if params.ndim == 1:
            params = params.reshape(-1, 1)
        if params.shape[1] != 6:
            logger.warning(f"Unexpected motion parameter shape for {subject_id}: {params.shape}")
            # Try to handle if only 3 translation params are present
            if params.shape[1] == 3:
                params = np.hstack([params, np.zeros_like(params)])
        
        return params
    except Exception as e:
        logger.error(f"Error loading motion parameters for {subject_id}: {e}")
        return None

def calculate_max_displacement(motion_params: np.ndarray) -> Tuple[float, float, float]:
    """
    Calculate maximum displacement metrics from motion parameters.
    
    Args:
        motion_params: Array of shape (n_volumes, 6) with [tx, ty, tz, rx, ry, rz]
        
    Returns:
        Tuple of (max_translation_mm, max_rotation_mm, max_combined_mm)
    """
    if motion_params is None or motion_params.size == 0:
        return 0.0, 0.0, 0.0
    
    # Extract translation (first 3 columns) and rotation (last 3 columns)
    translations = motion_params[:, :3]  # mm
    rotations = motion_params[:, 3:]     # radians
    
    # Calculate frame-wise displacement (sum of absolute differences)
    # This is a common metric in fMRI preprocessing
    if len(translations) > 1:
        diff = np.diff(translations, axis=0)
        # Convert rotation differences to mm (approximate using 50mm radius)
        # This is a standard approximation in fMRI literature
        rotation_radius_mm = 50.0
        rot_diff_mm = np.abs(np.diff(rotations, axis=0)) * rotation_radius_mm
        
        # Total displacement per frame
        displacement = np.sum(np.abs(diff), axis=1) + np.sum(rot_diff_mm, axis=1)
        
        # For this task, we focus on maximum absolute translation
        max_translation = np.max(np.abs(translations))
        max_rotation_mm = np.max(np.abs(rotations)) * rotation_radius_mm
        max_combined = np.max(displacement)
    else:
        max_translation = np.max(np.abs(translations))
        max_rotation_mm = np.max(np.abs(rotations)) * rotation_radius_mm
        max_combined = max_translation + max_rotation_mm
    
    return float(max_translation), float(max_rotation_mm), float(max_combined)

def flag_subject_motion(subject_id: str) -> Dict:
    """
    Evaluate motion for a single subject and determine exclusion status.
    
    Args:
        subject_id: The subject identifier
        
    Returns:
        Dictionary with subject_id, excluded status, max_translation, and reason
    """
    motion_params = load_motion_parameters(subject_id)
    
    if motion_params is None:
        return {
            "subject_id": subject_id,
            "excluded": True,
            "reason": "Motion parameters not found",
            "max_translation_mm": 0.0,
            "max_rotation_mm": 0.0,
            "max_combined_mm": 0.0
        }
    
    max_trans, max_rot, max_combined = calculate_max_displacement(motion_params)
    
    excluded = max_trans > MOTION_THRESHOLD_MM
    reason = ""
    
    if excluded:
        reason = f"Excessive translation: {max_trans:.2f}mm > {MOTION_THRESHOLD_MM}mm threshold"
    else:
        reason = "Motion within acceptable limits"
    
    return {
        "subject_id": subject_id,
        "excluded": excluded,
        "reason": reason,
        "max_translation_mm": max_trans,
        "max_rotation_mm": max_rot,
        "max_combined_mm": max_combined
    }

def get_all_subject_ids() -> List[str]:
    """
    Get list of all subject IDs from the raw data directory.
    
    Returns:
        List of subject IDs (e.g., ['sub-001', 'sub-002', ...])
    """
    if not DATA_RAW_DIR.exists():
        logger.error(f"Raw data directory not found: {DATA_RAW_DIR}")
        return []
    
    subject_ids = []
    for item in DATA_RAW_DIR.iterdir():
        if item.is_dir() and item.name.startswith("sub-"):
            subject_ids.append(item.name)
        elif item.is_file() and item.name.startswith("sub-"):
            # Handle flat structure where files are directly in data_raw
            base_name = item.name.split('_')[0] if '_' in item.name else item.name
            if base_name not in subject_ids:
                subject_ids.append(base_name)
    
    # If no standard structure found, try to extract from metadata if available
    if not subject_ids:
        metadata_file = DATA_METADATA_DIR / "subject_status.csv"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'subject_id' in row:
                        subject_ids.append(row['subject_id'])
    
    return sorted(subject_ids)

def run_motion_flagging_pipeline() -> str:
    """
    Run the motion flagging pipeline for all subjects.
    
    Returns:
        Path to the updated subject_status.csv file
    """
    subject_ids = get_all_subject_ids()
    
    if not subject_ids:
        logger.warning("No subjects found to process. Creating empty status file.")
        subject_ids = []
    
    logger.info(f"Processing motion flagging for {len(subject_ids)} subjects")
    
    # Ensure metadata directory exists
    DATA_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    status_file = DATA_METADATA_DIR / "subject_status.csv"
    results = []
    
    for subject_id in subject_ids:
        try:
            status = flag_subject_motion(subject_id)
            results.append(status)
            logger.info(f"{subject_id}: {'EXCLUDED' if status['excluded'] else 'INCLUDED'} - {status['reason']}")
        except Exception as e:
            logger.error(f"Error processing {subject_id}: {e}")
            # Mark as excluded with error reason
            results.append({
                "subject_id": subject_id,
                "excluded": True,
                "reason": f"Error processing: {str(e)}",
                "max_translation_mm": 0.0,
                "max_rotation_mm": 0.0,
                "max_combined_mm": 0.0
            })
    
    # Write results to CSV
    with open(status_file, 'w', newline='') as f:
        fieldnames = ["subject_id", "excluded", "reason", "max_translation_mm", "max_rotation_mm", "max_combined_mm"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    # Update exclusion counts
    excluded_count = sum(1 for r in results if r['excluded'])
    included_count = len(results) - excluded_count
    
    logger.info(f"Motion flagging complete: {included_count} included, {excluded_count} excluded")
    
    # Log exclusion details
    exclusion_log = DATA_METADATA_DIR / "exclusion_log.txt"
    with open(exclusion_log, 'w') as f:
        f.write(f"Motion Exclusion Log\n")
        f.write(f"====================\n")
        f.write(f"Threshold: {MOTION_THRESHOLD_MM}mm\n")
        f.write(f"Total subjects: {len(results)}\n")
        f.write(f"Excluded: {excluded_count}\n")
        f.write(f"Included: {included_count}\n")
        f.write(f"\nExcluded Subjects:\n")
        for r in results:
            if r['excluded']:
                f.write(f"  - {r['subject_id']}: {r['reason']}\n")
    
    return str(status_file)

def main():
    """Main entry point for motion flagging script."""
    logger.info("Starting motion flagging pipeline")
    status_file = run_motion_flagging_pipeline()
    logger.info(f"Pipeline complete. Status file saved to: {status_file}")
    return status_file

if __name__ == "__main__":
    main()
