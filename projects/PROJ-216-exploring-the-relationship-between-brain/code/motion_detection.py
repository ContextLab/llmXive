import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

def load_motion_metrics(interim_dir: Path) -> Dict[str, float]:
    """
    Load motion metrics (e.g., Framewise Displacement) from preprocessed subject logs.
    Assumes each subject has a motion log in data/interim/subj_*/func/motion_metrics.json
    
    Args:
        interim_dir: Path to the interim directory containing preprocessed subjects
        
    Returns:
        Dictionary mapping subject_id to their mean FD value
    """
    motion_metrics = {}
    
    if not interim_dir.exists():
        logger.warning(f"Interim directory not found: {interim_dir}")
        return motion_metrics
        
    for subject_path in interim_dir.iterdir():
        if not subject_path.is_dir():
            continue
            
        subject_id = subject_path.name
        motion_log_path = subject_path / "func" / "motion_metrics.json"
        
        if motion_log_path.exists():
            try:
                with open(motion_log_path, 'r') as f:
                    data = json.load(f)
                    # Extract mean FD, defaulting to 0 if not found
                    mean_fd = data.get('mean_fd', 0.0)
                    motion_metrics[subject_id] = mean_fd
                    logger.info(f"Loaded motion metrics for {subject_id}: FD={mean_fd:.4f}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error parsing motion metrics for {subject_id}: {e}")
        else:
            logger.warning(f"Motion metrics not found for {subject_id}: {motion_log_path}")
            
    return motion_metrics

def get_valid_subjects(motion_metrics: Dict[str, float], threshold: float = 0.5) -> List[str]:
    """
    Identify subjects with acceptable motion levels (FD <= threshold).
    
    Args:
        motion_metrics: Dictionary of subject_id -> mean FD
        threshold: Maximum acceptable FD (default 0.5mm)
        
    Returns:
        List of subject IDs that pass the motion threshold
    """
    valid = []
    for subj_id, fd in motion_metrics.items():
        if fd <= threshold:
            valid.append(subj_id)
            logger.info(f"Subject {subj_id} passed motion threshold: FD={fd:.4f} <= {threshold}")
        else:
            logger.info(f"Subject {subj_id} EXCLUDED due to motion: FD={fd:.4f} > {threshold}")
    return valid

def detect_motion_artifacts(motion_metrics: Dict[str, float], threshold: float = 0.5) -> Dict[str, str]:
    """
    Detect subjects with excessive motion artifacts.
    
    Args:
        motion_metrics: Dictionary of subject_id -> mean FD
        threshold: Maximum acceptable FD
        
    Returns:
        Dictionary mapping excluded subject_id to reason
    """
    excluded = {}
    for subj_id, fd in motion_metrics.items():
        if fd > threshold:
            excluded[subj_id] = f"FD > {threshold}mm (actual: {fd:.4f}mm)"
    return excluded

def write_motion_exclusion_log(excluded_subjects: Dict[str, str], output_path: Path) -> None:
    """
    Write excluded subjects to log file with format:
    SubjectID: Reason (e.g., FD > 0.5mm)
    
    Args:
        excluded_subjects: Dictionary of subject_id -> exclusion reason
        output_path: Path to the output log file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for subj_id, reason in excluded_subjects.items():
            f.write(f"{subj_id}: {reason}\n")
            
    logger.info(f"Wrote {len(excluded_subjects)} excluded subjects to {output_path}")

def save_valid_subjects(valid_subjects: List[str], output_path: Path) -> None:
    """
    Save list of valid subject IDs to a JSON file for downstream processing.
    
    Args:
        valid_subjects: List of subject IDs that passed motion screening
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump({
            "valid_subjects": valid_subjects,
            "count": len(valid_subjects),
            "threshold_used": 0.5
        }, f, indent=2)
        
    logger.info(f"Saved {len(valid_subjects)} valid subjects to {output_path}")

def main():
    """
    Main entry point for motion artifact detection and subject exclusion.
    This implements T018b: Proceed with Available Subjects after motion exclusion.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    interim_dir = project_root / "data" / "interim"
    processed_dir = project_root / "data" / "processed"
    
    exclusion_log_path = processed_dir / "excluded_subjects.log"
    valid_subjects_path = processed_dir / "valid_subjects.json"
    
    logger.info("Starting motion artifact detection...")
    logger.info(f"Interim directory: {interim_dir}")
    logger.info(f"Output paths: {exclusion_log_path}, {valid_subjects_path}")
    
    # Load motion metrics
    motion_metrics = load_motion_metrics(interim_dir)
    
    if not motion_metrics:
        logger.warning("No motion metrics found. Proceeding with all subjects if any exist.")
        # If no metrics found, we can't exclude anyone, so we proceed with all found subjects
        # This handles the case where preprocessing might not have generated motion logs
        all_subjects = [d.name for d in interim_dir.iterdir() if d.is_dir()]
        motion_metrics = {s: 0.0 for s in all_subjects}
    
    # Detect excluded subjects
    excluded = detect_motion_artifacts(motion_metrics, threshold=0.5)
    
    # Get valid subjects
    valid_subjects = get_valid_subjects(motion_metrics, threshold=0.5)
    
    # Write outputs
    write_motion_exclusion_log(excluded, exclusion_log_path)
    save_valid_subjects(valid_subjects, valid_subjects_path)
    
    # Summary
    logger.info(f"Motion detection complete.")
    logger.info(f"Total subjects processed: {len(motion_metrics)}")
    logger.info(f"Subjects excluded: {len(excluded)}")
    logger.info(f"Subjects retained: {len(valid_subjects)}")
    
    if len(valid_subjects) == 0:
        logger.error("No valid subjects remain after motion exclusion. Halting pipeline.")
        sys.exit(1)
        
    return valid_subjects

if __name__ == "__main__":
    main()
