"""
Preprocessing Deviation Logger for User Story 1.

This module implements logging for all pipeline deviations (slice-time, motion, 
normalization, smoothing) to data/processed/preprocessing.log in JSON format.

It specifically logs deviations for subjects with motion > 2mm or fmriprep failures,
adhering to Constitution Principle VI (Transparency and Reproducibility).
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from utils import (
    setup_logging, 
    get_bids_subject_path, 
    get_fmriprep_output_path,
    get_motion_file,
    parse_motion_parameters,
    check_motion_threshold
)


PREPROCESSING_LOG_PATH = Path("data/processed/preprocessing.log")
MOTION_THRESHOLD_MM = 2.0


def load_existing_log(log_path: Path) -> List[Dict[str, Any]]:
    """Load existing log entries if file exists."""
    if not log_path.exists():
        return []
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            
            # JSON Lines format: each line is a valid JSON object
            entries = []
            for line in content.split('\n'):
                if line.strip():
                    entries.append(json.loads(line))
            return entries
    except (json.JSONDecodeError, IOError) as e:
        logging.warning(f"Could not parse existing log file: {e}. Starting fresh.")
        return []


def save_log_entry(log_path: Path, entry: Dict[str, Any]) -> None:
    """Append a single log entry to the JSON Lines log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def detect_slice_time_deviation(bids_subject_path: Path, fmriprep_output_path: Path) -> Optional[Dict[str, Any]]:
    """
    Detect slice-time correction deviations.
    
    Checks if slice-time correction was skipped or if non-standard parameters were used.
    """
    deviations = []
    
    # Check for slice-time correction in fmriprep logs
    log_files = list(fmriprep_output_path.glob("**/log*.txt"))
    for log_file in log_files:
        try:
            content = log_file.read_text(encoding='utf-8', errors='ignore')
            if "SliceTiming" in content or "slice timing" in content.lower():
                # Check for warnings or errors related to slice timing
                if "skipped" in content.lower() or "warning" in content.lower():
                    deviations.append({
                        "type": "slice_time",
                        "severity": "warning",
                        "message": "Slice-time correction may have been skipped or used non-standard parameters",
                        "details": {
                            "log_file": str(log_file.relative_to(fmriprep_output_path))
                        }
                    })
        except Exception as e:
            logging.debug(f"Could not read log file {log_file}: {e}")
    
    if deviations:
        return {
            "category": "slice_time",
            "deviations": deviations
        }
    return None


def detect_motion_deviation(bids_subject_path: Path, motion_file: Path) -> Optional[Dict[str, Any]]:
    """
    Detect motion-related deviations.
    
    Identifies subjects with excessive motion (>2mm) and logs specific frame displacements.
    """
    if not motion_file.exists():
        return {
            "category": "motion",
            "deviations": [{
                "type": "missing_motion_file",
                "severity": "error",
                "message": f"Motion parameters file not found: {motion_file}",
                "details": {}
            }]
        }
    
    try:
        translations, rotations = parse_motion_parameters(motion_file)
        frame_displacements = calculate_frame_displacement(translations, rotations)
        
        # Check for subjects exceeding threshold
        max_displacement = max(frame_displacements) if frame_displacements else 0
        exceeded_frames = [i for i, disp in enumerate(frame_displacements) if disp > MOTION_THRESHOLD_MM]
        
        if max_displacement > MOTION_THRESHOLD_MM:
            return {
                "category": "motion",
                "deviations": [{
                    "type": "excessive_motion",
                    "severity": "warning",
                    "message": f"Subject exceeded motion threshold ({MOTION_THRESHOLD_MM}mm)",
                    "details": {
                        "max_displacement_mm": round(max_displacement, 3),
                        "exceeded_frame_indices": exceeded_frames,
                        "num_exceeded_frames": len(exceeded_frames),
                        "total_frames": len(frame_displacements)
                    }
                }]
            }
    except Exception as e:
        return {
            "category": "motion",
            "deviations": [{
                "type": "motion_parse_error",
                "severity": "error",
                "message": f"Failed to parse motion parameters: {str(e)}",
                "details": {}
            }]
        }
    
    return None


