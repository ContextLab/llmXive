"""
Quality Control module for fMRI data analysis.
Handles motion parameter calculation, condition verification, and subject filtering.
"""
import os
import json
import logging
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Literal

from src.config import load_config
from src.exceptions import DataUnavailableError, InsufficientDataError
from src.integrity import update_hashes

# Configure logger
logger = logging.getLogger(__name__)

# Constants
MOTION_THRESHOLD_MM = 3.0
MIN_SUBJECTS_REQUIRED = 10

def load_motion_parameters(subject_dir: Path) -> Dict[str, Any]:
    """
    Load motion parameters from a subject's confounds file.
    
    Args:
        subject_dir: Path to the subject's directory containing confounds.
        
    Returns:
        Dictionary containing motion parameters.
        
    Raises:
        DataUnavailableError: If confounds file is missing or invalid.
    """
    # Look for standard confounds files (fMRIPrep style)
    confounds_patterns = [
        "confounds_regressors.tsv",
        "confounds_timeseries.tsv",
        "confounds.tsv"
    ]
    
    confounds_file = None
    for pattern in confounds_patterns:
        candidate = subject_dir / pattern
        if candidate.exists():
            confounds_file = candidate
            break
    
    if not confounds_file:
        raise DataUnavailableError(f"Confounds file not found in {subject_dir}")
    
    try:
        import pandas as pd
        confounds_df = pd.read_csv(confounds_file, sep='\t')
        return confounds_df.to_dict('records')[0] if len(confounds_df) > 0 else {}
    except Exception as e:
        raise DataUnavailableError(f"Failed to parse confounds file: {e}")

def calculate_framewise_displacement(confounds: Dict[str, Any]) -> float:
    """
    Calculate Framewise Displacement (FD) from motion parameters.
    
    FD is calculated as the sum of absolute differences of motion parameters
    between consecutive time points (Power et al., 2012).
    
    Args:
        confounds: Dictionary containing motion parameters (rotations in radians, translations in mm).
        
    Returns:
        Mean Framewise Displacement in mm.
    """
    # Expected columns (fMRIPrep standard)
    trans_x = confounds.get('trans_x', [])
    trans_y = confounds.get('trans_y', [])
    trans_z = confounds.get('trans_z', [])
    rot_x = confounds.get('rot_x', [])
    rot_y = confounds.get('rot_y', [])
    rot_z = confounds.get('rot_z', [])
    
    if not trans_x or not rot_x:
        logger.warning("Motion parameters missing, returning 0.0 FD")
        return 0.0
    
    # Ensure arrays
    trans_x = np.array(trans_x)
    trans_y = np.array(trans_y)
    trans_z = np.array(trans_z)
    rot_x = np.array(rot_x)
    rot_y = np.array(rot_y)
    rot_z = np.array(rot_z)
    
    # Convert rotations from radians to mm (assuming 50mm radius)
    rot_x_mm = np.abs(np.diff(rot_x)) * 50.0
    rot_y_mm = np.abs(np.diff(rot_y)) * 50.0
    rot_z_mm = np.abs(np.diff(rot_z)) * 50.0
    
    # Calculate translation differences
    trans_x_diff = np.abs(np.diff(trans_x))
    trans_y_diff = np.abs(np.diff(trans_y))
    trans_z_diff = np.abs(np.diff(trans_z))
    
    # Sum of absolute differences
    fd = trans_x_diff + trans_y_diff + trans_z_diff + rot_x_mm + rot_y_mm + rot_z_mm
    
    return float(np.mean(fd))

def calculate_subject_motion_metrics(subject_dir: Path) -> float:
    """
    Calculate motion metrics for a single subject.
    
    Args:
        subject_dir: Path to subject directory.
        
    Returns:
        Mean Framewise Displacement in mm.
    """
    confounds = load_motion_parameters(subject_dir)
    return calculate_framewise_displacement(confounds)

def verify_conditions(subject_dir: Path) -> Literal["valid", "invalid"]:
    """
    Verify that a subject has valid time-series data for both Inclusion and Exclusion conditions.
    
    Args:
        subject_dir: Path to subject directory.
        
    Returns:
        "valid" if both conditions exist, "invalid" otherwise.
    """
    # Check for events file which should contain trial types
    events_patterns = [
        "events.tsv",
        "sub-*_events.tsv"
    ]
    
    events_file = None
    for pattern in events_patterns:
        for f in subject_dir.glob(pattern):
            events_file = f
            break
        if events_file:
            break
    
    if not events_file:
        logger.warning(f"No events file found for {subject_dir}")
        return "invalid"
    
    try:
        import pandas as pd
        events_df = pd.read_csv(events_file, sep='\t')
        
        # Check for required trial types
        if 'trial_type' not in events_df.columns:
            logger.warning(f"No trial_type column in events for {subject_dir}")
            return "invalid"
        
        trial_types = set(events_df['trial_type'].dropna().astype(str).unique())
        
        # Check for inclusion and exclusion trials
        has_inclusion = any('inclusion' in t.lower() for t in trial_types)
        has_exclusion = any('exclusion' in t.lower() for t in trial_types)
        
        if has_inclusion and has_exclusion:
            return "valid"
        else:
            logger.info(f"Subject {subject_dir.name}: missing inclusion={not has_inclusion}, exclusion={not has_exclusion}")
            return "invalid"
            
    except Exception as e:
        logger.error(f"Error verifying conditions for {subject_dir}: {e}")
        return "invalid"

