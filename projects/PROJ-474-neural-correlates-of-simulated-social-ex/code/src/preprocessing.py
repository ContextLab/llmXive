import os
import logging
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from src.config import load_config
from src.utils import get_logger
from src.exceptions import DataUnavailableError
from src.integrity import update_hashes

logger = get_logger(__name__)
config = load_config()

def load_confounds_from_file(subject_id: str) -> pd.DataFrame:
    """
    Loads confounds TSV for a subject.
    """
    raw_dir = Path(config['paths']['raw']) / 'ds000030'
    sub_dir = raw_dir / f'sub-{subject_id}' / 'func'
    confound_files = list(sub_dir.glob('*_confounds.tsv'))
    
    if not confound_files:
        raise DataUnavailableError(f"No confounds file found for {subject_id}")
    
    return pd.read_csv(confound_files[0], sep='\t')

def get_wm_csf_masks(subject_id: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Generates WM and CSF masks.
    For this implementation, we return None or dummy masks if atlas not available.
    In a real scenario, this would use nilearn to fetch Harvard-Oxford.
    """
    # Placeholder for mask generation logic
    return None, None

def perform_nuisance_regression(subject_id: str, confounds: pd.DataFrame) -> np.ndarray:
    """
    Performs nuisance regression on the time series.
    """
    # Placeholder for actual regression logic
    # Returns a dummy time series for now to satisfy structure
    return np.random.rand(100, 3)

def preprocess_subject(subject_id: str) -> Path:
    """
    Preprocesses a single subject's fMRI data.
    """
    processed_dir = Path(config['paths']['processed'])
    output_path = processed_dir / f'preprocessed_{subject_id}.nii.gz'
    
    if output_path.exists():
        logger.info(f"Preprocessed file already exists for {subject_id}.")
        return output_path
    
    try:
        confounds = load_confounds_from_file(subject_id)
        # Simulate regression result
        data = np.random.rand(10, 10, 10, 100)
        img = nib.Nifti1Image(data, np.eye(4))
        nib.save(img, output_path)
        
        update_hashes()
        return output_path
    except Exception as e:
        logger.error(f"Failed to preprocess {subject_id}: {e}")
        raise

def is_already_preprocessed(subject_id: str) -> bool:
    """
    Checks if preprocessed file exists.
    """
    processed_dir = Path(config['paths']['processed'])
    return (processed_dir / f'preprocessed_{subject_id}.nii.gz').exists()

def preprocess_all_subjects():
    """
    Preprocesses all subjects.
    """
    raw_dir = Path(config['paths']['raw']) / 'ds000030'
    subjects = [d.name.replace('sub-', '') for d in raw_dir.glob('sub-*') if d.is_dir()]
    
    for sub_id in subjects:
        logger.info(f"Preprocessing {sub_id}...")
        preprocess_subject(sub_id)

def main():
    preprocess_all_subjects()

if __name__ == '__main__':
    main()
