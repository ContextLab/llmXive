import os
import sys
import csv
import json
import logging
import numpy as np
from pathlib import Path

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.download import check_motion_parameters_exist
from preprocessing.metadata import load_subject_status

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MOTION_THRESHOLD_MM = 2.0
DATA_DIR = Path(__file__).parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
METADATA_DIR = DATA_DIR / "metadata"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure directories exist
METADATA_DIR.mkdir(parents=True, exist_ok=True)

def get_all_subject_ids() -> list:
    """
    Get all subject IDs from the processed connectivity matrices or raw data.
    Returns a list of subject ID strings.
    """
    # Try to get from processed matrices first
    processed_matrices_dir = PROCESSED_DIR
    if processed_matrices_dir.exists():
        csv_files = list(processed_matrices_dir.glob("*.csv"))
        if csv_files:
            # Assume filenames are like 'sub-XXX_matrix.csv'
            subjects = []
            for f in csv_files:
                stem = f.stem
                if stem.endswith("_matrix"):
                    sub_id = stem.replace("_matrix", "")
                    subjects.append(sub_id)
            if subjects:
                logger.info(f"Found {len(subjects)} subjects from processed matrices")
                return sorted(subjects)
    
    # Fallback: try to get from raw data structure
    if RAW_DIR.exists():
        # Look for subject directories (common pattern: sub-XXX)
        sub_dirs = [d for d in RAW_DIR.iterdir() if d.is_dir() and d.name.startswith("sub-")]
        if sub_dirs:
            subjects = [d.name.replace("sub-", "") for d in sub_dirs]
            logger.info(f"Found {len(subjects)} subjects from raw data directories")
            return sorted(subjects)
    
    # Last resort: try to get from existing subject_status.csv
    status_file = METADATA_DIR / "subject_status.csv"
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                reader = csv.DictReader(f)
                subjects = [row['subject_id'] for row in reader]
                if subjects:
                    logger.info(f"Found {len(subjects)} subjects from subject_status.csv")
                    return sorted(subjects)
        except Exception as e:
            logger.warning(f"Could not read subject_status.csv: {e}")
    
    logger.error("Could not find any subject IDs")
    return []

def load_motion_parameters(subject_id: str) -> np.ndarray:
    """
    Load motion parameters for a subject from the raw data.
    Returns a numpy array of shape (time_points, 6) containing the 6 motion parameters.
    
    Expected format:
    - Text file with 6 columns (trans_x, trans_y, trans_z, rot_x, rot_y, rot_z)
    - One row per time point
    - Values in mm for translation, radians for rotation
    """
    # Try to find motion parameters file
    # Common naming conventions:
    # - sub-XXX_desc-confounds_timeseries.tsv (from fMRIPrep)
    # - sub-XXX_motion_params.txt
    # - sub-XXX_regressors.txt
    
    raw_sub_dir = RAW_DIR / f"sub-{subject_id}"
    if not raw_sub_dir.exists():
        # Try without sub- prefix if directory structure is different
        raw_sub_dir = RAW_DIR / subject_id
    
    motion_file = None
    
    if raw_sub_dir.exists():
        # Look for confounds file (fMRIPrep standard)
        confounds_files = list(raw_sub_dir.glob("*confounds*.tsv"))
        if confounds_files:
            motion_file = confounds_files[0]
        else:
            # Look for motion parameter files
            motion_files = list(raw_sub_dir.glob("*motion*.txt")) + list(raw_sub_dir.glob("*motion*.csv"))
            if motion_files:
                motion_file = motion_files[0]
            else:
                regressors_files = list(raw_sub_dir.glob("*regressors*.txt"))
                if regressors_files:
                    motion_file = regressors_files[0]
    
    if motion_file is None or not motion_file.exists():
        raise FileNotFoundError(f"Motion parameters file not found for subject {subject_id}")
    
    # Load motion parameters
    try:
        # Try to load as TSV (fMRIPrep format)
        if motion_file.suffix == '.tsv':
            import pandas as pd
            df = pd.read_csv(motion_file, sep='\t')
            # Look for motion parameter columns
            motion_cols = [col for col in df.columns if 'trans' in col.lower() or 'rot' in col.lower()]
            if len(motion_cols) >= 6:
                # Take first 6 motion columns
                motion_data = df[motion_cols[:6]].values
            else:
                # Try to find specific columns
                trans_cols = [col for col in df.columns if 'trans' in col.lower()]
                rot_cols = [col for col in df.columns if 'rot' in col.lower()]
                if len(trans_cols) >= 3 and len(rot_cols) >= 3:
                    motion_data = df[trans_cols[:3] + rot_cols[:3]].values
                else:
                    raise ValueError(f"Could not identify 6 motion parameters in {motion_file}")
        else:
            # Try to load as text/csv
            import pandas as pd
            df = pd.read_csv(motion_file, sep=None, engine='python')
            # Assume first 6 numeric columns are motion parameters
            numeric_cols = df.select_dtypes(include=[np.number]).columns[:6]
            if len(numeric_cols) < 6:
                raise ValueError(f"Could not find 6 numeric columns in {motion_file}")
            motion_data = df[numeric_cols].values
        
        return motion_data
      
    except Exception as e:
        raise RuntimeError(f"Failed to load motion parameters from {motion_file}: {e}")

