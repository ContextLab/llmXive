import os
import csv
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import nibabel as nib
import pandas as pd
from code.data.paths import get_raw_path

def load_nifti(nifti_path: str) -> nib.Nifti1Image:
    """
    Loads a NIfTI file and returns the nibabel image object.
    
    Args:
        nifti_path: Path to the NIfTI file.
        
    Returns:
        nib.Nifti1Image: The loaded image.
    """
    if not os.path.exists(nifti_path):
        raise FileNotFoundError(f"NIfTI file not found: {nifti_path}")
    return nib.load(nifti_path)

def load_behavioral_csv(subject_id: str) -> Optional[pd.DataFrame]:
    """
    Loads the behavioral data CSV for a specific subject.
    
    Args:
        subject_id: The subject ID.
        
    Returns:
        Optional[pd.DataFrame]: The behavioral data, or None if not found.
    """
    raw_path = get_raw_path()
    file_name = f"HCP1200_allData_{subject_id}_Release20220522.csv"
    file_path = os.path.join(raw_path, subject_id, file_name)
    
    if not os.path.exists(file_path):
        return None
    
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load behavioral data for {subject_id}: {e}")

def validate_subject_data(subject_id: str, data_files: Dict[str, str]) -> bool:
    """
    Validates that all required data files exist for a subject.
    
    Args:
        subject_id: The subject ID.
        data_files: Dict mapping file type to path.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    required_keys = ["rsfc", "behavior"]
    for key in required_keys:
        if key not in data_files or not os.path.exists(data_files[key]):
            return False
    return True
