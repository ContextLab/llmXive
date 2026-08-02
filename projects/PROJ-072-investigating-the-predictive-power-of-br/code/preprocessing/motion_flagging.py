import os
import sys
import csv
import json
import logging
import numpy as np
from pathlib import Path

# Add project root to path to allow imports if run as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from preprocessing.download import get_dataset_download_url
from metadata.schemas import Subject

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MOTION_THRESHOLD_MM = 2.0  # mm
DATA_RAW_DIR = project_root / "data" / "raw"
DATA_METADATA_DIR = project_root / "data" / "metadata"
SUBJECT_STATUS_FILE = DATA_METADATA_DIR / "subject_status.csv"
EXCLUSION_LOG_FILE = DATA_METADATA_DIR / "exclusion_log.txt"

def get_all_subject_ids() -> list[str]:
    """
    Scans data/raw for subject directories (sub-*) and returns a list of subject IDs.
    """
    if not DATA_RAW_DIR.exists():
        logger.warning(f"Data raw directory not found: {DATA_RAW_DIR}")
        return []

    subjects = []
    for item in sorted(DATA_RAW_DIR.iterdir()):
        if item.is_dir() and item.name.startswith("sub-"):
            # Extract ID without 'sub-' prefix if needed, or keep full name
            # Standard convention: keep 'sub-xxx'
            subjects.append(item.name)
    
    logger.info(f"Found {len(subjects)} subjects in {DATA_RAW_DIR}")
    return subjects

def load_motion_parameters(subject_id: str) -> dict[str, np.ndarray]:
    """
    Loads motion parameters (6 rigid-body parameters) for a specific subject.
    Expects files like: data/raw/<subject_id>/func/<subject_id>_desc-motion_params.txt
    or similar standard outputs from FSL MCFLIRT or similar.
    
    Returns a dict with keys 'trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z'
    each containing a numpy array of values per timepoint.
    """
    # Look for standard FSL MCFLIRT output or similar
    # Common pattern: <subject_id>_desc-preproc_bold_mcf.par or similar
    # We will look for any .par or .txt file containing motion estimates in the func dir
    
    subject_dir = DATA_RAW_DIR / subject_id
    if not subject_dir.exists():
        raise FileNotFoundError(f"Subject directory not found: {subject_dir}")
    
    func_dir = subject_dir / "func"
    if not func_dir.exists():
        # Try to find in root of subject dir if func doesn't exist
        func_dir = subject_dir
        
    motion_files = list(func_dir.glob("*_mcf.par")) + list(func_dir.glob("*motion*.txt")) + list(func_dir.glob("*_motion_params.txt"))
    
    if not motion_files:
        # Fallback: check if there's a generic log we can parse or if we need to simulate reading
        # For real implementation, we assume preprocessing (T012) generated these or we read from FSL output
        # If T012 hasn't run, this might fail. We assume T012 creates the necessary logs.
        # If no file found, we raise an error to fail loudly as per constraints.
        raise FileNotFoundError(f"No motion parameter files found for {subject_id} in {func_dir}")
    
    # Assume the first found file is the one
    motion_file = motion_files[0]
    logger.info(f"Loading motion parameters from: {motion_file}")
    
    params = np.loadtxt(motion_file)
    
    # Ensure we have at least 6 columns (3 trans, 3 rot)
    if params.shape[1] < 6:
        # If it's 3 columns, maybe only translation? Or 3 rotations?
        # Standard FSL MCFLIRT outputs 6 columns: 3 translations (mm), 3 rotations (radians)
        raise ValueError(f"Motion file {motion_file} has {params.shape[1]} columns, expected at least 6.")
    
    return {
        "trans_x": params[:, 0],
        "trans_y": params[:, 1],
        "trans_z": params[:, 2],
        "rot_x": params[:, 3],
        "rot_y": params[:, 4],
        "rot_z": params[:, 5]
    }

def calculate_max_displacement(motion_params: dict[str, np.ndarray]) -> float:
    """
    Calculates the maximum displacement (in mm) for a subject.
    Translations are in mm. Rotations are in radians.
    To be conservative, we convert rotations to mm displacement assuming a standard brain radius (e.g., 60mm).
    Or, strictly, we can just sum the max translation and max rotation converted.
    Standard practice: Max displacement = max( |trans_x|, |trans_y|, |trans_z|, |rot_x|*R, |rot_y|*R, |rot_z|*R )
    where R is a radius (often 50-60mm). Let's use 60mm as a conservative estimate for head radius.
    """
    R = 60.0  # mm
    max_trans = np.max(np.abs(np.concatenate([
        motion_params["trans_x"],
        motion_params["trans_y"],
        motion_params["trans_z"]
    ])))
    
    max_rot_mm = np.max(np.abs(np.concatenate([
        motion_params["rot_x"],
        motion_params["rot_y"],
        motion_params["rot_z"]
    ]))) * R
    
    return max(max_trans, max_rot_mm)

def flag_subject_motion(subject_id: str) -> dict:
    """
    Flags a single subject based on motion threshold.
    Returns a dict with:
      - subject_id
      - included (bool)
      - reason (str)
      - max_displacement (float)
    """
    try:
        params = load_motion_parameters(subject_id)
        max_disp = calculate_max_displacement(params)
        
        included = max_disp <= MOTION_THRESHOLD_MM
        reason = "Pass" if included else f"Exceeds threshold: {max_disp:.2f}mm > {MOTION_THRESHOLD_MM}mm"
        
        return {
            "subject_id": subject_id,
            "included": included,
            "reason": reason,
            "max_displacement": max_disp
        }
    except Exception as e:
        logger.error(f"Error processing motion for {subject_id}: {e}")
        return {
            "subject_id": subject_id,
            "included": False,
            "reason": f"Error loading parameters: {str(e)}",
            "max_displacement": np.nan
        }

def run_motion_flagging_pipeline():
    """
    Main pipeline function to flag all subjects and update subject_status.csv.
    """
    logger.info("Starting motion flagging pipeline...")
    
    subject_ids = get_all_subject_ids()
    if not subject_ids:
        logger.warning("No subjects found to process.")
        return

    results = []
    excluded_subjects = []
    
    for sub_id in subject_ids:
        res = flag_subject_motion(sub_id)
        results.append(res)
        if not res["included"]:
            excluded_subjects.append(res)
    
    # Ensure metadata directory exists
    DATA_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write subject_status.csv
    with open(SUBJECT_STATUS_FILE, mode='w', newline='') as f:
        fieldnames = ["subject_id", "included", "reason", "max_displacement"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Updated {SUBJECT_STATUS_FILE} with {len(results)} subjects.")
    
    # Write exclusion log
    with open(EXCLUSION_LOG_FILE, mode='w') as f:
        f.write(f"# Exclusion Log - Motion Flagging\n")
        f.write(f"# Threshold: {MOTION_THRESHOLD_MM}mm\n")
        f.write(f"# Total Excluded: {len(excluded_subjects)}\n\n")
        for exc in excluded_subjects:
            f.write(f"Subject: {exc['subject_id']}\n")
            f.write(f"  Reason: {exc['reason']}\n")
            f.write(f"  Max Displacement: {exc['max_displacement']:.2f}mm\n\n")
    
    logger.info(f"Wrote exclusion log to {EXCLUSION_LOG_FILE}")
    return results

def main():
    """
    Entry point for the script.
    """
    run_motion_flagging_pipeline()

if __name__ == "__main__":
    main()