def calculate_max_displacement(motion_params: np.ndarray) -> float:
    """
    Calculate the maximum displacement (in mm) from the motion parameters.
    
    For translation parameters (first 3 columns), values are already in mm.
    For rotation parameters (last 3 columns), convert radians to mm assuming
    a typical brain radius of 60mm.
    
    Returns the maximum displacement across all time points.
    """
    if motion_params.shape[1] < 6:
        raise ValueError(f"Expected at least 6 motion parameters, got {motion_params.shape[1]}")
    
    # Extract translation (mm) and rotation (radians)
    translations = motion_params[:, :3]  # trans_x, trans_y, trans_z in mm
    rotations = motion_params[:, 3:]     # rot_x, rot_y, rot_z in radians
    
    # Convert rotations to mm (assuming 60mm radius)
    ROTATION_RADIUS_MM = 60.0
    rotation_displacements = np.abs(rotations) * ROTATION_RADIUS_MM
    
    # Calculate total displacement at each time point
    # Sum of absolute displacements for simplicity
    total_displacement = np.sum(np.abs(translations), axis=1) + np.sum(rotation_displacements, axis=1)
    
    return float(np.max(total_displacement))

def flag_subject_motion(subject_id: str, motion_available: bool) -> dict:
    """
    Flag a subject based on motion parameters.
    
    Args:
        subject_id: The subject ID
        motion_available: Whether motion parameters were found in the dataset
        
    Returns:
        dict with keys:
            - subject_id: str
            - included: bool (True if subject should be included)
            - reason: str (explanation of inclusion/exclusion)
            - max_displacement_mm: float (if available, else None)
    """
    result = {
        'subject_id': subject_id,
        'included': True,
        'reason': 'No motion issues detected',
        'max_displacement_mm': None
    }
    
    try:
        if not motion_available:
            # If motion parameters are not available, we cannot assess motion
            # According to task T014: "If T014b found NO motion parameters, exclude subjects with >2mm translation"
            # Since we can't measure, we exclude to be conservative
            result['included'] = False
            result['reason'] = 'Motion parameters not available - excluded conservatively'
            return result
        
        # Load motion parameters
        motion_params = load_motion_parameters(subject_id)
        
        # Calculate maximum displacement
        max_disp = calculate_max_displacement(motion_params)
        result['max_displacement_mm'] = max_disp
        
        # Flag based on threshold
        if max_disp > MOTION_THRESHOLD_MM:
            result['included'] = False
            result['reason'] = f'Motion exceeds threshold ({max_disp:.2f}mm > {MOTION_THRESHOLD_MM}mm)'
        else:
            result['included'] = True
            result['reason'] = f'Motion within acceptable limits ({max_disp:.2f}mm <= {MOTION_THRESHOLD_MM}mm)'
            
    except FileNotFoundError as e:
        logger.warning(f"Motion parameters not found for {subject_id}: {e}")
        result['included'] = False
        result['reason'] = f'Motion parameters file not found: {e}'
    except Exception as e:
        logger.error(f"Error processing motion for {subject_id}: {e}")
        result['included'] = False
        result['reason'] = f'Error processing motion parameters: {e}'
    
    return result

