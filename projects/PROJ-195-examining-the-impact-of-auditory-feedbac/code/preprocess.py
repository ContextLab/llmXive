import os
import sys
import subprocess
import logging
import time
import re
from pathlib import Path
from typing import List, Optional, Dict

# Import from utils as per API surface
from utils import (
    get_bids_subject_path,
    get_fmriprep_output_path,
    get_motion_file,
    parse_motion_parameters,
    calculate_frame_displacement,
    check_motion_threshold,
    log_qc_metrics,
    get_event_file_path,
    validate_event_labels
)

# Import from subject_filter as per API surface
from subject_filter import (
    setup_logging as sf_setup_logging,
    load_qc_log,
    filter_valid_subjects,
    write_valid_subjects
)

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Configure logging for the preprocessing pipeline.
    Creates a dedicated logger that writes to both console and a log file.
    """
    if log_file is None:
        log_file = Path("data/processed/preprocessing.log")
    
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("preprocessing")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates in repeated runs
    if logger.handlers:
        logger.handlers.clear()
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def get_subject_list(bids_root: Path) -> List[str]:
    """
    Extract list of subject IDs from the BIDS directory.
    Returns list of subject IDs (e.g., ['sub-01', 'sub-02']).
    """
    subjects = []
    if bids_root.exists():
        for item in bids_root.iterdir():
            if item.is_dir() and item.name.startswith("sub-"):
                subjects.append(item.name)
    return sorted(subjects)

def run_fmriprep_for_subject(
    bids_root: Path,
    subject_id: str,
    output_dir: Path,
    logger: logging.Logger,
    n_cpus: int = 2,
    fmriprep_version: str = "23.1.3"
) -> bool:
    """
    Run fmriprep for a single subject.
    Returns True if successful, False otherwise.
    
    Logs deviations to preprocessing.log as per Constitution Principle VI.
    """
    start_time = time.time()
    bids_subject_path = get_bids_subject_path(bids_root, subject_id)
    
    if not bids_subject_path.exists():
        logger.error(f"Subject {subject_id} not found in BIDS root")
        return False
    
    output_subject_path = output_dir / subject_id
    output_subject_path.mkdir(parents=True, exist_ok=True)
    
    docker_image = f"nipreps/fmriprep:{fmriprep_version}"
    
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{bids_root}:/bids:ro",
        "-v", f"{output_dir}:/output",
        "-v", f"{output_subject_path}:/scratch",
        "-e", "OMP_NUM_THREADS=1",
        docker_image,
        "/bids",
        "/output",
        "participant",
        "--participant-label", subject_id,
        "--skip_bids_validation",
        "--n-cpus", str(n_cpus),
        "--output-spaces", "MNI152NLin2009cAsym",
        "--fs-license-file", "/opt/freesurfer/license.txt"
    ]
    
    # Log deviation if Docker is not available
    try:
        subprocess.run(["docker", "ps"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        deviation_msg = f"DEV: Docker not available for {subject_id}. Skipping preprocessing."
        logger.warning(deviation_msg)
        return False
    
    logger.info(f"Starting fmriprep for {subject_id}...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - start_time
        
        if result.returncode != 0:
            deviation_msg = (
                f"DEV: fmriprep failed for {subject_id} "
                f"after {elapsed:.1f}s. Exit code: {result.returncode}. "
                f"Error: {result.stderr[:200]}"
            )
            logger.error(deviation_msg)
            return False
        
        logger.info(f"Completed {subject_id} in {elapsed:.1f}s")
        return True
        
    except Exception as e:
        deviation_msg = f"DEV: Exception running fmriprep for {subject_id}: {str(e)}"
        logger.error(deviation_msg)
        return False

def process_qc_and_exclude(
    subject_id: str,
    output_dir: Path,
    logger: logging.Logger,
    motion_threshold_mm: float = 2.0
) -> bool:
    """
    Parse fmriprep logs for motion QC and determine if subject should be excluded.
    Logs deviations and QC metrics.
    
    Returns True if subject passes QC, False otherwise.
    """
    motion_file = get_motion_file(output_dir, subject_id)
    
    if not motion_file.exists():
        deviation_msg = (
            f"DEV: Motion file missing for {subject_id}. "
            f"Expected: {motion_file}. Excluding."
        )
        logger.warning(deviation_msg)
        return False
    
    try:
        displacements = parse_motion_parameters(motion_file)
        max_disp = calculate_frame_displacement(displacements)
        
        passes = check_motion_threshold(max_disp, motion_threshold_mm)
        
        if not passes:
            deviation_msg = (
                f"DEV: Motion threshold exceeded for {subject_id}. "
                f"Max displacement: {max_disp:.2f}mm (threshold: {motion_threshold_mm}mm). Excluding."
            )
            logger.warning(deviation_msg)
            return False
        
        log_qc_metrics(logger, subject_id, max_disp)
        return True
        
    except Exception as e:
        deviation_msg = (
            f"DEV: Error parsing motion parameters for {subject_id}: {str(e)}. Excluding."
        )
        logger.error(deviation_msg)
        return False

def log_preprocessing_deviations(
    log_file: Path,
    deviations: List[str]
) -> None:
    """
    Append a batch of deviation messages to the preprocessing log.
    This function ensures all deviations are recorded in a structured format.
    
    Args:
        log_file: Path to the preprocessing log file.
        deviations: List of deviation message strings.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'a') as f:
        for msg in deviations:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - DEV - {msg}\n")

def main():
    """
    Main entry point for the preprocessing pipeline.
    Orchestrates downloading (if needed), running fmriprep, and QC.
    """
    bids_root = Path("data/raw")
    output_dir = Path("data/derivatives")
    valid_subjects_file = Path("data/processed/valid_subjects.txt")
    
    logger = setup_logging(Path("data/processed/preprocessing.log"))
    logger.info("Starting preprocessing pipeline...")
    
    subjects = get_subject_list(bids_root)
    if not subjects:
        logger.error("No subjects found in BIDS directory")
        sys.exit(1)
    
    logger.info(f"Found {len(subjects)} subjects: {', '.join(subjects)}")
    
    valid_subjects = []
    deviations = []
    
    for subject in subjects:
        # Run fmriprep
        if not run_fmriprep_for_subject(bids_root, subject, output_dir, logger):
            deviations.append(f"Preprocessing failed for {subject}")
            continue
        
        # QC check
        if process_qc_and_exclude(subject, output_dir, logger):
            valid_subjects.append(subject)
        else:
            deviations.append(f"QC failed for {subject}")
    
    # Log all deviations at the end
    if deviations:
        log_preprocessing_deviations(
            Path("data/processed/preprocessing.log"),
            deviations
        )
    
    # Write valid subjects list
    write_valid_subjects(valid_subjects_file, valid_subjects)
    
    logger.info(f"Preprocessing complete. {len(valid_subjects)} subjects passed QC.")
    logger.info(f"Valid subjects saved to {valid_subjects_file}")

if __name__ == "__main__":
    main()
