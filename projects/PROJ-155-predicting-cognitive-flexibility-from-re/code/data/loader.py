"""
Core data loading functions for HCP resting-state fMRI and behavioral data.

This module handles the ingestion of raw NIfTI files and behavioral CSVs,
performing initial validation and path resolution.
"""

import os
import csv
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import nibabel as nib
import pandas as pd

from code.config import get_config
from code.data.paths import get_raw_path, get_processed_path


def load_nifti(subject_id: str, run_index: int = 1) -> nib.Nifti1Image:
    """
    Load a preprocessed resting-state fMRI NIfTI file for a given subject.
    
    Args:
        subject_id: The HCP subject ID (e.g., '100307').
        run_index: The run number (1 or 2). Defaults to 1.
        
    Returns:
        The loaded NIfTI image object.
        
    Raises:
        FileNotFoundError: If the file does not exist at the expected path.
    """
    config = get_config()
    # Expected path structure based on HCP minimal preprocessing pipeline
    filename = f"rfnREST_min.nii.gz"
    # HCP typically stores preprocessed data in: <subject>/MNINonLinear/Results/rfMRI_REST1_LR/
    # For simplicity in this pipeline, we assume a flattened structure in data/raw/
    # or a specific substructure defined in the download task.
    # Assuming the download task places files in: data/raw/<subject_id>/rfnREST_min.nii.gz
    # Adjusting path logic to match standard HCP OpenAccess structure if downloaded directly
    # or a normalized structure if T012 organizes it.
    # Let's assume T012 organizes as: data/raw/<subject_id>/MNINonLinear/Results/rfMRI_REST1_LR/rfnREST_min.nii.gz
    # However, to be robust, we check the raw path root.
    
    # Standard HCP path relative to raw folder:
    # <subject>/MNINonLinear/Results/rfMRI_REST1_LR/rfnREST_min.nii.gz
    # But often simplified in pipelines to:
    # <subject>/rfnREST_min.nii.gz
    
    # We will construct the path assuming T012 places the file in:
    # data/raw/<subject_id>/MNINonLinear/Results/rfMRI_REST1_LR/rfnREST_min.nii.gz
    # If T012 simplifies it, we might need a fallback.
    # For now, we implement the standard HCP path structure as per spec.
    
    base_path = get_raw_path()
    subject_dir = os.path.join(base_path, subject_id)
    
    # Try standard HCP path first
    possible_paths = [
        os.path.join(subject_dir, "MNINonLinear", "Results", f"rfMRI_REST{run_index}_LR", "rfnREST_min.nii.gz"),
        os.path.join(subject_dir, "MNINonLinear", "Results", f"rfMRI_REST{run_index}_RL", "rfnREST_min.nii.gz"),
        os.path.join(subject_dir, "rfnREST_min.nii.gz"), # Simplified if T012 flattens
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return nib.load(path)
    
    raise FileNotFoundError(f"Could not find NIfTI file for subject {subject_id}. Checked: {possible_paths}")


def load_behavioral_csv(subject_ids: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Load the behavioral data CSV containing cognitive flexibility scores and covariates.
    
    Args:
        subject_ids: Optional list of subject IDs to filter. If None, loads all.
        
    Returns:
        A pandas DataFrame with behavioral data.
        
    Raises:
        FileNotFoundError: If the behavioral CSV is missing.
    """
    config = get_config()
    base_path = get_raw_path()
    # Assuming T012 downloads the behavioral CSV to: data/raw/behavioral_data.csv
    # or a specific manifest file. The spec mentions "NIH Toolbox Dimensional Change Card Sort scores".
    # HCP 1200 release usually provides a CSV with all subjects.
    csv_path = os.path.join(base_path, "hcp_1200_behavioral.csv")
    
    # Fallback if the file is named differently
    if not os.path.exists(csv_path):
        # Try common HCP behavioral file names
        alt_paths = [
            os.path.join(base_path, "behavioral_data.csv"),
            os.path.join(base_path, "data/behavioral.csv"),
        ]
        for alt in alt_paths:
            if os.path.exists(alt):
                csv_path = alt
                break
        else:
            raise FileNotFoundError(f"Behavioral CSV not found in {base_path}. Expected hcp_1200_behavioral.csv")
    
    df = pd.read_csv(csv_path)
    
    # Standardize column names if necessary (HCP uses specific naming)
    # Common columns: Subject, Age, Sex, DCCS (Dimensional Change Card Sort), Total Scan Time
    # Map to expected internal names if they differ
    # We assume the CSV already has columns or we map them here.
    # Let's assume the CSV has: 'Subject', 'Age', 'Sex', 'DCCS', 'Total Scan Time'
    
    # Normalize column names to lowercase for robustness
    df.columns = df.columns.str.strip().str.lower()
    
    # Map HCP standard names to internal canonical names
    mapping = {
        'subject': 'Subject_ID',
        'age': 'Age',
        'sex': 'Sex',
        'dccs': 'Flexibility_Score', # DCCS is the proxy for cognitive flexibility
        'total scan time': 'Total Scan Time',
        'mean fd': 'Mean_FD' # Might be pre-calculated in some releases, or we calc it
    }
    
    for old, new in mapping.items():
        if old in df.columns:
            df.rename(columns={old, new}, inplace=True)
    
    if subject_ids is not None:
        # Ensure Subject_ID is string for comparison
        if 'subject_id' in df.columns:
            df['subject_id'] = df['subject_id'].astype(str)
            subject_ids = [str(s) for s in subject_ids]
            df = df[df['subject_id'].isin(subject_ids)]
        else:
            # Fallback if column name mismatch persists
            if 'subject' in df.columns:
                df['subject'] = df['subject'].astype(str)
                subject_ids = [str(s) for s in subject_ids]
                df = df[df['subject'].isin(subject_ids)]
    
    return df


def validate_subject_data(
    subject_id: str,
    behavioral_df: pd.DataFrame,
    motion_threshold: float = 0.2
) -> Tuple[bool, Optional[str]]:
    """
    Validate that a subject has both imaging and behavioral data available.
    
    Args:
        subject_id: The subject ID to validate.
        behavioral_df: The loaded behavioral DataFrame.
        motion_threshold: Threshold for Mean FD exclusion (from config).
        
    Returns:
        A tuple (is_valid, reason). is_valid is True if data is present.
        reason is None if valid, otherwise a string describing the failure.
    """
    # Check behavioral data
    if 'subject_id' in behavioral_df.columns:
        sub_row = behavioral_df[behavioral_df['subject_id'] == str(subject_id)]
    elif 'subject' in behavioral_df.columns:
        sub_row = behavioral_df[behavioral_df['subject'] == str(subject_id)]
    else:
        return False, "Behavioral CSV missing 'Subject' or 'Subject_ID' column"
    
    if sub_row.empty:
        return False, "Missing_Behavioral_Score"
    
    # Check for missing flexibility score
    flex_col = 'flexibility_score' if 'flexibility_score' in sub_row.columns else 'dccs'
    if flex_col not in sub_row.columns:
        return False, "Missing_Behavioral_Score"
        
    if pd.isna(sub_row[flex_col].iloc[0]):
        return False, "Missing_Behavioral_Score"
    
    # Check imaging data existence
    try:
        load_nifti(subject_id)
    except FileNotFoundError:
        return False, "Missing_Imaging_Data"
    
    # Check Mean FD if available in behavioral data
    if 'mean_fd' in sub_row.columns:
        mean_fd = sub_row['mean_fd'].iloc[0]
        if not pd.isna(mean_fd) and mean_fd > motion_threshold:
            return False, "Motion"
    
    return True, None