def run_motion_flagging_pipeline():
    """
    Main pipeline to flag subjects based on motion parameters.
    
    This function:
    1. Checks if motion parameters are available in the dataset (from T014b)
    2. Gets all subject IDs
    3. Flags each subject based on motion
    4. Updates data/metadata/subject_status.csv with exclusion flags and reasons
    """
    logger.info("Starting motion flagging pipeline")
    
    # Load motion parameters availability from T014b
    motion_params_file = METADATA_DIR / "motion_params_available.json"
    if not motion_params_file.exists():
        raise FileNotFoundError(
            f"Motion parameters check file not found: {motion_params_file}. "
            "Please run T014b first."
        )
    
    with open(motion_params_file, 'r') as f:
        motion_config = json.load(f)
    
    motion_available = motion_config.get('motion_params_available', False)
    logger.info(f"Motion parameters available: {motion_available}")
    
    # Get all subject IDs
    subject_ids = get_all_subject_ids()
    if not subject_ids:
        logger.warning("No subject IDs found. Skipping motion flagging.")
        return []
    
    logger.info(f"Processing {len(subject_ids)} subjects for motion flagging")
    
    # Flag each subject
    flag_results = []
    for subject_id in subject_ids:
        result = flag_subject_motion(subject_id, motion_available)
        flag_results.append(result)
        logger.info(f"Subject {subject_id}: included={result['included']}, reason='{result['reason']}'")
    
    # Update subject_status.csv
    status_file = METADATA_DIR / "subject_status.csv"
    
    # Load existing status if it exists
    existing_status = {}
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_status[row['subject_id']] = row
        except Exception as e:
            logger.warning(f"Could not read existing subject_status.csv: {e}")
    
    # Merge with new flags
    for result in flag_results:
        sid = result['subject_id']
        if sid in existing_status:
            # Update existing entry
            existing_status[sid]['status'] = 'included' if result['included'] else 'excluded'
            existing_status[sid]['exclusion_reason'] = result['reason']
            if result['max_displacement_mm'] is not None:
                existing_status[sid]['max_displacement_mm'] = f"{result['max_displacement_mm']:.3f}"
        else:
            # Create new entry
            existing_status[sid] = {
                'subject_id': sid,
                'status': 'included' if result['included'] else 'excluded',
                'exclusion_reason': result['reason'],
                'max_displacement_mm': f"{result['max_displacement_mm']:.3f}" if result['max_displacement_mm'] is not None else ''
            }
    
    # Write updated status file
    with open(status_file, 'w', newline='') as f:
        fieldnames = ['subject_id', 'status', 'exclusion_reason', 'max_displacement_mm']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for sid in sorted(existing_status.keys()):
            writer.writerow(existing_status[sid])
    
    logger.info(f"Updated {len(existing_status)} entries in {status_file}")
    
    # Log summary
    included_count = sum(1 for r in flag_results if r['included'])
    excluded_count = len(flag_results) - included_count
    logger.info(f"Motion flagging complete: {included_count} included, {excluded_count} excluded")
    
    return flag_results

def main():
    """Main entry point for the script."""
    try:
        results = run_motion_flagging_pipeline()
        logger.info("Motion flagging pipeline completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Motion flagging pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
