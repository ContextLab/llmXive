import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import json
import numpy as np
import nibabel as nib
import logging

from config import ensure_directories
from utils import get_logger, read_csv, write_csv, log_execution_time

# Ensure logger is configured if not already
logger = get_logger(__name__)

def load_hcp_fmri_data(data_dir: Union[str, Path]) -> Dict[str, Path]:
    """
    Load HCP fMRI data from the raw directory.
    Returns a dictionary mapping subject IDs to their fMRI file paths.
    """
    data_dir = Path(data_dir)
    fmri_files = {}
    # Expected structure: data/raw/sub-<label>/func/sub-<label>_task-rest_bold.nii.gz
    for subject_dir in data_dir.iterdir():
        if subject_dir.is_dir() and subject_dir.name.startswith("sub-"):
            func_dir = subject_dir / "func"
            if func_dir.exists():
                bold_file = func_dir / f"{subject_dir.name}_task-rest_bold.nii.gz"
                if bold_file.exists():
                    fmri_files[subject_dir.name] = bold_file
    return fmri_files

def load_mwq_data(data_dir: Union[str, Path]) -> Dict[str, Dict]:
    """
    Load Mind-Wandering Questionnaire (MWQ) data.
    Returns a dictionary mapping subject IDs to their MWQ scores and demographics.
    """
    data_dir = Path(data_dir)
    mwq_file = data_dir / "mwq_scores.csv"
    if not mwq_file.exists():
        raise FileNotFoundError(f"MWQ data file not found at {mwq_file}")
    
    # Read CSV manually to avoid pandas dependency if not strictly needed, 
    # but assuming utils.read_csv handles it or we use standard csv if utils is limited.
    # Based on utils.py signature, it likely returns a list of dicts or similar.
    # We will assume standard CSV reading logic compatible with the project.
    import csv
    data = {}
    with open(mwq_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize subject ID if necessary (e.g., sub-001 -> 001)
            sub_id = row.get('Subject_ID') or row.get('subject_id')
            if sub_id:
                data[sub_id] = row
    return data

def join_fmri_mwq_data(fmri_data: Dict[str, Path], mwq_data: Dict[str, Dict]) -> List[Dict]:
    """
    Join fMRI and MWQ data based on subject ID.
    Returns a list of dictionaries containing combined data for matched subjects.
    """
    joined_data = []
    for sub_id, fmri_path in fmri_data.items():
        if sub_id in mwq_data:
            record = {
                'subject_id': sub_id,
                'fmri_path': str(fmri_path),
                **mwq_data[sub_id]
            }
            joined_data.append(record)
        else:
            logger.warning(f"Subject {sub_id} found in fMRI data but not in MWQ data. Skipping.")
    return joined_data

def validate_subject_data(record: Dict) -> bool:
    """
    Validate that a subject record has all required fields.
    """
    required_fields = ['subject_id', 'fmri_path', 'MWQ_Score', 'Age', 'Sex']
    for field in required_fields:
        if field not in record or record[field] is None:
            logger.error(f"Missing required field '{field}' for subject {record.get('subject_id', 'UNKNOWN')}")
            return False
    return True

def process_subject_validation(records: List[Dict]) -> List[Dict]:
    """
    Process a list of records, filtering out invalid ones.
    """
    valid_records = []
    for record in records:
        if validate_subject_data(record):
            valid_records.append(record)
    return valid_records

def prepare_bids_structure(base_dir: Union[str, Path]) -> Path:
    """
    Prepare BIDS-compatible directory structure.
    """
    base_dir = Path(base_dir)
    # Logic to create sub-*/func/ directories if they don't exist
    # This is a placeholder for the actual logic described in T007
    return base_dir

def generate_bids_filename(subject_id: str, task: str = "rest", suffix: str = "bold") -> str:
    """
    Generate a BIDS-compatible filename.
    """
    return f"{subject_id}_task-{task}_{suffix}.nii.gz"

def create_empty_bids_files(output_path: Path) -> None:
    """
    Create empty BIDS files for testing structure.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.touch()

@log_execution_time
def compute_global_signal_mean_time_series(nifti_path: Union[str, Path]) -> np.ndarray:
    """
    Compute the voxel-wise mean time series (global signal) from a 4D NIfTI file.
    Returns a 1D numpy array of the mean time series.
    """
    nifti_path = Path(nifti_path)
    if not nifti_path.exists():
        raise FileNotFoundError(f"NIfTI file not found: {nifti_path}")
    
    img = nib.load(nifti_path)
    data = img.get_fdata()
    
    # data shape: (x, y, z, time)
    if data.ndim != 4:
        raise ValueError(f"Expected 4D data, got {data.ndim}D")
    
    # Compute mean across voxels (axes 0, 1, 2) for each time point (axis 3)
    global_signal = np.mean(data, axis=(0, 1, 2))
    return global_signal

@log_execution_time
def compute_global_signal_sd_per_run(global_signal: np.ndarray) -> float:
    """
    Compute the standard deviation of the global signal for a single run.
    """
    if global_signal.size == 0:
        return 0.0
    return float(np.std(global_signal))

@log_execution_time
def compute_subject_average_global_signal_sd(global_signal_sds: List[float]) -> float:
    """
    Compute the average global signal SD across multiple runs for a subject.
    """
    if not global_signal_sds:
        return 0.0
    return float(np.mean(global_signal_sds))

def check_zero_variance_subjects(records: List[Dict], output_log_path: Optional[Path] = None) -> List[Dict]:
    """
    T015: Implement zero-variance check to exclude subjects with global_signal_sd == 0.
    
    This function filters the input records, removing any subject where the 
    computed Global_Signal_SD is exactly 0.0 (or very close to it, e.g., < 1e-9).
    It logs warnings for excluded subjects.
    
    Args:
        records: List of dictionaries containing subject data including 'Global_Signal_SD'.
        output_log_path: Optional path to write a log of excluded subjects.
        
    Returns:
        List of records with zero-variance subjects removed.
    """
    cleaned_records = []
    excluded_count = 0
    excluded_subjects = []

    for record in records:
        sub_id = record.get('subject_id', 'UNKNOWN')
        gs_sd = record.get('Global_Signal_SD')
        
        if gs_sd is None:
            logger.warning(f"Subject {sub_id} has missing Global_Signal_SD. Excluding.")
            excluded_count += 1
            excluded_subjects.append(sub_id)
            continue

        # Check for zero variance (strictly 0 or extremely close to 0 due to float precision)
        if gs_sd == 0.0 or abs(gs_sd) < 1e-9:
            logger.warning(f"Subject {sub_id} has zero global signal SD ({gs_sd}). Excluding.")
            excluded_count += 1
            excluded_subjects.append(sub_id)
        else:
            cleaned_records.append(record)

    if excluded_count > 0:
        logger.info(f"Zero-variance check complete: {excluded_count} subjects excluded.")
        if output_log_path:
            output_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_log_path, 'w') as f:
                f.write("Subject_ID,Reason\n")
                for sub in excluded_subjects:
                    f.write(f"{sub},Zero_Global_Signal_SD\n")
    else:
        logger.info("Zero-variance check complete: No subjects excluded.")

    return cleaned_records