def detect_normalization_deviation(fmriprep_output_path: Path) -> Optional[Dict[str, Any]]:
    """
    Detect normalization deviations.
    
    Checks if spatial normalization to MNI space was successful or if alternative spaces were used.
    """
    deviations = []
    
    # Check for MNI space output
    mni_spaces = list(fmriprep_output_path.glob("**/space-MNI*/**/*.nii.gz"))
    if not mni_spaces:
        deviations.append({
            "type": "no_mni_normalization",
            "severity": "warning",
            "message": "No MNI-normalized output found; subject may not have been normalized to standard space",
            "details": {}
        })
    
    # Check for non-standard spaces
    all_spaces = list(fmriprep_output_path.glob("**/space-*/**/*.nii.gz"))
    non_mni_spaces = [s for s in all_spaces if "MNI" not in str(s)]
    if non_mni_spaces:
        deviations.append({
            "type": "non_standard_normalization",
            "severity": "info",
            "message": f"Found {len(non_mni_spaces)} non-MNI normalized outputs",
            "details": {
                "spaces": [str(s.parent.relative_to(fmriprep_output_path)) for s in non_mni_spaces]
            }
        })
    
    if deviations:
        return {
            "category": "normalization",
            "deviations": deviations
        }
    return None


def detect_smoothing_deviation(fmriprep_output_path: Path) -> Optional[Dict[str, Any]]:
    """
    Detect smoothing deviations.
    
    fmriprep does not apply smoothing by default, so this checks if smoothing 
    was applied in subsequent steps or if it was explicitly skipped.
    """
    deviations = []
    
    # Check for smoothed outputs
    smoothed_files = list(fmriprep_output_path.glob("**/*smooth*.nii.gz"))
    if smoothed_files:
        deviations.append({
            "type": "smoothing_applied",
            "severity": "info",
            "message": f"Found {len(smoothed_files)} smoothed outputs in derivatives",
            "details": {
                "files": [str(f.relative_to(fmriprep_output_path)) for f in smoothed_files]
            }
        })
    else:
        deviations.append({
            "type": "no_smoothing",
            "severity": "info",
            "message": "No smoothing applied (fmriprep default behavior)",
            "details": {}
        })
    
    return {
        "category": "smoothing",
        "deviations": deviations
    }


def detect_fmriprep_failure(bids_subject_path: Path, fmriprep_output_path: Path) -> Optional[Dict[str, Any]]:
    """
    Detect fmriprep execution failures.
    
    Checks for missing outputs, error logs, or incomplete processing.
    """
    deviations = []
    
    # Check for essential output files
    essential_outputs = [
        "sub-*/func/*_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz",
        "sub-*/func/*_space-MNI152NLin2009cAsym_desc-confounds_timeseries.tsv"
    ]
    
    for pattern in essential_outputs:
        outputs = list(fmriprep_output_path.glob(pattern))
        if not outputs:
            deviations.append({
                "type": "missing_essential_output",
                "severity": "error",
                "message": f"Essential output not found: {pattern}",
                "details": {"pattern": pattern}
            })
    
    # Check for error logs
    error_logs = list(fmriprep_output_path.glob("**/*error*.txt"))
    error_logs += list(fmriprep_output_path.glob("**/log/*ERROR*"))
    if error_logs:
        deviations.append({
            "type": "fmriprep_error_log",
            "severity": "error",
            "message": f"Found {len(error_logs)} error log files",
            "details": {
                "error_files": [str(e.relative_to(fmriprep_output_path)) for e in error_logs]
            }
        })
    
    if deviations:
        return {
            "category": "fmriprep_failure",
            "deviations": deviations
        }
    return None


def log_preprocessing_deviations(
    subject_id: str,
    bids_root: Path,
    fmriprep_derivatives: Path,
    log_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Log all preprocessing deviations for a single subject.
    
    This function checks for deviations in:
    - Slice-time correction
    - Motion parameters (>2mm threshold)
    - Normalization to MNI space
    - Smoothing
    - fmriprep execution failures
    
    Args:
        subject_id: BIDS subject ID (e.g., 'sub-01')
        bids_root: Path to the BIDS dataset root
        fmriprep_derivatives: Path to fmriprep derivatives directory
        log_path: Optional custom path for the log file (defaults to PREPROCESSING_LOG_PATH)
    
    Returns:
        Dictionary containing the log entry for this subject
    """
    log_path = log_path or PREPROCESSING_LOG_PATH
    bids_subject_path = bids_root / subject_id
    fmriprep_output_path = fmriprep_derivatives / subject_id
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "subject_id": subject_id,
        "bids_path": str(bids_subject_path),
        "fmriprep_output_path": str(fmriprep_output_path),
        "deviations": []
    }
    
    # Check for fmriprep failure first
    fmriprep_failure = detect_fmriprep_failure(bids_subject_path, fmriprep_output_path)
    if fmriprep_failure:
        entry["deviations"].append(fmriprep_failure)
        entry["has_failure"] = True
    else:
        entry["has_failure"] = False
    
    # Check motion (always log if >2mm)
    motion_file = get_motion_file(fmriprep_output_path)
    motion_deviation = detect_motion_deviation(bids_subject_path, motion_file)
    if motion_deviation:
        entry["deviations"].append(motion_deviation)
        # Check if motion exceeded threshold
        for dev in motion_deviation.get("deviations", []):
            if dev.get("type") == "excessive_motion":
                entry["exceeded_motion_threshold"] = True
                break
    
    # Check slice-time
    slice_time_deviation = detect_slice_time_deviation(bids_subject_path, fmriprep_output_path)
    if slice_time_deviation:
        entry["deviations"].append(slice_time_deviation)
    
    # Check normalization
    norm_deviation = detect_normalization_deviation(fmriprep_output_path)
    if norm_deviation:
        entry["deviations"].append(norm_deviation)
    
    # Check smoothing
    smooth_deviation = detect_smoothing_deviation(fmriprep_output_path)
    if smooth_deviation:
        entry["deviations"].append(smooth_deviation)
    
    # Determine if this subject should be logged (has deviations OR failure OR high motion)
    should_log = (
        entry["has_failure"] or 
        entry.get("exceeded_motion_threshold", False) or
        len(entry["deviations"]) > 0
    )
    
    if should_log:
        save_log_entry(log_path, entry)
        logging.info(f"Logged preprocessing deviations for {subject_id}: {len(entry['deviations'])} issues found")
    else:
        logging.debug(f"No deviations logged for {subject_id}")
    
    return entry


def log_all_subjects_deviations(
    valid_subjects: List[str],
    bids_root: Path,
    fmriprep_derivatives: Path,
    log_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Log preprocessing deviations for all valid subjects.
    
    Args:
        valid_subjects: List of subject IDs to process
        bids_root: Path to the BIDS dataset root
        fmriprep_derivatives: Path to fmriprep derivatives directory
        log_path: Optional custom path for the log file
    
    Returns:
        List of all log entries created
    """
    log_path = log_path or PREPROCESSING_LOG_PATH
    all_entries = []
    
    for subject_id in valid_subjects:
        try:
            entry = log_preprocessing_deviations(
                subject_id, 
                bids_root, 
                fmriprep_derivatives, 
                log_path
            )
            all_entries.append(entry)
        except Exception as e:
            logging.error(f"Failed to log deviations for {subject_id}: {e}")
            # Log the error as a deviation entry
            error_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "subject_id": subject_id,
                "error": str(e),
                "deviations": [{
                    "type": "processing_error",
                    "severity": "error",
                    "message": f"Failed to process subject: {str(e)}",
                    "details": {}
                }]
            }
            save_log_entry(log_path, error_entry)
            all_entries.append(error_entry)
    
    return all_entries


def main():
    """
    Main entry point for logging preprocessing deviations.
    
    This script should be run after fmriprep completion to generate
    a comprehensive log of all pipeline deviations.
    """
    # Setup logging
    logger = setup_logging("preprocessing_logger", level=logging.INFO)
    logger.info("Starting preprocessing deviation logging...")
    
    # Default paths
    bids_root = Path("data/raw")
    fmriprep_derivatives = Path("data/derivatives")
    log_path = PREPROCESSING_LOG_PATH
    
    # Load valid subjects
    valid_subjects_file = Path("data/processed/valid_subjects.txt")
    if not valid_subjects_file.exists():
        logger.error(f"Valid subjects file not found: {valid_subjects_file}")
        sys.exit(1)
    
    with open(valid_subjects_file, 'r') as f:
        valid_subjects = [line.strip() for line in f if line.strip()]
    
    logger.info(f"Processing {len(valid_subjects)} valid subjects...")
    
    # Log deviations for all subjects
    entries = log_all_subjects_deviations(
        valid_subjects,
        bids_root,
        fmriprep_derivatives,
        log_path
    )
    
    # Summary
    total_deviations = sum(len(entry.get("deviations", [])) for entry in entries)
    subjects_with_failures = sum(1 for entry in entries if entry.get("has_failure"))
    subjects_with_high_motion = sum(1 for entry in entries if entry.get("exceeded_motion_threshold", False))
    
    logger.info(f"Logging complete. Total entries: {len(entries)}")
    logger.info(f"Total deviations logged: {total_deviations}")
    logger.info(f"Subjects with fmriprep failures: {subjects_with_failures}")
    logger.info(f"Subjects with high motion (>2mm): {subjects_with_high_motion}")
    logger.info(f"Log file: {log_path.resolve()}")


if __name__ == "__main__":
    main()