def filter_by_motion_threshold(subject_metrics: List[Dict[str, Any]], threshold: float = MOTION_THRESHOLD_MM) -> List[Dict[str, Any]]:
    """
    Filter subjects based on motion threshold.
    
    Args:
        subject_metrics: List of subject metric dictionaries.
        threshold: Maximum allowed mean FD in mm.
        
    Returns:
        Filtered list with 'retained' flag set.
    """
    for subject in subject_metrics:
        subject['retained'] = subject['motion_metric'] <= threshold
    return subject_metrics

def check_subject_count(subject_list: List[Dict[str, Any]], min_count: int = MIN_SUBJECTS_REQUIRED) -> None:
    """
    Check if the number of retained subjects meets the minimum requirement.
    
    Args:
        subject_list: List of subject metric dictionaries.
        min_count: Minimum number of subjects required.
        
    Raises:
        InsufficientDataError: If retained subjects are below threshold.
    """
    retained_count = sum(1 for s in subject_list if s.get('retained', False))
    if retained_count < min_count:
        raise InsufficientDataError(f"Insufficient subjects (N={retained_count}) for valid permutation test.")

def run_qc_pipeline(data_dir: Path, output_dir: Path, config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Run the full QC pipeline on a dataset.
    
    Args:
        data_dir: Path to the raw data directory containing subject folders.
        output_dir: Path to output processed data directory.
        config: Optional configuration dictionary.
        
    Returns:
        List of subject QC records.
    """
    if config is None:
        config = load_config()
    
    motion_threshold = config.get('qc', {}).get('motion_threshold_mm', MOTION_THRESHOLD_MM)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all subject directories
    subject_dirs = sorted([d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith('sub-')])
    
    if not subject_dirs:
        raise DataUnavailableError(f"No subject directories found in {data_dir}")
    
    logger.info(f"Processing {len(subject_dirs)} subjects for QC...")
    
    subject_qc_list = []
    
    for subject_dir in subject_dirs:
        subject_id = subject_dir.name
        logger.info(f"Processing {subject_id}...")
        
        try:
            # Calculate motion metric
            motion_metric = calculate_subject_motion_metrics(subject_dir)
            
            # Verify conditions
            condition_status = verify_conditions(subject_dir)
            
            # Determine retention
            retained = (motion_metric <= motion_threshold) and (condition_status == "valid")
            
            record = {
                'subject_id': subject_id,
                'motion_metric': float(motion_metric),
                'condition_status': condition_status,
                'retained': retained
            }
            
            subject_qc_list.append(record)
            
        except Exception as e:
            logger.error(f"Error processing {subject_id}: {e}")
            # Add record with error status
            subject_qc_list.append({
                'subject_id': subject_id,
                'motion_metric': 0.0,
                'condition_status': 'invalid',
                'retained': False,
                'error': str(e)
            })
    
    # Sort by subject_id for consistency
    subject_qc_list.sort(key=lambda x: x['subject_id'])
    
    # Write QC list
    qc_list_path = output_dir / 'subject_qc_list.json'
    with open(qc_list_path, 'w') as f:
        json.dump(subject_qc_list, f, indent=2)
    
    # Generate subjects metadata (only retained subjects)
    retained_subjects = [s for s in subject_qc_list if s['retained']]
    metadata_path = output_dir / 'subjects_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump({
            'retained_subjects': [s['subject_id'] for s in retained_subjects],
            'total_retained': len(retained_subjects),
            'total_excluded': len(subject_qc_list) - len(retained_subjects),
            'motion_threshold_mm': motion_threshold
        }, f, indent=2)
    
    # Update integrity hashes
    update_hashes(str(qc_list_path))
    update_hashes(str(metadata_path))
    
    logger.info(f"QC complete. Retained: {len(retained_subjects)}, Excluded: {len(subject_qc_list) - len(retained_subjects)}")
    
    return subject_qc_list

def main():
    """Main entry point for QC pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run QC pipeline on fMRI dataset')
    parser.add_argument('--data-dir', type=str, required=True, help='Path to raw data directory')
    parser.add_argument('--output-dir', type=str, required=True, help='Path to output directory')
    parser.add_argument('--config', type=str, default=None, help='Path to config file')
    
    args = parser.parse_args()
    
    setup_logging()
    
    config = load_config(args.config) if args.config else load_config()
    
    try:
        run_qc_pipeline(
            data_dir=Path(args.data_dir),
            output_dir=Path(args.output_dir),
            config=config
        )
    except Exception as e:
        logger.error(f"QC pipeline failed: {e}")
        raise

def setup_logging():
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )