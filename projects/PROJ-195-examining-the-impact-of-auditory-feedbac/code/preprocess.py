"""
Preprocessing orchestration script for fmriprep.
Handles dataset download, subject filtering, fmriprep execution, QC, and deviation logging.
"""
import os
import sys
import subprocess
import logging
import time
import re
from pathlib import Path
from typing import List, Optional, Dict, Any

# Import utilities from sibling module
from utils import (
    get_bids_subject_path,
    get_fmriprep_output_path,
    get_motion_file,
    parse_motion_parameters,
    calculate_frame_displacement,
    check_motion_threshold,
    log_qc_metrics,
    filter_subjects_by_motion
)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_DERIVATIVES = PROJECT_ROOT / "data" / "derivatives"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
LOG_FILE = PROJECT_ROOT / "data" / "processed" / "preprocessing.log"
VALID_SUBJECTS_FILE = DATA_PROCESSED / "valid_subjects.txt"
QC_LOG_FILE = DATA_PROCESSED / "qc_log.csv"
EXCLUSION_LOG_FILE = DATA_PROCESSED / "excluded_subjects.log"

# Motion threshold in mm
MOTION_THRESHOLD_MM = 2.0

def setup_logging(log_file: Path) -> logging.Logger:
    """
    Setup logging configuration to write to both console and file.
    
    Args:
        log_file: Path to the log file.
        
    Returns:
        Configured logger instance.
    """
    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("preprocessing")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_subject_list() -> List[str]:
    """
    Get list of subjects from the raw data directory.
    
    Returns:
        List of subject IDs.
    """
    if not DATA_RAW.exists():
        raise FileNotFoundError(f"Raw data directory not found: {DATA_RAW}")
    
    subjects = []
    for item in sorted(DATA_RAW.iterdir()):
        if item.is_dir() and item.name.startswith("sub-"):
            subject_id = item.name.replace("sub-", "")
            subjects.append(subject_id)
    
    return subjects

def run_fmriprep_for_subject(
    subject_id: str,
    bids_root: Path,
    output_dir: Path,
    logger: logging.Logger,
    fmriprep_image: str = "nipreps/fmriprep:23.1.3"
) -> bool:
    """
    Run fmriprep for a single subject.
    
    Args:
        subject_id: Subject ID (without 'sub-' prefix).
        bids_root: Path to the BIDS root directory.
        output_dir: Path to the output directory.
        logger: Logger instance.
        fmriprep_image: Docker image tag for fmriprep.
        
    Returns:
        True if successful, False otherwise.
    """
    subject_dir = f"sub-{subject_id}"
    bids_subject_path = bids_root / subject_dir
    
    if not bids_subject_path.exists():
        logger.error(f"Subject directory not found: {bids_subject_path}")
        return False
    
    output_subject_dir = output_dir / subject_dir
    output_subject_dir.mkdir(parents=True, exist_ok=True)
    
    # Build fmriprep command
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{bids_root}:/bids:ro",
        "-v", f"{output_dir}:/output",
        "-v", f"{output_dir}/work:/work",
        "--env", "OMP_NUM_THREADS=2",
        "--env", "OPENBLAS_NUM_THREADS=2",
        "--env", "MKL_NUM_THREADS=2",
        "--env", "VECLIB_MAXIMUM_THREADS=2",
        "--env", "NUMEXPR_NUM_THREADS=2",
        fmriprep_image,
        "/bids", "/output", "participant",
        "--participant-label", subject_id,
        "--skip_bids_validation",
        "--output-spaces", "MNI152NLin2009cAsym",
        "--fs-no-reconall",
        "--cifti-output", "91k"
    ]
    
    logger.info(f"Running fmriprep for subject {subject_id}...")
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        elapsed_time = time.time() - start_time
        
        if result.returncode != 0:
            logger.error(f"fmriprep failed for subject {subject_id} after {elapsed_time:.2f}s")
            logger.error(f"STDERR: {result.stderr}")
            # Log deviation
            logger.warning(f"DEVIATION: fmriprep execution failed for {subject_id}")
            return False
        else:
            logger.info(f"fmriprep completed successfully for subject {subject_id} in {elapsed_time:.2f}s")
            return True
            
    except FileNotFoundError:
        logger.error("Docker not found. Please install Docker and try again.")
        logger.warning(f"DEVIATION: Docker not available for subject {subject_id}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running fmriprep for {subject_id}: {str(e)}")
        logger.warning(f"DEVIATION: Unexpected error during fmriprep for {subject_id}")
        return False

def process_qc_and_exclude(
    subject_id: str,
    bids_root: Path,
    output_dir: Path,
    logger: logging.Logger
) -> bool:
    """
    Process QC metrics and exclude subjects with excessive motion.
    
    Args:
        subject_id: Subject ID.
        bids_root: Path to the BIDS root directory.
        output_dir: Path to the output directory.
        logger: Logger instance.
        
    Returns:
        True if subject is valid, False if excluded.
    """
    # Get motion file path
    motion_file = get_motion_file(output_dir, subject_id)
    
    if not motion_file.exists():
        logger.warning(f"Motion file not found for subject {subject_id}")
        logger.warning(f"DEVIATION: Missing motion file for {subject_id}")
        return False
    
    # Parse motion parameters
    try:
        motion_data = parse_motion_parameters(motion_file)
        if motion_data is None:
            logger.warning(f"Could not parse motion file for subject {subject_id}")
            logger.warning(f"DEVIATION: Invalid motion file format for {subject_id}")
            return False
    except Exception as e:
        logger.error(f"Error parsing motion file for {subject_id}: {str(e)}")
        logger.warning(f"DEVIATION: Error parsing motion file for {subject_id}")
        return False
    
    # Calculate frame-wise displacement
    displacements = calculate_frame_displacement(motion_data)
    mean_displacement = sum(displacements) / len(displacements) if displacements else 0
    max_displacement = max(displacements) if displacements else 0
    
    # Check motion threshold
    is_valid = check_motion_threshold(mean_displacement, MOTION_THRESHOLD_MM)
    
    # Log QC metrics
    log_qc_metrics(
        subject_id=subject_id,
        mean_displacement=mean_displacement,
        max_displacement=max_displacement,
        is_valid=is_valid,
        log_file=QC_LOG_FILE
    )
    
    if not is_valid:
        logger.warning(f"Subject {subject_id} excluded: mean displacement {mean_displacement:.3f}mm > {MOTION_THRESHOLD_MM}mm")
        logger.warning(f"DEVIATION: Subject {subject_id} excluded due to excessive motion (mean={mean_displacement:.3f}mm, max={max_displacement:.3f}mm)")
        # Log to exclusion file
        with open(EXCLUSION_LOG_FILE, 'a') as f:
            f.write(f"{subject_id},motion,{mean_displacement:.3f},{max_displacement:.3f}\n")
        return False
    
    logger.info(f"Subject {subject_id} passed QC: mean={mean_displacement:.3f}mm, max={max_displacement:.3f}mm")
    return True

def log_preprocessing_deviations(
    deviations: List[Dict[str, Any]],
    logger: logging.Logger
) -> None:
    """
    Log preprocessing deviations to the log file.
    This function is called whenever a deviation is detected during preprocessing.
    
    Args:
        deviations: List of deviation dictionaries with keys:
            - subject_id: Subject ID (optional)
            - deviation_type: Type of deviation (e.g., 'motion', 'missing_file', 'error')
            - message: Detailed message about the deviation
            - timestamp: Timestamp of the deviation (optional)
        logger: Logger instance.
    """
    for dev in deviations:
        subject_id = dev.get('subject_id', 'N/A')
        deviation_type = dev.get('deviation_type', 'unknown')
        message = dev.get('message', 'No message provided')
        
        # Log as warning with DEVIATION prefix for easy filtering
        log_msg = f"DEVIATION [{deviation_type}]: {message}"
        if subject_id != 'N/A':
            log_msg = f"Subject {subject_id}: {log_msg}"
        
        logger.warning(log_msg)

def main():
    """
    Main function to orchestrate the preprocessing pipeline.
    """
    # Setup logging
    logger = setup_logging(LOG_FILE)
    logger.info("=" * 60)
    logger.info("Starting preprocessing pipeline")
    logger.info("=" * 60)
    
    # Ensure directories exist
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    DATA_DERIVATIVES.mkdir(parents=True, exist_ok=True)
    
    # Get subject list
    try:
        subjects = get_subject_list()
        logger.info(f"Found {len(subjects)} subjects in raw data")
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.warning("DEVIATION: Raw data directory missing, cannot proceed")
        sys.exit(1)
    
    if not subjects:
        logger.warning("No subjects found in raw data directory")
        logger.warning("DEVIATION: No subjects available for preprocessing")
        sys.exit(0)
    
    # Process each subject
    valid_subjects = []
    deviations = []
    
    for subject_id in subjects:
        logger.info(f"\nProcessing subject {subject_id}")
        
        # Run fmriprep
        fmriprep_success = run_fmriprep_for_subject(
            subject_id=subject_id,
            bids_root=DATA_RAW,
            output_dir=DATA_DERIVATIVES,
            logger=logger
        )
        
        if not fmriprep_success:
            deviations.append({
                'subject_id': subject_id,
                'deviation_type': 'fmriprep_failure',
                'message': 'fmriprep execution failed'
            })
            continue
        
        # Process QC
        qc_success = process_qc_and_exclude(
            subject_id=subject_id,
            bids_root=DATA_RAW,
            output_dir=DATA_DERIVATIVES,
            logger=logger
        )
        
        if not qc_success:
            deviations.append({
                'subject_id': subject_id,
                'deviation_type': 'motion_exclusion',
                'message': 'Subject excluded due to excessive motion'
            })
            continue
        
        valid_subjects.append(subject_id)
    
    # Log all deviations at the end
    if deviations:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Preprocessing Deviations Summary ({len(deviations)} total)")
        logger.info(f"{'=' * 60}")
        log_preprocessing_deviations(deviations, logger)
    
    # Write valid subjects list
    with open(VALID_SUBJECTS_FILE, 'w') as f:
        for subject_id in valid_subjects:
            f.write(f"{subject_id}\n")
    
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Preprocessing complete")
    logger.info(f"Valid subjects: {len(valid_subjects)}/{len(subjects)}")
    logger.info(f"Valid subjects list saved to: {VALID_SUBJECTS_FILE}")
    logger.info(f"{'=' * 60}")
    
    # Return valid subjects for downstream use
    return valid_subjects

if __name__ == "__main__":
    main()
